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

/* Reduce spacing between captions and values */
.stCaption, [data-testid="stCaptionContainer"], small {
    margin-bottom: -15px !important;
    padding-bottom: 0 !important;
}
[data-testid="stMarkdownContainer"] p {
    margin-bottom: 0.5rem !important;
}

/* Reduce divider spacing */
hr {
    margin-top: 0.5rem !important;
    margin-bottom: 0.5rem !important;
}

/* Center button text vertically */
[data-testid="stBaseButton-secondary"] p,
[data-testid="stBaseButton-primary"] p,
.stButton button p {
    margin: 0 !important;
    padding-top: 2px !important;
}

/* Re-ingest button styling (green) */
[data-testid="stHorizontalBlock"] [class*="st-key-reingest_"] button {
    background-color: #28a745 !important;
    color: white !important;
    border: none !important;
}
[data-testid="stHorizontalBlock"] [class*="st-key-reingest_"] button:hover {
    background-color: #218838 !important;
    color: white !important;
}

/* Promote button styling (purple) */
[data-testid="stHorizontalBlock"] [class*="st-key-promote_"] button {
    background-color: #6f42c1 !important;
    color: white !important;
    border: none !important;
}
[data-testid="stHorizontalBlock"] [class*="st-key-promote_"] button:hover {
    background-color: #5a32a3 !important;
    color: white !important;
}

/* Finish button styling (blue) */
[data-testid="stHorizontalBlock"] [class*="st-key-finish_"] button {
    background-color: #007bff !important;
    color: white !important;
    border: none !important;
}
[data-testid="stHorizontalBlock"] [class*="st-key-finish_"] button:hover {
    background-color: #0056b3 !important;
    color: white !important;
}

/* Delete button styling (red) */
[data-testid="stHorizontalBlock"] [class*="st-key-delete_"] button {
    background-color: #dc3545 !important;
    color: white !important;
    border: none !important;
}
[data-testid="stHorizontalBlock"] [class*="st-key-delete_"] button:hover {
    background-color: #c82333 !important;
    color: white !important;
}
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


def make_promote_call(config: Config, hash_id: str):
    """Make a PATCH call to promote a media entry (clear errors, set to downloaded)"""
    endpoint = f"{config.base_url}media/{hash_id}/promote"

    try:
        logger.info(f"PATCH {endpoint} (promote)")

        response = requests.patch(
            endpoint,
            timeout=config.api_timeout
        )

        if response.status_code == 200:
            logger.info("Promote successful")
            return True, response.json()
        else:
            logger.error(f"Promote failed: {response.status_code}")
            return False, response.text

    except Exception as e:
        logger.error(f"Exception during promote call: {str(e)}")
        return False, str(e)


def make_finish_call(config: Config, hash_id: str):
    """Make a PATCH call to finish a media entry (mark complete, remove from Transmission)"""
    endpoint = f"{config.base_url}media/{hash_id}/finish"

    try:
        logger.info(f"PATCH {endpoint} (finish)")

        response = requests.patch(
            endpoint,
            timeout=config.api_timeout
        )

        if response.status_code == 200:
            logger.info("Finish successful")
            return True, response.json()
        else:
            logger.error(f"Finish failed: {response.status_code}")
            return False, response.text

    except Exception as e:
        logger.error(f"Exception during finish call: {str(e)}")
        return False, str(e)


