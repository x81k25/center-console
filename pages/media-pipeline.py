import streamlit as st
import requests
import pandas as pd
from config import Config
from typing import Dict, List, Optional, Any
import time

st.set_page_config(
    page_title="Media Pipeline",
    page_icon="🔧",
    layout="wide"
)

# Custom CSS for styling
st.markdown("""
<style>
.stTextInput > div > div > input {
    font-family: 'Courier New', monospace;
}
.search-result {
    border: 1px solid #ddd;
    border-radius: 5px;
    padding: 10px;
    margin-bottom: 10px;
}
.success-message {
    background-color: #d4edda;
    color: #155724;
    padding: 10px;
    border-radius: 5px;
    margin: 10px 0;
}
.error-message {
    background-color: #f8d7da;
    color: #721c24;
    padding: 10px;
    border-radius: 5px;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def search_media_by_hash(_config: Config, hash_value: str) -> Optional[Dict]:
    """Search media by hash value"""
    try:
        params = {"hash": hash_value}
        response = requests.get(
            _config.media_endpoint,
            params=params,
            timeout=_config.api_timeout
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to search by hash: {str(e)}")
        return None

@st.cache_data(ttl=60)
def search_media_by_title(_config: Config, title: str) -> Optional[Dict]:
    """Search media by title"""
    try:
        params = {"media_title": title}
        response = requests.get(
            _config.media_endpoint,
            params=params,
            timeout=_config.api_timeout
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to search by title: {str(e)}")
        return None

@st.cache_data(ttl=300)
def get_pipeline_options(_config: Config) -> Dict[str, List[str]]:
    """Get all possible pipeline status values - using actual database values"""
    return {
        'pipeline_status': ['ingested', 'rejected', 'downloading', 'complete'],
        'error_status': ['true', 'false'],
        'rejection_status': ['unfiltered', 'accepted', 'rejected']
    }

def update_pipeline_status(_config: Config, hash_id: str, updates: Dict[str, Any]) -> bool:
    """Update pipeline status for a media item"""
    try:
        # Remove empty values
        payload = {k: v for k, v in updates.items() if v}
        
        response = requests.patch(
            _config.get_media_pipeline_endpoint(hash_id),
            json=payload,
            timeout=_config.api_timeout
        )
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Failed to update pipeline status: {str(e)}")
        return False

def display_media_item(item: Dict, options: Dict[str, List[str]], config: Config):
    """Display a single media item with edit capabilities"""
    with st.container():
        st.markdown('<div class="search-result">', unsafe_allow_html=True)
        
        # Display basic info
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write(f"**{item.get('media_title', 'Unknown')}**")
            st.write(f"Hash: `{item.get('hash', 'NULL')}`")
            if item.get('media_type'):
                st.write(f"Type: {item.get('media_type')}")
        
        with col2:
            current_pipeline = item.get('pipeline_status', '')
            st.write(f"**Pipeline Status:** {current_pipeline}")
            
            current_error = item.get('error_status', '')
            if current_error:
                st.write(f"**Error Status:** {current_error}")
        
        with col3:
            current_rejection = item.get('rejection_status', '')
            st.write(f"**Rejection Status:** {current_rejection}")
            
            if item.get('error_condition'):
                st.write(f"**Error Condition:** {item.get('error_condition')}")
        
        # Edit form
        with st.form(f"edit_form_{item.get('hash', 'unknown')}"):
            st.write("**Update Pipeline Status:**")
            
            form_col1, form_col2, form_col3 = st.columns(3)
            
            with form_col1:
                new_pipeline_status = st.selectbox(
                    "Pipeline Status",
                    options=[""] + options['pipeline_status'],
                    index=0,
                    key=f"pipeline_{item.get('hash', 'unknown')}"
                )
            
            with form_col2:
                new_error_status = st.selectbox(
                    "Error Status",
                    options=[""] + options['error_status'],
                    index=0,
                    key=f"error_{item.get('hash', 'unknown')}",
                    help="Boolean field: true or false"
                )
            
            with form_col3:
                new_rejection_status = st.selectbox(
                    "Rejection Status",
                    options=[""] + options['rejection_status'],
                    index=0,
                    key=f"rejection_{item.get('hash', 'unknown')}"
                )
            
            submitted = st.form_submit_button("Update Pipeline", type="primary")
            
            if submitted:
                updates = {}
                if new_pipeline_status:
                    updates['pipeline_status'] = new_pipeline_status
                if new_error_status:
                    # Convert string to boolean for error_status
                    updates['error_status'] = new_error_status == 'true'
                if new_rejection_status:
                    updates['rejection_status'] = new_rejection_status
                
                if updates:
                    if update_pipeline_status(config, item.get('hash'), updates):
                        st.success(f"✅ Successfully updated pipeline status for {item.get('media_title', 'Unknown')}")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                else:
                    st.warning("No updates specified")
        
        # Expandable details
        with st.expander(f"📋 Full Details for {item.get('media_title', 'Unknown')}", expanded=False):
            detail_col1, detail_col2 = st.columns(2)
            
            with detail_col1:
                st.write("**Basic Info:**")
                st.write(f"• **Hash:** {item.get('hash', 'NULL')}")
                st.write(f"• **IMDB ID:** {item.get('imdb_id', 'NULL')}")
                st.write(f"• **Media Type:** {item.get('media_type', 'NULL')}")
                st.write(f"• **Release Year:** {item.get('release_year', 'NULL')}")
                st.write(f"• **Runtime:** {item.get('runtime', 'NULL')} min")
                st.write(f"• **Original Language:** {item.get('original_language', 'NULL')}")
                
                st.write("**Pipeline Details:**")
                st.write(f"• **Pipeline Status:** {item.get('pipeline_status', 'NULL')}")
                st.write(f"• **Error Status:** {item.get('error_status', 'NULL')}")
                st.write(f"• **Error Condition:** {item.get('error_condition', 'NULL')}")
                st.write(f"• **Rejection Status:** {item.get('rejection_status', 'NULL')}")
                st.write(f"• **Rejection Reason:** {item.get('rejection_reason', 'NULL')}")
            
            with detail_col2:
                st.write("**Technical Details:**")
                st.write(f"• **Resolution:** {item.get('resolution', 'NULL')}")
                st.write(f"• **Video Codec:** {item.get('video_codec', 'NULL')}")
                st.write(f"• **Audio Codec:** {item.get('audio_codec', 'NULL')}")
                st.write(f"• **Upload Type:** {item.get('upload_type', 'NULL')}")
                st.write(f"• **Uploader:** {item.get('uploader', 'NULL')}")
                
                st.write("**Paths:**")
                st.write(f"• **Parent Path:** {item.get('parent_path', 'NULL')}")
                st.write(f"• **Target Path:** {item.get('target_path', 'NULL')}")
                st.write(f"• **Original Path:** {item.get('original_path', 'NULL')}")
                
                st.write("**Timestamps:**")
                st.write(f"• **Created:** {item.get('created_at', 'NULL')}")
                st.write(f"• **Updated:** {item.get('updated_at', 'NULL')}")
        
        st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Main application function"""
    try:
        config = Config()
    except ValueError as e:
        st.error(f"Configuration Error: {str(e)}")
        st.info("Please set the required environment variables: REAR_DIFF_HOST, REAR_DIFF_PORT_EXTERNAL")
        return
    
    st.title("🔧 Media Pipeline Management")
    
    # Search section
    st.header("🔍 Search Media")
    
    search_col1, search_col2 = st.columns(2)
    
    with search_col1:
        st.subheader("Search by Hash")
        hash_input = st.text_input(
            "Enter hash value",
            placeholder="e.g., abc123def456...",
            help="Enter the full hash value to search for a specific media item"
        )
        search_hash_btn = st.button("Search by Hash", type="primary")
    
    with search_col2:
        st.subheader("Search by Title")
        title_input = st.text_input(
            "Enter media title",
            placeholder="e.g., The Matrix",
            help="Enter part or full title to search for media items"
        )
        search_title_btn = st.button("Search by Title", type="primary")
    
    # Get pipeline options
    options = get_pipeline_options(config)
    
    # Handle search
    search_results = None
    
    if search_hash_btn and hash_input:
        with st.spinner("Searching by hash..."):
            search_results = search_media_by_hash(config, hash_input.strip())
    
    elif search_title_btn and title_input:
        with st.spinner("Searching by title..."):
            search_results = search_media_by_title(config, title_input.strip())
    
    # Display results
    if search_results:
        items = search_results.get("data", [])
        total_items = search_results.get("total", 0)
        
        if items:
            st.success(f"Found {total_items} item(s)")
            st.divider()
            
            for item in items:
                display_media_item(item, options, config)
                st.divider()
        else:
            st.info("No items found matching your search criteria")
    
    # Help section
    st.header("ℹ️ Help")
    with st.expander("How to use this page", expanded=False):
        st.markdown("""
        **Search Options:**
        - **Hash Search**: Enter the exact hash value to find a specific media item
        - **Title Search**: Enter part or full media title to find matching items
        
        **Pipeline Status Updates:**
        - Select new values from the dropdowns to update pipeline status
        - Leave fields empty to keep current values
        - Click "Update Pipeline" to apply changes
        
        **Available Fields:**
        - **Pipeline Status**: Current processing state (ingested, rejected, downloading, complete)
        - **Error Status**: Boolean field indicating if there was an error (true/false)
        - **Rejection Status**: Item filtering status (unfiltered, accepted, rejected)
        
        **Tips:**
        - Use the expandable details section to see full item information
        - Changes are applied immediately and will refresh the display
        - Hash searches are exact matches, title searches are partial matches
        """)

if __name__ == "__main__":
    main()