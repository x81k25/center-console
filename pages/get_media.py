import streamlit as st
import requests
import pandas as pd
from config import Config
from typing import Dict, List, Optional
import time

st.set_page_config(
    page_title="get-media",
    page_icon="🎬",
    layout="wide"
)

# Custom CSS for styling
st.markdown("""
<style>
/* Status indicators */
.status-ingested { color: #28a745; font-weight: bold; }
.status-processed { color: #007bff; font-weight: bold; }
.status-failed { color: #dc3545; font-weight: bold; }
.status-pending { color: #ffc107; font-weight: bold; }
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
            col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 1, 1, 0.8, 0.8, 1, 1])
            
            with col1:
                st.write(f"**{item.get('media_title', 'Unknown')}**")
                # Show season/episode info for TV shows
                if item.get('media_type') == 'tv_show' and item.get('season') and item.get('episode'):
                    st.caption(f"S{item.get('season')}E{item.get('episode')}")
            
            with col2:
                resolution = item.get('resolution')
                if resolution:
                    st.write(f"**{resolution}**")
                    st.caption("Quality")
                else:
                    st.write("Quality: NULL")
            
            with col3:
                codec = item.get('video_codec')
                upload_type = item.get('upload_type')
                if codec and upload_type:
                    st.write(f"**{upload_type}**")
                    st.caption(f"{codec}")
                elif upload_type:
                    st.write(f"**{upload_type}**")
                    st.caption("Source")
                else:
                    st.write("Source: NULL")
            
            with col4:
                release_year = item.get('release_year')
                st.write(f"Year: {release_year if release_year else 'NULL'}")
            
            with col5:
                lang = item.get('original_language')
                st.write(f"Lang: {lang.upper() if lang else 'NULL'}")
            
            with col6:
                # Show pipeline status
                pipeline_status = item.get('pipeline_status', 'unknown')
                status_color = {
                    'ingested': '#28a745',
                    'processed': '#007bff', 
                    'failed': '#dc3545',
                    'pending': '#ffc107'
                }.get(pipeline_status, '#6c757d')
                st.markdown(f'<span style="color: {status_color}; font-weight: bold;">Status: {pipeline_status}</span>', unsafe_allow_html=True)
            
            with col7:
                uploader = item.get('uploader')
                if uploader:
                    st.write(f"**{uploader}**")
                    st.caption("Uploader")
                else:
                    st.write("Uploader: NULL")
            
            # Show error status if applicable
            if item.get('error_status') or item.get('rejection_status') != 'unfiltered':
                error_col1, error_col2, error_col3 = st.columns([2, 2, 6])
                with error_col1:
                    if item.get('error_status'):
                        st.error(f"Error: {item.get('error_condition', 'Unknown')}")
                with error_col2:
                    rejection_status = item.get('rejection_status')
                    if rejection_status and rejection_status != 'unfiltered':
                        st.warning(f"Rejected: {item.get('rejection_reason', 'Unknown')}")
            
            # Expandable details section
            with st.expander(f"📋 Details for {item.get('media_title', 'Unknown')}", expanded=False):
                detail_col1, detail_col2 = st.columns(2)
                
                with detail_col1:
                    st.write("**Basic Info:**")
                    st.write(f"• **Hash:** {item.get('hash', 'NULL')}")
                    st.write(f"• **IMDB ID:** {item.get('imdb_id', 'NULL')}")
                    st.write(f"• **TMDB ID:** {item.get('tmdb_id', 'NULL')}")
                    st.write(f"• **Media Type:** {item.get('media_type', 'NULL')}")
                    st.write(f"• **Release Year:** {item.get('release_year', 'NULL')}")
                    st.write(f"• **Runtime:** {item.get('runtime', 'NULL')} min")
                    st.write(f"• **Original Language:** {item.get('original_language', 'NULL')}")
                    st.write(f"• **Origin Country:** {item.get('origin_country', 'NULL')}")
                    
                    st.write("**Pipeline Status:**")
                    st.write(f"• **Status:** {item.get('pipeline_status', 'NULL')}")
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
                    st.write(f"• **RSS Source:** {item.get('rss_source', 'NULL')}")
                    
                    st.write("**Ratings & Scores:**")
                    st.write(f"• **IMDB Rating:** {item.get('imdb_rating', 'NULL')}")
                    st.write(f"• **IMDB Votes:** {item.get('imdb_votes', 'NULL')}")
                    st.write(f"• **TMDB Rating:** {item.get('tmdb_rating', 'NULL')}")
                    st.write(f"• **TMDB Votes:** {item.get('tmdb_votes', 'NULL')}")
                    st.write(f"• **RT Score:** {item.get('rt_score', 'NULL')}")
                    st.write(f"• **Metascore:** {item.get('metascore', 'NULL')}")
                
                st.write("**File Paths:**")
                st.write(f"• **Original Title:** {item.get('original_title', 'NULL')}")
                st.write(f"• **Parent Path:** {item.get('parent_path', 'NULL')}")
                st.write(f"• **Target Path:** {item.get('target_path', 'NULL')}")
                st.write(f"• **Original Path:** {item.get('original_path', 'NULL')}")
                
                if item.get('original_link'):
                    st.write("**Original Link:**")
                    st.code(item.get('original_link'), language=None)
                
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