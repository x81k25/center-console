import streamlit as st
import requests
import pandas as pd
from config import Config
from typing import Dict, List, Optional
import time

st.set_page_config(page_title="Training Backlog", layout="wide")

# Custom CSS for button styling
st.markdown("""
<style>
/* Blue buttons for would_watch when active */
div[data-testid="stButton"] > button[kind="primary"] {
    background-color: #1f77b4 !important;
    color: white !important;
    border-color: #1f77b4 !important;
}

/* Red buttons for would_not_watch when active */
div[data-testid="stButton"] > button[kind="tertiary"] {
    background-color: #d62728 !important;
    color: white !important;
    border-color: #d62728 !important;
}

/* Transparent buttons when inactive */
div[data-testid="stButton"] > button:not([kind]) {
    background-color: transparent !important;
    color: #262730 !important;
    border: 1px solid #d0d0d0 !important;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def fetch_training_data(_config: Config, page: int = 1, limit: int = 20) -> Optional[Dict]:
    """Fetch training data from the API with caching"""
    try:
        params = {
            "page": page,
            "limit": limit,
            "sort_by": "updated_at",
            "sort_order": "desc",
            "reviewed": "false",
            "media_type": "movie"
        }
        
        response = requests.get(
            _config.training_endpoint,
            params=params,
            timeout=_config.api_timeout
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch training data: {str(e)}")
        return None

def update_label(_config: Config, imdb_id: str, new_label: str) -> bool:
    """Update the label for a training item"""
    try:
        payload = {
            "imdb_id": imdb_id,
            "label": new_label,
            "human_labeled": True,
            "reviewed": True
        }
        
        response = requests.patch(
            _config.get_label_update_endpoint(imdb_id),
            json=payload,
            timeout=_config.api_timeout
        )
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Failed to update label for {imdb_id}: {str(e)}")
        return False

def mark_as_reviewed(_config: Config, imdb_id: str) -> bool:
    """Mark a training item as reviewed"""
    try:
        endpoint = f"{_config.base_url}training/{imdb_id}/reviewed"
        payload = {"imdb_id": imdb_id, "reviewed": True}
        
        response = requests.patch(
            endpoint,
            json=payload,
            timeout=_config.api_timeout
        )
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Failed to mark {imdb_id} as reviewed: {str(e)}")
        return False

def main():
    """Main application function"""
    try:
        config = Config()
    except ValueError as e:
        st.error(f"Configuration Error: {str(e)}")
        st.info("Please set the required environment variables: REAR_DIFF_HOST, REAR_DIFF_PORT")
        return
    
    st.title("Training Backlog")
    
    data = fetch_training_data(config)
    
    if not data:
        return
    
    items = data.get("data", [])
    
    if not items:
        st.success("✅ Backlog cleared")
        return
    
    
    for idx, item in enumerate(items):
        with st.container():
            # Main row with basic info and buttons
            col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 2, 1.5, 1.5])
            
            with col1:
                st.write(f"**{item.get('media_title', 'Unknown')}**")
            
            with col2:
                rt_score = item.get('rt_score')
                if rt_score is None:
                    rt_score_display = "NULL"
                else:
                    rt_score_display = f"{rt_score}%"
                st.write(f"RT: {rt_score_display}")
            
            with col3:
                imdb_votes = item.get('imdb_votes')
                if imdb_votes is None:
                    imdb_votes_display = "NULL"
                elif isinstance(imdb_votes, int):
                    imdb_votes_display = f"{imdb_votes:,}"
                else:
                    imdb_votes_display = str(imdb_votes)
                st.write(f"IMDB: {imdb_votes_display}")
            
            with col4:
                genres = item.get('genre', [])
                if genres and isinstance(genres, list):
                    genre_display = ", ".join(genres[:2])  # Show first 2 genres
                    if len(genres) > 2:
                        genre_display += "..."
                else:
                    genre_display = "NULL"
                st.write(f"Genre: {genre_display}")
            
            current_label = item.get('label', '')
            
            with col5:
                # Would Watch button - blue when active, transparent when inactive
                button_type = "primary" if current_label == "would_watch" else None
                button_kwargs = {"use_container_width": True}
                if button_type:
                    button_kwargs["type"] = button_type
                
                if st.button("would_watch", key=f"would_watch_{item.get('imdb_id')}", **button_kwargs):
                    if update_label(config, item.get('imdb_id'), "would_watch"):
                        st.cache_data.clear()
                        st.rerun()
            
            with col6:
                # Would Not Watch button - red when active, transparent when inactive
                button_type = "tertiary" if current_label == "would_not_watch" else None
                button_kwargs = {"use_container_width": True}
                if button_type:
                    button_kwargs["type"] = button_type
                
                if st.button("would_not", key=f"would_not_watch_{item.get('imdb_id')}", **button_kwargs):
                    if update_label(config, item.get('imdb_id'), "would_not_watch"):
                        st.cache_data.clear()
                        st.rerun()
            
            # Expandable details section
            with st.expander(f"📋 Details for {item.get('media_title', 'Unknown')}", expanded=False):
                detail_col1, detail_col2 = st.columns(2)
                
                with detail_col1:
                    st.write("**Basic Info:**")
                    st.write(f"• **IMDB ID:** {item.get('imdb_id', 'NULL')}")
                    st.write(f"• **TMDB ID:** {item.get('tmdb_id', 'NULL')}")
                    st.write(f"• **Release Year:** {item.get('release_year', 'NULL')}")
                    st.write(f"• **Runtime:** {item.get('runtime', 'NULL')} min")
                    st.write(f"• **Original Language:** {item.get('original_language', 'NULL')}")
                    st.write(f"• **Origin Country:** {item.get('origin_country', 'NULL')}")
                    
                    st.write("**Status:**")
                    st.write(f"• **Current Label:** {item.get('label', 'NULL')}")
                    st.write(f"• **Human Labeled:** {item.get('human_labeled', 'NULL')}")
                    st.write(f"• **Reviewed:** {item.get('reviewed', 'NULL')}")
                    st.write(f"• **Anomalous:** {item.get('anomalous', 'NULL')}")
                
                with detail_col2:
                    st.write("**Ratings & Scores:**")
                    st.write(f"• **RT Score:** {item.get('rt_score', 'NULL')}")
                    st.write(f"• **IMDB Rating:** {item.get('imdb_rating', 'NULL')}")
                    st.write(f"• **IMDB Votes:** {item.get('imdb_votes', 'NULL')}")
                    st.write(f"• **TMDB Rating:** {item.get('tmdb_rating', 'NULL')}")
                    st.write(f"• **TMDB Votes:** {item.get('tmdb_votes', 'NULL')}")
                    st.write(f"• **Metascore:** {item.get('metascore', 'NULL')}")
                    
                    st.write("**Financial:**")
                    st.write(f"• **Budget:** ${item.get('budget', 'NULL'):,}" if item.get('budget') else "• **Budget:** NULL")
                    st.write(f"• **Revenue:** ${item.get('revenue', 'NULL'):,}" if item.get('revenue') else "• **Revenue:** NULL")
                
                st.write("**Additional Info:**")
                st.write(f"• **Genres:** {', '.join(item.get('genre', [])) if item.get('genre') else 'NULL'}")
                st.write(f"• **Production Status:** {item.get('production_status', 'NULL')}")
                st.write(f"• **Tagline:** {item.get('tagline', 'NULL')}")
                
                if item.get('overview'):
                    st.write("**Overview:**")
                    st.write(item.get('overview'))
                
                st.write("**Timestamps:**")
                st.write(f"• **Created:** {item.get('created_at', 'NULL')}")
                st.write(f"• **Updated:** {item.get('updated_at', 'NULL')}")
            
            st.divider()

if __name__ == "__main__":
    main()