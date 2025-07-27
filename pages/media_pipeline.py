import streamlit as st
import requests
import logging
from config import Config
import json
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="media-pipeline", layout="wide")

def make_patch_call(config: Config, hash_id: str, updates: Dict):
    """Make a PATCH call to update pipeline status"""
    # Prepare payload with hash and updates
    payload = {"hash": hash_id, **updates}
    
    try:
        endpoint = config.get_media_pipeline_endpoint(hash_id)
        
        logger.info("=" * 80)
        logger.info("MAKING PATCH CALL")
        logger.info(f"Hash: {hash_id}")
        logger.info(f"Endpoint: {endpoint}")
        logger.info(f"Payload: {json.dumps(payload, indent=2)}")
        logger.info("=" * 80)
        
        response = requests.patch(
            endpoint,
            json=payload,
            timeout=config.api_timeout
        )
        
        logger.info(f"Response Status Code: {response.status_code}")
        logger.info(f"Response Headers: {dict(response.headers)}")
        logger.info(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            logger.info("SUCCESS! API call completed successfully")
            return True, response.json()
        else:
            logger.error(f"API call failed with status {response.status_code}")
            return False, response.text
            
    except Exception as e:
        logger.error(f"Exception during API call: {str(e)}")
        return False, str(e)

@st.cache_data(ttl=60)
def search_media(_config: Config, search_term: str, search_type: str = "hash") -> Optional[List[Dict]]:
    """Search for media items by hash or title"""
    try:
        logger.info(f"Searching media with term: {search_term}, type: {search_type}")
        
        if search_type == "hash":
            params = {"hash": search_term}
        else:
            params = {"media_title": search_term}
            
        response = requests.get(
            _config.media_endpoint,
            params=params,
            timeout=_config.api_timeout
        )
        
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, dict):
            items = data.get("data", [data])
        elif isinstance(data, list):
            items = data
        else:
            items = []
            
        logger.info(f"Found {len(items)} items")
        return items
        
    except Exception as e:
        logger.error(f"Failed to search media: {str(e)}")
        st.error(f"Failed to search media: {str(e)}")
        return None

