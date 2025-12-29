import streamlit as st
import requests
import logging
from config import Config
import json
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="media",
    page_icon="./favicon/favicon.ico",
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


def make_patch_call(config: Config, hash_id: str, updates: Dict):
    """Make a PATCH call to update pipeline status"""
    payload = {"hash": hash_id, **updates}
    endpoint = config.get_media_pipeline_endpoint(hash_id)

    st.session_state.last_api_call = f"PATCH {endpoint}"
    st.session_state.last_api_payload = json.dumps(payload, indent=2)

    try:
        logger.info(f"PATCH {endpoint} with payload: {json.dumps(payload)}")

        response = requests.patch(
            endpoint,
            json=payload,
            timeout=config.api_timeout
        )

        if response.status_code == 200:
            logger.info("Pipeline update successful")
            return True, response.json()
        else:
            logger.error(f"Pipeline update failed: {response.status_code}")
            return False, response.text

    except Exception as e:
        logger.error(f"Exception during API call: {str(e)}")
        return False, str(e)


def make_soft_delete_call(config: Config, hash_id: str):
    """Make a PATCH call to soft delete a media entry"""
    endpoint = f"{config.base_url}media/{hash_id}/soft_delete"

    try:
        logger.info(f"PATCH {endpoint} (soft delete)")

        response = requests.patch(
            endpoint,
            timeout=config.api_timeout
        )

        if response.status_code == 200:
            logger.info("Soft delete successful")
            return True, response.json()
        else:
            logger.error(f"Soft delete failed: {response.status_code}")
            return False, response.text

    except Exception as e:
        logger.error(f"Exception during soft delete call: {str(e)}")
        return False, str(e)


