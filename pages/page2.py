import streamlit as st
import requests
import pandas as pd
from config import Config
from typing import Dict, List, Optional
import time

st.set_page_config(
    page_title="Media Library",
    page_icon="🎬",
    layout="wide"
)

# Custom CSS for styling
st.markdown("""
<style>
/* RT Score - Crimson */
div[data-testid="stColumn"]:nth-child(2) .stProgress > div > div > div > div {
    background-color: #DC143C !important;
}

/* IMDB Votes - IMDB Yellow */
div[data-testid="stColumn"]:nth-child(3) .stProgress > div > div > div > div {
    background-color: #F5C518 !important;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def fetch_media_data(_config: Config, page: int = 1, limit: int = 20) -> Optional[Dict]:
    """Fetch media data from the API with caching"""
    try:
        params = {
            "page": page,
            "limit": limit,
            "sort_by": "updated_at",
            "sort_order": "desc"
        }
        
        response = requests.get(
            _config.media_endpoint,
            params=params,
            timeout=_config.api_timeout
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch media data: {str(e)}")
        return None

def main():
    """Main application function"""
    try:
        config = Config()
    except ValueError as e:
        st.error(f"Configuration Error: {str(e)}")
        st.info("Please set the required environment variables: REAR_DIFF_HOST, REAR_DIFF_PORT_EXTERNAL")
        return
    
    st.title("🎬 Media Library")
    
    # Add pagination controls
    col1, col2, col3 = st.columns([1, 1, 8])
    with col1:
        page = st.number_input("Page", min_value=1, value=1, step=1)
    with col2:
        limit = st.selectbox("Items per page", [10, 20, 50], index=1)
    
    data = fetch_media_data(config, page=page, limit=limit)
    
    if not data:
        return
    
    items = data.get("data", [])
    total_items = data.get("total", 0)
    total_pages = data.get("pages", 1)
    
    # Display metadata
    st.info(f"Showing {len(items)} items | Total: {total_items} | Page {page} of {total_pages}")
    
    if not items:
        st.info("No media items found")
        return
    
    # Display each media item
    for idx, item in enumerate(items):
        with st.container():
            # Main row with basic info
            col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 0.8, 0.6, 2])
            
            with col1:
                st.write(f"**{item.get('media_title', 'Unknown')}**")
            
            with col2:
                rt_score = item.get('rt_score')
                if rt_score is None:
                    st.write("RT: NULL")
                else:
                    # Show RT score with progress bar
                    st.write("**RT Score**")
                    st.progress(rt_score / 100.0)
                    st.caption(f"{rt_score}%")
            
            with col3:
                imdb_votes = item.get('imdb_votes')
                if imdb_votes is None:
                    st.write("IMDB: NULL")
                else:
                    # Show IMDB votes as progress bar with 100k cap
                    if isinstance(imdb_votes, int):
                        st.write("**IMDB Votes**")
                        # Cap at 100k for progress bar
                        progress_value = min(imdb_votes / 100000.0, 1.0)
                        st.progress(progress_value)
                        # Format display
                        if imdb_votes >= 1000000:
                            votes_display = f"{imdb_votes/1000000:.1f}M"
                        elif imdb_votes >= 1000:
                            votes_display = f"{imdb_votes/1000:.0f}K"
                        else:
                            votes_display = str(imdb_votes)
                        st.caption(votes_display)
                    else:
                        st.write(f"IMDB: {imdb_votes}")
            
            with col4:
                release_year = item.get('release_year')
                st.write(f"Year: {release_year if release_year else 'NULL'}")
            
            with col5:
                lang = item.get('original_language')
                st.write(f"Lang: {lang.upper() if lang else 'NULL'}")
            
            with col6:
                genres = item.get('genre', [])
                if genres and isinstance(genres, list):
                    genre_display = ", ".join(genres[:2])  # Show first 2 genres
                    if len(genres) > 2:
                        genre_display += "..."
                else:
                    genre_display = "NULL"
                st.write(f"Genre: {genre_display}")
            
            # Show label status if available
            if item.get('label'):
                label_col1, label_col2, label_col3 = st.columns([1, 1, 8])
                with label_col1:
                    label = item.get('label', '')
                    label_color = "#1f77b4" if label == "would_watch" else "#d62728" if label == "would_not_watch" else "#808080"
                    st.markdown(f'<span style="color: {label_color}; font-weight: bold;">Label: {label}</span>', unsafe_allow_html=True)
                with label_col2:
                    if item.get('human_labeled'):
                        st.success("Human Labeled")
                with label_col3:
                    if item.get('reviewed'):
                        st.info("Reviewed")
            
            # Expandable details section
            with st.expander(f"📋 Details for {item.get('media_title', 'Unknown')}", expanded=False):
                detail_col1, detail_col2 = st.columns(2)
                
                with detail_col1:
                    st.write("**Basic Info:**")
                    st.write(f"• **IMDB ID:** {item.get('imdb_id', 'NULL')}")
                    st.write(f"• **TMDB ID:** {item.get('tmdb_id', 'NULL')}")
                    st.write(f"• **Media Type:** {item.get('media_type', 'NULL')}")
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