def fetch_media_data(config: Config, limit: int = 20, offset: int = 0, search_term: str = None, search_type: str = "title", error_status: bool = None, pipeline_statuses: List[str] = None) -> Optional[Dict]:
    """Fetch media data from the API. If multiple pipeline_statuses are provided, makes separate calls and merges results."""
    try:
        base_params = {
            "limit": limit,
            "offset": offset,
            "sort_by": "updated_at",
            "sort_order": "desc"
        }

        if search_term:
            if search_type == "hash":
                base_params["hash"] = search_term
            else:
                base_params["media_title"] = search_term

        if error_status is not None:
            base_params["error_status"] = str(error_status).lower()

        # If multiple pipeline statuses, make separate calls and merge
        if pipeline_statuses and len(pipeline_statuses) > 1:
            all_items = []
            seen_hashes = set()
            for status in pipeline_statuses:
                params = {**base_params, "pipeline_status": status}
                response = requests.get(
                    config.media_endpoint,
                    params=params,
                    timeout=config.api_timeout
                )
                response.raise_for_status()
                data = response.json()
                for item in data.get("data", []):
                    if item.get("hash") not in seen_hashes:
                        seen_hashes.add(item.get("hash"))
                        all_items.append(item)
            # Sort by updated_at desc and limit
            all_items.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
            return {"data": all_items[:limit]}

        # Single status or no status filter
        if pipeline_statuses and len(pipeline_statuses) == 1:
            base_params["pipeline_status"] = pipeline_statuses[0]

        response = requests.get(
            config.media_endpoint,
            params=base_params,
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
        # Hash row
        st.markdown(f"<span style='font-family: monospace; font-size: 0.945em; color: #00ffff; background-color: rgba(0,255,255,0.1); padding: 4px 8px; border-radius: 4px; border: 1px solid rgba(0,255,255,0.3);'>{item.get('hash', 'n/a')}</span>", unsafe_allow_html=True)

        # Main row with basic info
        col1, col2, col3, col4, col5 = st.columns([2.5, 1, 1.2, 1, 1.2])

        with col1:
            st.markdown(f"<div style='padding-left: 4px;'><strong>{item.get('media_title', 'unknown')}</strong></div>", unsafe_allow_html=True)
            if item.get('media_type') == 'tv_show' and item.get('season') and item.get('episode'):
                st.markdown(f"<div style='padding-left: 4px; font-size: 0.875em; color: #808495;'>s{item.get('season')}e{item.get('episode')}</div>", unsafe_allow_html=True)

        with col2:
            media_type = item.get('media_type', 'unknown')
            st.markdown(f"<div style='line-height: 1.2;'><span style='font-size: 0.875em; color: #808495;'>media_type</span><br><strong>{media_type}</strong></div>", unsafe_allow_html=True)

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
            st.markdown(f"<div style='line-height: 1.2;'><span style='font-size: 0.875em; color: #808495;'>pipeline_status</span><br><span style='color: {status_color}; font-weight: bold;'>{pipeline_status}</span></div>", unsafe_allow_html=True)

        with col4:
            error_status = item.get('error_status', False)
            error_color = '#dc3545' if error_status else '#28a745'
            error_text = 'true' if error_status else 'false'
            st.markdown(f"<div style='line-height: 1.2;'><span style='font-size: 0.875em; color: #808495;'>error_status</span><br><span style='color: {error_color}; font-weight: bold;'>{error_text}</span></div>", unsafe_allow_html=True)

        with col5:
            rejection_status = item.get('rejection_status', 'unfiltered')
            rejection_color = {
                'unfiltered': '#6c757d',
                'accepted': '#28a745',
                'rejected': '#dc3545',
                'override': '#ffc107'
            }.get(rejection_status, '#6c757d')
            st.markdown(f"<div style='line-height: 1.2;'><span style='font-size: 0.875em; color: #808495;'>rejection_status</span><br><span style='color: {rejection_color}; font-weight: bold;'>{rejection_status}</span></div>", unsafe_allow_html=True)

        # Buttons row
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        btn1, btn2, btn3, btn4, btn5 = st.columns([1, 1, 1, 1, 1])
        with btn1:
            if st.button("edit", key=f"edit_{idx}", use_container_width=True):
                st.session_state.selected_item = item
                st.rerun()
        with btn2:
            if st.button("re-ingest", key=f"reingest_{idx}", use_container_width=True):
                updates = {
                    'pipeline_status': 'ingested',
                    'error_status': False,
                    'rejection_status': 'unfiltered'
                }
                success, result = make_patch_call(config, item.get('hash'), updates)
                if success:
                    st.rerun()
                else:
                    st.error(f"failed to re-ingest: {result}")
        with btn3:
            if st.button("promote", key=f"promote_{idx}", use_container_width=True):
                success, result = make_promote_call(config, item.get('hash'))
                if success:
                    st.rerun()
                else:
                    st.error(f"failed to promote: {result}")
        with btn4:
            if st.button("finish", key=f"finish_{idx}", use_container_width=True):
                success, result = make_finish_call(config, item.get('hash'))
                if success:
                    st.rerun()
                else:
                    st.error(f"failed to finish: {result}")
        with btn5:
            if st.button("delete", key=f"delete_{idx}", use_container_width=True, type="primary"):
                success, result = make_soft_delete_call(config, item.get('hash'))
                if success:
                    st.rerun()
                else:
                    st.error(f"failed to delete: {result}")

        st.divider()


def display_focused_item(item: Dict, config: Config):
    """Display focused item with pipeline editing controls"""
    # Style for back button
    st.markdown("""
    <style>
    .st-key-back_btn button {
        background-color: #00bcd4 !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
    }
    .st-key-back_btn button:hover {
        background-color: #00acc1 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

    if st.button("← Back to Results", use_container_width=False, key="back_btn"):
        st.session_state.selected_item = None
        st.rerun()

    st.subheader(f"{item.get('media_title', 'Unknown')}")
    st.markdown(f"<span style='font-family: monospace; font-size: 1.1em; color: #00ffff; background-color: rgba(0,255,255,0.1); padding: 4px 8px; border-radius: 4px; border: 1px solid rgba(0,255,255,0.3);'>{item.get('hash')}</span>", unsafe_allow_html=True)
    st.markdown(f"<span style='font-family: monospace; font-size: 0.9em; color: #ff9800; background-color: rgba(255,152,0,0.1); padding: 4px 8px; border-radius: 4px; border: 1px solid rgba(255,152,0,0.3);'>{item.get('original_title', 'Unknown')}</span>", unsafe_allow_html=True)

    res_col1, res_col2, res_spacer = st.columns([1, 5, 0.5])
    with res_col1:
        st.caption("resolution")
        st.write(f"**{item.get('resolution', 'Unknown')}**")
    with res_col2:
        st.caption("video_codec")
        st.write(f"**{item.get('video_codec') or 'None'}**")

    # Current values
    current_pipeline = item.get('pipeline_status', 'ingested')
    current_error = item.get('error_status', False)
    current_rejection = item.get('rejection_status', 'unfiltered')

    # Pipeline status row
    pipeline_color = {
        'ingested': '#28a745',
        'processed': '#007bff',
        'failed': '#dc3545',
        'pending': '#ffc107',
        'complete': '#28a745',
        'downloading': '#17a2b8',
        'transferred': '#6f42c1',
        'rejected': '#dc3545',
        'paused': '#ffc107'
    }.get(current_pipeline, '#6c757d')
    st.caption("pipeline_status")
    st.markdown(f'<span style="color: {pipeline_color}; font-weight: bold;">{current_pipeline}</span>', unsafe_allow_html=True)

    error_condition = item.get('error_condition')
    rejection_reason = item.get('rejection_reason')

    # Error row
    err_col1, err_col2, err_spacer = st.columns([1, 5, 0.5])
    with err_col1:
        error_color = '#dc3545' if current_error else '#28a745'
        error_text = 'True' if current_error else 'False'
        st.caption("error_status")
        st.markdown(f'<span style="color: {error_color}; font-weight: bold;">{error_text}</span>', unsafe_allow_html=True)
    with err_col2:
        st.caption("error_condition")
        if error_condition:
            st.markdown(f"<span style='color: #ffc107; font-weight: bold;'>{error_condition}</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='color: #6c757d;'>None</span>", unsafe_allow_html=True)

    # Rejection row
    rej_col1, rej_col2, rej_spacer = st.columns([1, 5, 0.5])
    with rej_col1:
        rejection_color = {
            'unfiltered': '#6c757d',
            'accepted': '#28a745',
            'rejected': '#dc3545',
            'override': '#ffc107'
        }.get(current_rejection, '#6c757d')
        st.caption("rejection_status")
        st.markdown(f'<span style="color: {rejection_color}; font-weight: bold;">{current_rejection}</span>', unsafe_allow_html=True)
    with rej_col2:
        st.caption("rejection_reason")
        if rejection_reason:
            st.markdown(f"<span style='color: #ffc107; font-weight: bold;'>{rejection_reason}</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='color: #6c757d;'>None</span>", unsafe_allow_html=True)

    st.divider()
    st.write("**update values:**")

    col1, col2, col3 = st.columns(3)

    with col1:
        pipeline_options = ['ingested', 'paused', 'parsed', 'rejected', 'file_accepted',
                          'metadata_collected', 'media_accepted', 'downloading',
                          'downloaded', 'transferred', 'complete']
        if current_pipeline not in pipeline_options:
            pipeline_options.append(current_pipeline)

        new_pipeline = st.selectbox(
            "pipeline_status",
            options=pipeline_options,
            index=pipeline_options.index(current_pipeline),
            key="pipeline_select"
        )

    with col2:
        new_error = st.selectbox(
            "error_status",
            options=[False, True],
            index=1 if current_error else 0,
            key="error_select"
        )

    with col3:
        rejection_options = ['unfiltered', 'accepted', 'rejected', 'override']
        if current_rejection not in rejection_options:
            rejection_options.append(current_rejection)

        new_rejection = st.selectbox(
            "rejection_status",
            options=rejection_options,
            index=rejection_options.index(current_rejection),
            key="rejection_select"
        )

    st.divider()

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
    .st-key-promote_detail_btn button {
        background-color: #6f42c1 !important;
        color: white !important;
        border: none !important;
    }
    .st-key-promote_detail_btn button:hover {
        background-color: #5a32a3 !important;
        color: white !important;
    }
    .st-key-finish_detail_btn button {
        background-color: #007bff !important;
        color: white !important;
        border: none !important;
    }
    .st-key-finish_detail_btn button:hover {
        background-color: #0056b3 !important;
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

    button_col1, button_col2, button_col3, button_col4 = st.columns(4)

    with button_col1:
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

    with button_col2:
        if st.button("Promote", use_container_width=True, key="promote_detail_btn"):
            with st.spinner("Promoting..."):
                success, result = make_promote_call(config, item.get('hash'))
            if success:
                st.success("Media entry promoted successfully!")
                st.session_state.selected_item = None
                st.rerun()
            else:
                st.error(f"Failed to promote: {result}")

    with button_col3:
        if st.button("Finish", use_container_width=True, key="finish_detail_btn"):
            with st.spinner("Finishing..."):
                success, result = make_finish_call(config, item.get('hash'))
            if success:
                st.success("Media entry finished successfully!")
                st.session_state.selected_item = None
                st.rerun()
            else:
                st.error(f"Failed to finish: {result}")

    with button_col4:
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
    if 'filter_in_transmission' not in st.session_state:
        st.session_state.filter_in_transmission = False
    if 'filter_pipeline_status' not in st.session_state:
        st.session_state.filter_pipeline_status = "All"
    if 'page_offset' not in st.session_state:
        st.session_state.page_offset = 0

    # If item is selected, show edit view
    if st.session_state.selected_item:
        display_focused_item(st.session_state.selected_item, config)
        return

    # Search and filters
    error_count = fetch_error_count(config)

    search_col1, search_col2, search_col3, search_col4 = st.columns([3, 1, 1, 0.3])

    with search_col1:
        search_term = st.text_input("Search", placeholder="Enter hash or title...", key="search_input", label_visibility="collapsed")

    with search_col2:
        search_type = st.selectbox("Search By", ["hash", "title"], key="search_type_select", label_visibility="collapsed")

    with search_col3:
        popover_label = f"⚠️ errors ({error_count})" if error_count > 0 else "filters"
        with st.popover(popover_label, use_container_width=True):
            if error_count > 0:
                st.markdown(f'<span style="color: #dc3545; font-weight: bold;">⚠️ {error_count} items with errors</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span style="color: #28a745; font-weight: bold;">✓ No errors</span>', unsafe_allow_html=True)

            st.divider()

            filter_errors = st.checkbox(
                "Show errors only",
                value=st.session_state.filter_errors,
                key="filter_errors_checkbox"
            )
            if filter_errors != st.session_state.filter_errors:
                st.session_state.filter_errors = filter_errors
                st.session_state.page_offset = 0
                st.rerun()

            filter_in_transmission = st.checkbox(
                "In-transmission",
                value=st.session_state.filter_in_transmission,
                key="filter_in_transmission_checkbox",
                help="Show items with pipeline_status: downloading, downloaded, transferred",
                disabled=st.session_state.filter_pipeline_status != "All"
            )
            if filter_in_transmission != st.session_state.filter_in_transmission:
                st.session_state.filter_in_transmission = filter_in_transmission
                st.session_state.page_offset = 0
                st.rerun()

            pipeline_status_options = [
                "All",
                "ingested",
                "paused",
                "parsed",
                "rejected",
                "file_accepted",
                "metadata_collected",
                "media_accepted",
                "downloading",
                "downloaded",
                "transferred",
                "complete"
            ]
            filter_pipeline_status = st.selectbox(
                "Pipeline Status",
                options=pipeline_status_options,
                index=pipeline_status_options.index(st.session_state.filter_pipeline_status),
                key="filter_pipeline_status_select"
            )
            if filter_pipeline_status != st.session_state.filter_pipeline_status:
                st.session_state.filter_pipeline_status = filter_pipeline_status
                st.session_state.page_offset = 0
                # Clear in-transmission if a specific status is selected
                if filter_pipeline_status != "All":
                    st.session_state.filter_in_transmission = False
                st.rerun()

    with search_col4:
        if st.button("↻", key="refresh_btn", use_container_width=True):
            st.rerun()

    # Mobile-only enter button
    st.markdown("""
    <style>
    .st-key-mobile_enter_btn {
        display: none;
    }
    @media (max-width: 768px) {
        .st-key-mobile_enter_btn {
            display: block;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    if st.button("Enter", key="mobile_enter_btn", use_container_width=True):
        st.rerun()

    # Build API call display
    page_size = 20
    params = {
        "limit": page_size,
        "offset": st.session_state.page_offset,
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

    pipeline_statuses = None
    if st.session_state.filter_pipeline_status != "All":
        # Specific pipeline status selected
        pipeline_statuses = [st.session_state.filter_pipeline_status]
    elif st.session_state.filter_in_transmission:
        # In-transmission shortcut (only when no specific status selected)
        pipeline_statuses = ["downloading", "downloaded", "transferred"]

    param_string = "&".join([f"{k}={v}" for k, v in params.items()])
    if pipeline_statuses:
        # Show that we're making multiple calls
        api_urls = [f"{config.media_endpoint}?{param_string}&pipeline_status={s}" for s in pipeline_statuses]
        st.code("\n".join(api_urls), language="bash")
    else:
        api_url = f"{config.media_endpoint}?{param_string}"
        st.code(api_url, language="bash")

    # Fetch data
    error_filter = True if st.session_state.filter_errors else None
    data = fetch_media_data(config, limit=page_size, offset=st.session_state.page_offset, search_term=search_term if search_term else None, search_type=search_type, error_status=error_filter, pipeline_statuses=pipeline_statuses)

    if not data:
        return

    items = data.get("data", [])

    if not items:
        st.info("0 media items found")
        return

    # Display count
    filter_parts = []
    if st.session_state.filter_errors:
        filter_parts.append("with errors")
    if st.session_state.filter_pipeline_status != "All":
        filter_parts.append(f"status: {st.session_state.filter_pipeline_status}")
    elif st.session_state.filter_in_transmission:
        filter_parts.append("in-transmission")
    filter_desc = f" ({', '.join(filter_parts)})" if filter_parts else ""

    start_idx = st.session_state.page_offset + 1
    end_idx = st.session_state.page_offset + len(items)
    range_str = f"{start_idx}-{end_idx}"

    if search_term:
        st.info(f"showing {range_str}{filter_desc} matching '{search_term}'")
    else:
        st.info(f"showing {range_str}{filter_desc}")

    # Display each media item
    for idx, item in enumerate(items):
        display_media_item(item, idx, config)

    # Pagination buttons
    st.divider()
    pag_col1, pag_col2, pag_col3 = st.columns([1, 2, 1])

    with pag_col1:
        if st.session_state.page_offset > 0:
            if st.button("← Previous", use_container_width=True):
                st.session_state.page_offset = max(0, st.session_state.page_offset - page_size)
                st.rerun()

    with pag_col2:
        current_page = (st.session_state.page_offset // page_size) + 1
        st.markdown(f"<div style='text-align: center; padding-top: 5px;'>Page {current_page}</div>", unsafe_allow_html=True)

    with pag_col3:
        # Show next button if we got a full page (might be more)
        if len(items) == page_size:
            if st.button("Next →", use_container_width=True):
                st.session_state.page_offset += page_size
                st.rerun()


if __name__ == "__main__":
    main()
