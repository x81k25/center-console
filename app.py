import streamlit as st
import requests
import pandas as pd
from config import Config
import re
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Rear Diff Training Data Viewer",
    page_icon="🚗",
    layout="wide"
)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_training_data(base_url, limit=25, offset=0, sort_by="updated_at", sort_order="desc"):
    """Fetch training data from the API with caching"""
    params = {
        "limit": limit,
        "offset": offset,
        "sort_by": sort_by,
        "sort_order": sort_order
    }
    
    try:
        response = requests.get(
            f"{base_url}training",
            params=params,
            timeout=st.session_state.config.api_timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Failed to fetch data from API: {str(e)}")
        return None

def validate_imdb_id(imdb_id):
    """Validate IMDB ID format (tt + 7-8 digits)"""
    return bool(re.match(r'^tt\d{7,8}$', imdb_id))

def update_label(imdb_id, new_label):
    """Update label for a specific IMDB ID"""
    if not validate_imdb_id(imdb_id):
        st.warning(f"Invalid IMDB ID format: {imdb_id}")
        return False
    
    endpoint = st.session_state.config.get_label_update_endpoint(imdb_id)
    
    try:
        response = requests.patch(
            endpoint,
            json={"imdb_id": imdb_id, "label": new_label},
            timeout=st.session_state.config.api_timeout
        )
        response.raise_for_status()
        result = response.json()
        
        if result.get("success"):
            return True
        else:
            st.warning(f"Failed to update label: {result.get('message', 'Unknown error')}")
            return False
    except requests.RequestException as e:
        st.warning(f"Failed to update label for {imdb_id}: {str(e)}")
        return False

def get_unique_labels():
    """Get valid label values for the API"""
    # Return the valid API labels (excluding None/null values)
    return ['would_watch', 'would_not_watch']

def initialize_app():
    """Initialize the application and check connectivity"""
    try:
        config = Config()
        st.session_state.config = config
        
        # Test API connectivity
        st.info("Checking API connectivity...")
        health_response = requests.get(config.health_endpoint, timeout=5)
        health_response.raise_for_status()
        
        return True
    except ValueError as e:
        st.error(f"Configuration Error: {str(e)}")
        st.info("Please set the following environment variables:")
        st.code("""
export REAR_DIFF_HOST=192.168.50.2
export REAR_DIFF_PORT=30812
export REAR_DIFF_PATH=/rear-diff/
export API_TIMEOUT=30
        """)
        return False
    except requests.RequestException as e:
        st.error(f"API Connection Error: Could not connect to {config.base_url}")
        st.info(f"Error details: {str(e)}")
        st.info("Please verify the API is running and accessible.")
        return False

def main():
    st.title("🚗 Rear Diff Training Data Viewer")
    
    # Initialize app
    if 'initialized' not in st.session_state:
        st.session_state.initialized = initialize_app()
    
    if not st.session_state.initialized:
        st.stop()
    
    # Pagination controls
    col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
    
    with col1:
        page_size = st.selectbox("Records per page", [25, 50, 100], index=0)
    
    with col2:
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 0
        page_number = st.number_input("Page", min_value=1, value=st.session_state.current_page + 1)
        st.session_state.current_page = page_number - 1
    
    with col3:
        sort_by = st.selectbox("Sort by", ["updated_at", "created_at", "imdb_id", "label"], index=0)
    
    with col4:
        sort_order = st.selectbox("Sort order", ["desc", "asc"], index=0)
    
    # Fetch data
    offset = st.session_state.current_page * page_size
    data_response = fetch_training_data(
        st.session_state.config.base_url,
        limit=page_size,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    if not data_response:
        st.stop()
    
    # Process data
    data = data_response.get("data", [])
    pagination = data_response.get("pagination", {})
    
    if not data:
        st.warning("No data available")
        st.stop()
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Get unique labels for dropdown
    all_labels = get_unique_labels()
    
    # Column visibility controls
    st.subheader("Display Options")
    available_columns = df.columns.tolist()
    selected_columns = st.multiselect(
        "Select columns to display",
        available_columns,
        default=available_columns
    )
    
    # Display data with editable labels
    st.subheader(f"Training Data (Total: {pagination.get('total', 0)} records)")
    
    # Create a container for the data editor
    data_container = st.container()
    
    # Track label updates
    if 'label_updates' not in st.session_state:
        st.session_state.label_updates = {}
    
    # Display each row with editable label dropdown
    for idx, row in df.iterrows():
        cols = st.columns([3, 2, 2, 2, 1])
        
        # Display key fields
        with cols[0]:
            st.text(f"IMDB: {row.get('imdb_id', 'N/A')}")
            st.text(f"Title: {row.get('media_title', 'N/A')}")
        
        with cols[1]:
            st.text(f"Type: {row.get('media_type', 'N/A')}")
            st.text(f"Year: {row.get('release_year', 'N/A')}")
        
        with cols[2]:
            current_label = row.get('label')
            # Handle None/null labels
            if current_label is None:
                current_label = ''
            label_key = f"label_{row['imdb_id']}"
            
            # Create dropdown with unique labels (None/empty shows as first option)
            new_label = st.selectbox(
                "Label",
                options=['(No Label)'] + all_labels,
                index=all_labels.index(current_label) + 1 if current_label in all_labels else 0,
                key=label_key
            )
            
            # Track if label changed (ignore "(No Label)" selection)
            if new_label != current_label and new_label != "(No Label)":
                st.session_state.label_updates[row['imdb_id']] = new_label
        
        with cols[3]:
            st.text(f"Human Labeled: {row.get('human_labeled', False)}")
            if 'updated_at' in row:
                st.text(f"Updated: {row['updated_at'][:10]}")
        
        with cols[4]:
            if row['imdb_id'] in st.session_state.label_updates:
                if st.button("Save", key=f"save_{row['imdb_id']}"):
                    new_label = st.session_state.label_updates[row['imdb_id']]
                    if update_label(row['imdb_id'], new_label):
                        st.success(f"Updated label for {row['imdb_id']}")
                        del st.session_state.label_updates[row['imdb_id']]
                        # Clear cache to refresh data
                        st.cache_data.clear()
                        st.rerun()
        
        st.divider()
    
    # Full data view in expandable section
    with st.expander("View Full Data Table"):
        st.dataframe(df[selected_columns], use_container_width=True, height=400)
    
    # Pagination info and controls
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.session_state.current_page > 0:
            if st.button("← Previous"):
                st.session_state.current_page -= 1
                st.rerun()
    
    with col2:
        total_pages = (pagination.get('total', 0) + page_size - 1) // page_size
        st.markdown(f"<center>Page {st.session_state.current_page + 1} of {total_pages}</center>", unsafe_allow_html=True)
    
    with col3:
        if pagination.get('next'):
            if st.button("Next →"):
                st.session_state.current_page += 1
                st.rerun()

if __name__ == "__main__":
    main()