def display_focused_item(item: Dict, config: Config):
    """Display focused item with toggles and submit button"""
    st.subheader(f"🎬 {item.get('media_title', 'Unknown')}")
    st.write(f"**Hash:** `{item.get('hash')}`")
    
    # Show resolution and video codec
    resolution = item.get('resolution', 'Unknown')
    video_codec = item.get('video_codec') or 'None'
    st.write(f"**Resolution:** {resolution} | **Video Codec:** {video_codec}")
    
    # Show original title
    original_title = item.get('original_title', 'Unknown')
    st.write(f"**Original Title:** {original_title}")
    
    # Current values
    current_pipeline = item.get('pipeline_status', 'ingested')
    current_error = item.get('error_status', False)
    current_rejection = item.get('rejection_status', 'unfiltered')
    
    # Show current status
    st.write("**Current Status:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"Pipeline: {current_pipeline}")
    with col2:
        st.info(f"Error: {current_error}")
    with col3:
        st.info(f"Rejection: {current_rejection}")
    
    # Show additional status details if available
    error_condition = item.get('error_condition')
    rejection_reason = item.get('rejection_reason')
    
    if error_condition or rejection_reason:
        st.write("**Additional Details:**")
        detail_col1, detail_col2 = st.columns(2)
        
        with detail_col1:
            if error_condition:
                st.warning(f"**Error Condition:** {error_condition}")
            else:
                st.write("**Error Condition:** None")
        
        with detail_col2:
            if rejection_reason:
                st.warning(f"**Rejection Reason:** {rejection_reason}")
            else:
                st.write("**Rejection Reason:** None")
    
    st.divider()
    st.write("**Update Values:**")
    
    # Dropdown toggles
    col1, col2, col3 = st.columns(3)
    
    with col1:
        pipeline_options = ['ingested', 'paused', 'parsed', 'rejected', 'file_accepted', 
                          'metadata_collected', 'media_accepted', 'downloading', 
                          'downloaded', 'transferred', 'complete']
        if current_pipeline not in pipeline_options:
            pipeline_options.append(current_pipeline)
        
        new_pipeline = st.selectbox(
            "Pipeline Status",
            options=pipeline_options,
            index=pipeline_options.index(current_pipeline),
            key="pipeline_select"
        )
    
    with col2:
        new_error = st.selectbox(
            "Error Status", 
            options=[False, True],
            index=1 if current_error else 0,
            key="error_select"
        )
    
    with col3:
        rejection_options = ['unfiltered', 'accepted', 'rejected', 'override']
        if current_rejection not in rejection_options:
            rejection_options.append(current_rejection)
        
        new_rejection = st.selectbox(
            "Rejection Status",
            options=rejection_options,
            index=rejection_options.index(current_rejection),
            key="rejection_select"
        )
    
    # Submit button
    st.divider()
    if st.button("Submit Pipeline Update", type="primary", use_container_width=True):
        logger.info(f"Submit button clicked for hash: {item.get('hash')}")
        logger.info(f"Current values - pipeline: {current_pipeline}, error: {current_error}, rejection: {current_rejection}")
        logger.info(f"New values - pipeline: {new_pipeline}, error: {new_error}, rejection: {new_rejection}")
        
        # Prepare updates
        updates = {}
        if new_pipeline != current_pipeline:
            updates['pipeline_status'] = new_pipeline
        if new_error != current_error:
            updates['error_status'] = new_error
        if new_rejection != current_rejection:
            updates['rejection_status'] = new_rejection
        
        if updates:
            logger.info(f"Applying updates: {updates}")
            with st.spinner("Updating pipeline status..."):
                success, result = make_patch_call(config, item.get('hash'), updates)
            
            if success:
                st.success("Pipeline status updated successfully!")
                st.json(result)
                
                # Refresh the item data to show updated values
                logger.info(f"Refreshing item data for hash: {item.get('hash')}")
                updated_results = search_media(config, item.get('hash'), "hash")
                
                if updated_results and len(updated_results) > 0:
                    st.session_state.selected_item = updated_results[0]
                    logger.info("Item data refreshed with updated values")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    logger.warning("Failed to refresh item data")
                    st.cache_data.clear()
                    st.rerun()
            else:
                st.error("Failed to update pipeline status!")
                st.code(result)
        else:
            st.info("No changes detected")

def main():
    """Main application function"""
    try:
        config = Config()
        logger.info("Configuration loaded successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        st.error(f"Configuration Error: {str(e)}")
        return
    
    st.title("media-pipeline")
    
    # Initialize session state
    if 'selected_item' not in st.session_state:
        st.session_state.selected_item = None
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    
    # Search section
    st.subheader("Search Media")
    
    search_col1, search_col2 = st.columns([3, 1])
    
    with search_col1:
        search_term = st.text_input("Search Term", placeholder="Enter hash or media title...")
    
    with search_col2:
        search_type = st.selectbox("Search By", ["title", "hash"])
    
    search_button = st.button("Search", use_container_width=True)
    
    # Handle search
    if search_button and search_term:
        logger.info(f"Search initiated: {search_term} ({search_type})")
        
        with st.spinner("Searching..."):
            results = search_media(config, search_term, search_type)
        
        if results:
            st.session_state.search_results = results
            
            # Auto-select if only one result
            if len(results) == 1:
                st.session_state.selected_item = results[0]
                logger.info(f"Auto-selected single result: {results[0].get('hash')}")
            else:
                st.session_state.selected_item = None
        else:
            st.session_state.search_results = None
            st.session_state.selected_item = None
    
    elif search_button and not search_term:
        st.warning("Please enter a search term")
    
    # Display results or focused item
    if st.session_state.selected_item:
        # Show focused item with toggles
        st.divider()
        display_focused_item(st.session_state.selected_item, config)
        
        # Back button
        if st.button("← Back to Results"):
            st.session_state.selected_item = None
            st.rerun()
    
    elif st.session_state.search_results:
        # Show multiple results for selection
        st.success(f"Found {len(st.session_state.search_results)} result(s)")
        st.write("**Select an item to edit:**")
        
        for idx, item in enumerate(st.session_state.search_results):
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.write(f"**{item.get('media_title', 'Unknown')}**")
                    st.write(f"Pipeline: {item.get('pipeline_status')} | Error: {item.get('error_status')} | Rejection: {item.get('rejection_status')}")
                    
                    # Show resolution and video codec
                    resolution = item.get('resolution', 'Unknown')
                    video_codec = item.get('video_codec') or 'None'
                    st.write(f"Resolution: {resolution} | Video Codec: {video_codec}")
                    
                    # Show original title
                    original_title = item.get('original_title', 'Unknown')
                    st.write(f"Original Title: {original_title}")
                    
                    st.write(f"Hash: `{item.get('hash')}`")
                
                with col2:
                    if st.button("Select", key=f"select_{idx}"):
                        st.session_state.selected_item = item
                        logger.info(f"Selected item: {item.get('hash')}")
                        st.rerun()
                
                st.divider()

if __name__ == "__main__":
    main()