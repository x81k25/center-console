import streamlit as st
import requests
import pandas as pd
from config import Config
from typing import Dict, List, Optional
import time

st.set_page_config(page_title="Training Backlog", layout="wide")

@st.cache_data(ttl=300)
def fetch_training_data(config: Config, page: int = 1, limit: int = 20) -> Optional[Dict]:
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
            config.training_endpoint,
            params=params,
            timeout=config.api_timeout
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch training data: {str(e)}")
        return None

def update_label(config: Config, imdb_id: str, current_label: str) -> bool:
    """Update the label for a training item"""
    try:
        new_label = "would_not_watch" if current_label == "would_watch" else "would_watch"
        
        payload = {
            "label": new_label,
            "human_labeled": True,
            "reviewed": True
        }
        
        response = requests.patch(
            config.get_label_update_endpoint(imdb_id),
            json=payload,
            timeout=config.api_timeout
        )
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Failed to update label for {imdb_id}: {str(e)}")
        return False

def mark_as_reviewed(config: Config, imdb_id: str) -> bool:
    """Mark a training item as reviewed"""
    try:
        endpoint = f"{config.base_url}training/{imdb_id}/reviewed"
        payload = {"reviewed": True}
        
        response = requests.patch(
            endpoint,
            json=payload,
            timeout=config.api_timeout
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
    
    items = data.get("items", [])
    
    if not items:
        st.success("✅ Backlog cleared")
        return
    
    st.info(f"Showing {len(items)} unreviewed movies")
    
    for idx, item in enumerate(items):
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 2, 2])
            
            with col1:
                st.write(f"**{item.get('media_title', 'Unknown')}**")
            
            with col2:
                rt_score = item.get('rt_score', 'N/A')
                st.write(f"RT: {rt_score}%")
            
            with col3:
                imdb_votes = item.get('imdb_votes', 'N/A')
                if isinstance(imdb_votes, int):
                    imdb_votes = f"{imdb_votes:,}"
                st.write(f"IMDB: {imdb_votes}")
            
            with col4:
                current_label = item.get('label', '')
                button_color = "primary" if current_label == "would_watch" else "secondary"
                button_text = current_label if current_label else "No Label"
                
                if current_label == "would_watch":
                    button_text = "🟦 " + button_text
                elif current_label == "would_not_watch":
                    button_text = "🟥 " + button_text
                
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
                    "✓ Confirm",
                    key=f"confirm_{item.get('imdb_id')}",
                    type="primary",
                    use_container_width=True
                ):
                    if mark_as_reviewed(config, item.get('imdb_id')):
                        st.cache_data.clear()
                        st.rerun()
            
            st.divider()

if __name__ == "__main__":
    main()