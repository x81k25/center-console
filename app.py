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
/* Red buttons for would_not_watch */
div[data-testid="stButton"] > button[kind="secondary"] {
    background-color: #ff4b4b !important;
    color: white !important;
    border-color: #ff4b4b !important;
}

div[data-testid="stButton"] > button[kind="secondary"]:hover {
    background-color: #ff2626 !important;
    border-color: #ff2626 !important;
}

/* Neutral/default buttons (no type specified) */
div[data-testid="stButton"] > button:not([kind]) {
    background-color: #f0f2f6 !important;
    color: #262730 !important;
    border-color: #d4d4d4 !important;
}

div[data-testid="stButton"] > button:not([kind]):hover {
    background-color: #e6e8ec !important;
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

def update_label(_config: Config, imdb_id: str, current_label: str) -> bool:
    """Update the label for a training item"""
    try:
        new_label = "would_not_watch" if current_label == "would_watch" else "would_watch"
        
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
    
    if st.button("Refresh Data", type="secondary"):
        st.cache_data.clear()
        st.rerun()
    
    data = fetch_training_data(config)
    
    if not data:
        return
    
    items = data.get("data", [])
    
    if not items:
        st.success("✅ Backlog cleared")
        return
    
    
    for idx, item in enumerate(items):
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 2, 2])
            
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
                current_label = item.get('label', '')
                
                # Set button color based on label
                if current_label == "would_watch":
                    button_color = "primary"  # Blue background
                    button_text = "would_watch"
                elif current_label == "would_not_watch":
                    button_color = "secondary"  # Red-ish background  
                    button_text = "would_not_watch"
                else:
                    button_color = "secondary"
                    button_text = "No Label"
                
                if st.button(
                    button_text,
                    key=f"label_{item.get('imdb_id')}",
                    type=button_color,
                    use_container_width=True
                ):
                    if update_label(config, item.get('imdb_id'), current_label):
                        st.cache_data.clear()
                        st.rerun()
            
            with col5:
                if st.button(
                    "Confirm",
                    key=f"confirm_{item.get('imdb_id')}",
                    use_container_width=True
                ):
                    if mark_as_reviewed(config, item.get('imdb_id')):
                        st.cache_data.clear()
                        st.rerun()
            
            st.divider()

if __name__ == "__main__":
    main()