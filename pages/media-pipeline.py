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

/* Pipeline status icons */
.status-ingested { color: #17a2b8; font-weight: bold; }
.status-paused { color: #ffc107; font-weight: bold; }
.status-parsed { color: #6c757d; font-weight: bold; }
.status-rejected { color: #dc3545; font-weight: bold; }
.status-file_accepted { color: #20c997; font-weight: bold; }
.status-metadata_collected { color: #6f42c1; font-weight: bold; }
.status-media_accepted { color: #28a745; font-weight: bold; }
.status-downloading { color: #fd7e14; font-weight: bold; }
.status-downloaded { color: #007bff; font-weight: bold; }
.status-transferred { color: #6610f2; font-weight: bold; }
.status-complete { color: #28a745; font-weight: bold; }

/* Rejection status styling */
.rejection-unfiltered { color: #6c757d; font-weight: bold; }
.rejection-accepted { color: #28a745; font-weight: bold; }
.rejection-rejected { color: #dc3545; font-weight: bold; }
.rejection-override { color: #fd7e14; font-weight: bold; }

/* Error status styling */
.error-true { color: #dc3545; font-weight: bold; }
.error-false { color: #28a745; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=5)
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

@st.cache_data(ttl=5)
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
    """Get all possible pipeline status values - using API schema values"""
    return {
        'pipeline_status': ['ingested', 'paused', 'parsed', 'rejected', 'file_accepted', 'metadata_collected', 'media_accepted', 'downloading', 'downloaded', 'transferred', 'complete'],
        'error_status': ['true', 'false'],
        'rejection_status': ['unfiltered', 'accepted', 'rejected', 'override']
    }

def get_pipeline_status_icon(status: str) -> str:
    """Get icon and CSS class for pipeline status"""
    icons = {
        'ingested': '📥',
        'paused': '⏸️',
        'parsed': '📝',
        'rejected': '❌',
        'file_accepted': '✅',
        'metadata_collected': '📊',
        'media_accepted': '🎬',
        'downloading': '⬇️',
        'downloaded': '💾',
        'transferred': '🔄',
        'complete': '✅'
    }
    return icons.get(status, '❓')

def get_rejection_status_icon(status: str) -> str:
    """Get icon for rejection status"""
    icons = {
        'unfiltered': '⚪',
        'accepted': '✅',
        'rejected': '❌',
        'override': '🔄'
    }
    return icons.get(status, '❓')

def get_error_status_icon(status: bool) -> str:
    """Get icon for error status"""
    return '❌' if status else '✅'

def update_pipeline_status(_config: Config, hash_id: str, updates: Dict[str, Any]) -> bool:
    """Update pipeline status for a media item"""
    try:
        # Remove empty values and add required hash field
        payload = {k: v for k, v in updates.items() if v is not None}
        payload['hash'] = hash_id  # Required field according to API schema
        
        response = requests.patch(
            _config.get_media_pipeline_endpoint(hash_id),
            json=payload,
            timeout=_config.api_timeout
        )
        
        # Check for specific permission error
        if response.status_code == 400:
            error_text = response.text
            if "permission denied" in error_text.lower():
                st.error("❌ Database permission error: The API user doesn't have UPDATE permissions on the media table. Please contact the administrator to grant UPDATE permissions.")
                return False
        
        response.raise_for_status()
        
        # Parse response to check success/error
        result = response.json()
        if not result.get('success'):
            st.error(f"❌ API Error: {result.get('error', 'Unknown error')}")
            return False
            
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Failed to update pipeline status: {str(e)}")
        return False
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        return False

def display_media_item(item: Dict, options: Dict[str, List[str]], config: Config):
    """Display a single media item with edit capabilities"""
    with st.container():
        
        # Display basic info
        col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 1, 1, 1, 1])
        
        with col1:
            st.write(f"**{item.get('media_title', 'Unknown')}**")
            st.write(f"Hash: `{item.get('hash', 'NULL')}`")
            if item.get('media_type'):
                st.write(f"Type: {item.get('media_type')}")
        
        with col2:
            current_pipeline = item.get('pipeline_status', '')
            st.write(f"**Pipeline Status:**")
            if current_pipeline:
                icon = get_pipeline_status_icon(current_pipeline)
                st.markdown(f'<span class="status-{current_pipeline}">{icon} {current_pipeline}</span>', unsafe_allow_html=True)
            else:
                st.write("NULL")
        
        with col3:
            current_rejection = item.get('rejection_status', '')
            st.write(f"**Rejection Status:**")
            if current_rejection:
                icon = get_rejection_status_icon(current_rejection)
                st.markdown(f'<span class="rejection-{current_rejection}">{icon} {current_rejection}</span>', unsafe_allow_html=True)
            else:
                st.write("NULL")
        
        with col4:
            rejection_reason = item.get('rejection_reason', '')
            st.write(f"**Rejection Reason:**")
            st.write(f"{rejection_reason if rejection_reason else 'NULL'}")
        
        with col5:
            error_status = item.get('error_status', False)  # Default to False for boolean
            st.write(f"**Error Status:**")
            icon = get_error_status_icon(error_status)
            status_text = str(error_status).lower()
            st.markdown(f'<span class="error-{status_text}">{icon} {status_text}</span>', unsafe_allow_html=True)
        
        with col6:
            error_condition = item.get('error_condition', '')
            st.write(f"**Error Condition:**")
            st.write(f"{error_condition if error_condition else 'NULL'}")
        
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
                if new_pipeline_status and new_pipeline_status != "":
                    updates['pipeline_status'] = new_pipeline_status
                if new_error_status and new_error_status != "":
                    # Convert string to boolean for error_status
                    updates['error_status'] = new_error_status == 'true'
                if new_rejection_status and new_rejection_status != "":
                    updates['rejection_status'] = new_rejection_status
                
                # Debug info
                st.info(f"Debug: Form submitted with updates: {updates}")
                
                if updates:
                    st.info(f"Debug: Calling update_pipeline_status for hash: {item.get('hash')}")
                    if update_pipeline_status(config, item.get('hash'), updates):
                        st.success(f"✅ Successfully updated pipeline status for {item.get('media_title', 'Unknown')}")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                else:
                    st.warning("No updates specified - please select at least one field to update")
        
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
        total_items = len(items)  # Use actual length of items array
        
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
        - **Pipeline Status**: Current processing state (ingested, paused, parsed, rejected, file_accepted, metadata_collected, media_accepted, downloading, downloaded, transferred, complete)
        - **Error Status**: Boolean field indicating if there was an error (true/false)
        - **Rejection Status**: Item filtering status (unfiltered, accepted, rejected, override)
        
        **Tips:**
        - Use the expandable details section to see full item information
        - Changes are applied immediately and will refresh the display
        - Hash searches are exact matches, title searches are partial matches
        """)

if __name__ == "__main__":
    main()