def fetch_media_data(config: Config, limit: int = 20, search_term: str = None, search_type: str = "title", error_status: bool = None) -> Optional[Dict]:
    """Fetch media data from the API"""
    try:
        params = {
            "limit": limit,
            "sort_by": "updated_at",
            "sort_order": "desc"
        }

        if search_term:
            if search_type == "hash":
                params["hash"] = search_term
            else:
                params["media_title"] = search_term

        if error_status is not None:
            params["error_status"] = str(error_status).lower()

        response = requests.get(
            config.media_endpoint,
            params=params,
            timeout=config.api_timeout
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch media data: {str(e)}")
        return None


def fetch_error_count(config: Config) -> int:
    """Fetch count of items with error_status = True"""
    try:
        params = {
            "limit": 1000,
            "error_status": "true"
        }
        response = requests.get(
            config.media_endpoint,
            params=params,
            timeout=config.api_timeout
        )
        response.raise_for_status()
        data = response.json()
        return len(data.get("data", []))
    except Exception:
        return 0


def display_media_item(item: Dict, idx: int, config: Config):
    """Display a single media item row with expandable details"""
    with st.container():
        # Main row with basic info
        col1, col2, col3, col4, col5, col_buttons = st.columns([2.2, 1, 1.2, 1, 1.2, 2.4])

        with col1:
            st.write(f"**{item.get('media_title', 'Unknown')}**")
            if item.get('media_type') == 'tv_show' and item.get('season') and item.get('episode'):
                st.caption(f"S{item.get('season')}E{item.get('episode')}")

        with col2:
            media_type = item.get('media_type', 'unknown')
            st.write(f"**{media_type}**")
            st.caption("Type")

        with col3:
            pipeline_status = item.get('pipeline_status', 'unknown')
            status_color = {
                'ingested': '#28a745',
                'processed': '#007bff',
                'failed': '#dc3545',
                'pending': '#ffc107',
                'complete': '#28a745',
                'downloading': '#17a2b8',
                'transferred': '#6f42c1',
                'rejected': '#dc3545',
                'paused': '#ffc107'
            }.get(pipeline_status, '#6c757d')
            st.markdown(f'<span style="color: {status_color}; font-weight: bold;">{pipeline_status}</span>', unsafe_allow_html=True)
            st.caption("Pipeline")

        with col4:
            error_status = item.get('error_status', False)
            error_color = '#dc3545' if error_status else '#28a745'
            error_text = 'True' if error_status else 'False'
            st.markdown(f'<span style="color: {error_color}; font-weight: bold;">{error_text}</span>', unsafe_allow_html=True)
            st.caption("Error")

        with col5:
            rejection_status = item.get('rejection_status', 'unfiltered')
            rejection_color = {
                'unfiltered': '#6c757d',
                'accepted': '#28a745',
                'rejected': '#dc3545',
                'override': '#ffc107'
            }.get(rejection_status, '#6c757d')
            st.markdown(f'<span style="color: {rejection_color}; font-weight: bold;">{rejection_status}</span>', unsafe_allow_html=True)
            st.caption("Rejection")

        with col_buttons:
            btn1, btn2 = st.columns(2)
            with btn1:
                if st.button("Edit", key=f"edit_{idx}", use_container_width=True):
                    st.session_state.selected_item = item
                    st.rerun()
            with btn2:
                if st.button("Re-ingest", key=f"reingest_{idx}", use_container_width=True):
                    updates = {
                        'pipeline_status': 'ingested',
                        'error_status': False,
                        'rejection_status': 'unfiltered'
                    }
                    success, result = make_patch_call(config, item.get('hash'), updates)
                    if success:
                        st.rerun()
                    else:
                        st.error(f"Failed to re-ingest: {result}")

        st.divider()


def display_focused_item(item: Dict, config: Config):
    """Display focused item with pipeline editing controls"""
    st.subheader(f"{item.get('media_title', 'Unknown')}")
    st.write(f"**Hash:** `{item.get('hash')}`")

    resolution = item.get('resolution', 'Unknown')
    video_codec = item.get('video_codec') or 'None'
    st.write(f"**Resolution:** {resolution} | **Video Codec:** {video_codec}")

    original_title = item.get('original_title', 'Unknown')
    st.write(f"**Original Title:** {original_title}")

    # Current values
    current_pipeline = item.get('pipeline_status', 'ingested')
    current_error = item.get('error_status', False)
    current_rejection = item.get('rejection_status', 'unfiltered')

    st.write("**Current Status:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"Pipeline: {current_pipeline}")
    with col2:
        st.info(f"Error: {current_error}")
    with col3:
        st.info(f"Rejection: {current_rejection}")

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

    st.divider()
    button_col1, button_col2 = st.columns(2)

    with button_col1:
        if st.button("Back to Results", use_container_width=True):
            st.session_state.selected_item = None
            st.rerun()

    with button_col2:
        if st.button("Submit Pipeline Update", use_container_width=True, key="submit_btn"):
            updates = {}
            if new_pipeline != current_pipeline:
                updates['pipeline_status'] = new_pipeline
            if new_error != current_error:
                updates['error_status'] = new_error
            if new_rejection != current_rejection:
                updates['rejection_status'] = new_rejection

            if updates:
                with st.spinner("Updating pipeline status..."):
                    success, result = make_patch_call(config, item.get('hash'), updates)

                if success:
                    st.success("Pipeline status updated successfully!")
                    st.json(result)
                    st.session_state.selected_item = None
                    st.rerun()
                else:
                    st.error("Failed to update pipeline status!")
                    st.code(result)
            else:
                st.info("No changes detected")

    # Custom button styling using key-based CSS selectors
    st.markdown("""
    <style>
    .st-key-submit_btn button {
        background-color: #28a745 !important;
        color: white !important;
        border: none !important;
    }
    .st-key-submit_btn button:hover {
        background-color: #218838 !important;
        color: white !important;
    }
    .st-key-delete_btn button {
        background-color: #dc3545 !important;
        color: white !important;
        border: none !important;
    }
    .st-key-delete_btn button:hover {
        background-color: #c82333 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

    if st.button("Delete Media Entry", use_container_width=True, key="delete_btn"):
        with st.spinner("Deleting..."):
            success, result = make_soft_delete_call(config, item.get('hash'))
        if success:
            st.success("Media entry soft deleted successfully!")
            st.session_state.selected_item = None
            st.rerun()
        else:
            st.error(f"Failed to delete: {result}")

    # Expandable details section
    with st.expander(f"Details for {item.get('media_title', 'Unknown')}", expanded=False):
        detail_col1, detail_col2 = st.columns(2)

        with detail_col1:
            st.write("**Basic Info:**")
            st.write(f"- **Hash:** {item.get('hash', 'NULL')}")
            st.write(f"- **IMDB ID:** {item.get('imdb_id', 'NULL')}")
            st.write(f"- **TMDB ID:** {item.get('tmdb_id', 'NULL')}")
            st.write(f"- **Media Type:** {item.get('media_type', 'NULL')}")
            st.write(f"- **Release Year:** {item.get('release_year', 'NULL')}")
            st.write(f"- **Runtime:** {item.get('runtime', 'NULL')} min")
            st.write(f"- **Original Language:** {item.get('original_language', 'NULL')}")
            st.write(f"- **Origin Country:** {item.get('origin_country', 'NULL')}")

            st.write("**Pipeline Status:**")
            st.write(f"- **Status:** {item.get('pipeline_status', 'NULL')}")
            st.write(f"- **Error Status:** {item.get('error_status', 'NULL')}")
            st.write(f"- **Error Condition:** {item.get('error_condition', 'NULL')}")
            st.write(f"- **Rejection Status:** {item.get('rejection_status', 'NULL')}")
            st.write(f"- **Rejection Reason:** {item.get('rejection_reason', 'NULL')}")

        with detail_col2:
            st.write("**Technical Details:**")
            st.write(f"- **Resolution:** {item.get('resolution', 'NULL')}")
            st.write(f"- **Video Codec:** {item.get('video_codec', 'NULL')}")
            st.write(f"- **Audio Codec:** {item.get('audio_codec', 'NULL')}")
            st.write(f"- **Upload Type:** {item.get('upload_type', 'NULL')}")
            st.write(f"- **Uploader:** {item.get('uploader', 'NULL')}")
            st.write(f"- **RSS Source:** {item.get('rss_source', 'NULL')}")

            st.write("**Ratings & Scores:**")
            st.write(f"- **IMDB Rating:** {item.get('imdb_rating', 'NULL')}")
            st.write(f"- **IMDB Votes:** {item.get('imdb_votes', 'NULL')}")
            st.write(f"- **TMDB Rating:** {item.get('tmdb_rating', 'NULL')}")
            st.write(f"- **TMDB Votes:** {item.get('tmdb_votes', 'NULL')}")
            st.write(f"- **RT Score:** {item.get('rt_score', 'NULL')}")
            st.write(f"- **Metascore:** {item.get('metascore', 'NULL')}")

        st.write("**File Paths:**")
        st.write(f"- **Original Title:** {item.get('original_title', 'NULL')}")
        st.write(f"- **Parent Path:** {item.get('parent_path', 'NULL')}")
        st.write(f"- **Target Path:** {item.get('target_path', 'NULL')}")
        st.write(f"- **Original Path:** {item.get('original_path', 'NULL')}")

        if item.get('original_link'):
            st.write("**Original Link:**")
            st.code(item.get('original_link'), language=None)

        st.write("**Additional Info:**")
        st.write(f"- **Genres:** {', '.join(item.get('genre', [])) if item.get('genre') else 'NULL'}")
        st.write(f"- **Production Status:** {item.get('production_status', 'NULL')}")
        st.write(f"- **Tagline:** {item.get('tagline', 'NULL')}")

        if item.get('overview'):
            st.write("**Overview:**")
            st.write(item.get('overview'))

        st.write("**Timestamps:**")
        st.write(f"- **Created:** {item.get('created_at', 'NULL')}")
        st.write(f"- **Updated:** {item.get('updated_at', 'NULL')}")


def main():
    """Main application function"""
    try:
        config = Config()
    except ValueError as e:
        st.error(f"Configuration Error: {str(e)}")
        st.info("Please set the required environment variables: REAR_DIFF_HOST, REAR_DIFF_PORT_EXTERNAL")
        return

    st.title("media")

    # Initialize session state
    if 'selected_item' not in st.session_state:
        st.session_state.selected_item = None
    if 'search_term' not in st.session_state:
        st.session_state.search_term = ""
    if 'search_type' not in st.session_state:
        st.session_state.search_type = "title"
    if 'filter_errors' not in st.session_state:
        st.session_state.filter_errors = False

    # If item is selected, show edit view
    if st.session_state.selected_item:
        display_focused_item(st.session_state.selected_item, config)
        return

    # Error indicator and filter
    error_count = fetch_error_count(config)
    error_col1, error_col2, error_col3 = st.columns([1, 1, 4])

    with error_col1:
        if error_count > 0:
            st.markdown(f'<span style="color: #dc3545; font-weight: bold; font-size: 1.2em;">Errors: {error_count}</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span style="color: #28a745; font-weight: bold; font-size: 1.2em;">Errors: 0</span>', unsafe_allow_html=True)

    with error_col2:
        if st.session_state.filter_errors:
            if st.button("Show All", use_container_width=True):
                st.session_state.filter_errors = False
                st.rerun()
        else:
            if st.button("Show Errors", type="primary" if error_count > 0 else "secondary", use_container_width=True):
                st.session_state.filter_errors = True
                st.rerun()

    # Search section
    search_col1, search_col2, search_col3 = st.columns([3, 1, 1])

    with search_col1:
        search_term = st.text_input("Search", placeholder="Enter hash or title...", key="search_input")

    with search_col2:
        search_type = st.selectbox("Search By", ["hash", "title"], key="search_type_select")

    with search_col3:
        st.write("")  # Spacer for alignment
        search_clicked = st.button("Search", use_container_width=True)

    # Build API call display
    params = {
        "limit": 20,
        "sort_by": "updated_at",
        "sort_order": "desc"
    }
    if search_term:
        if search_type == "hash":
            params["hash"] = search_term
        else:
            params["media_title"] = search_term

    if st.session_state.filter_errors:
        params["error_status"] = "true"

    param_string = "&".join([f"{k}={v}" for k, v in params.items()])
    api_url = f"{config.media_endpoint}?{param_string}"
    st.code(api_url, language="bash")

    # Fetch data
    error_filter = True if st.session_state.filter_errors else None
    data = fetch_media_data(config, limit=20, search_term=search_term if search_term else None, search_type=search_type, error_status=error_filter)

    if not data:
        return

    items = data.get("data", [])

    # Display count
    filter_desc = " with errors" if st.session_state.filter_errors else ""
    if search_term:
        st.info(f"Found {len(items)} media items{filter_desc} matching '{search_term}'")
    else:
        st.info(f"Showing {len(items)} most recent media items{filter_desc}")

    if not items:
        st.info("No media items found")
        return

    # Display each media item
    for idx, item in enumerate(items):
        display_media_item(item, idx, config)


if __name__ == "__main__":
    main()
