import streamlit as st
import requests
import pandas as pd
from config import Config
from typing import Dict, List, Optional
import time

st.set_page_config(page_title="Training Anomalies", layout="wide")

@st.cache_data(ttl=300)
def fetch_anomalies_data(_config: Config, page: int = 1, limit: int = 20) -> Optional[Dict]:
    """Fetch anomalous training data from the API with caching"""
    try:
        params = {
            "page": page,
            "limit": limit,
            "sort_by": "updated_at",
            "sort_order": "desc",
            "anomalous": "true",
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
        st.error(f"Failed to fetch anomalies data: {str(e)}")
        return None

def main():
    """Main application function"""
    try:
        config = Config()
    except ValueError as e:
        st.error(f"Configuration Error: {str(e)}")
        st.info("Please set the required environment variables: REAR_DIFF_HOST, REAR_DIFF_PORT")
        return
    
    st.title("Training Anomalies")
    
    data = fetch_anomalies_data(config)
    
    if not data:
        return
    
    items = data.get("data", [])
    
    if not items:
        st.success("✅ No anomalies found")
        return
    
    st.info(f"Found {len(items)} anomalous training items")
    
    # TODO: Add anomaly display and management functionality
    for idx, item in enumerate(items):
        with st.container():
            st.write(f"**{item.get('media_title', 'Unknown')}** - IMDB ID: {item.get('imdb_id', 'NULL')}")
            st.write(f"Anomalous: {item.get('anomalous', 'NULL')}")
            st.divider()

if __name__ == "__main__":
    main()