import streamlit as st
import requests
import pandas as pd
from config import Config
from typing import Dict, List, Optional
import time

st.set_page_config(page_title="prediction-anomalies", layout="wide")

# Custom CSS for button styling
st.markdown("""
<style>
/* Blue buttons for would_watch when active */
div[data-testid="stButton"] > button[kind="primary"] {
    background-color: #1f77b4 !important;
    color: white !important;
    border-color: #1f77b4 !important;
}

/* Red buttons for would_not_watch when active */
div[data-testid="stButton"] > button[kind="tertiary"] {
    background-color: #d62728 !important;
    color: white !important;
    border-color: #d62728 !important;
}

/* Transparent buttons when inactive */
div[data-testid="stButton"] > button:not([kind]) {
    background-color: transparent !important;
    color: #262730 !important;
    border: 1px solid #d0d0d0 !important;
}

/* Custom progress bar colors */
/* RT Score - Crimson */
div[data-testid="stColumn"]:nth-child(2) .stProgress > div > div > div > div {
    background-color: #DC143C !important;
}

/* IMDB Votes - IMDB Yellow */
div[data-testid="stColumn"]:nth-child(3) .stProgress > div > div > div > div {
    background-color: #F5C518 !important;
}

/* Prediction probability - Green */
div[data-testid="stColumn"]:nth-child(6) .stProgress > div > div > div > div {
    background-color: #28a745 !important;
}
</style>
""", unsafe_allow_html=True)

def fetch_prediction_data(_config: Config, cm_value_filter: str = None, offset: int = 0, limit: int = 20, sort_order: str = "desc") -> Optional[Dict]:
    """Fetch prediction results with pagination, filtered by cm_value if specified"""
    try:
        # For filtered results, we need to fetch more and filter client-side
        # This is not ideal but works with current API limitations
        if cm_value_filter and cm_value_filter != "all":
            # Fetch larger batch to ensure we get enough filtered results
            fetch_limit = limit * 5  # Fetch 5x to ensure we get enough filtered results
            params = {
                "limit": fetch_limit,
                "offset": offset,
                "sort_by": "probability",
                "sort_order": sort_order
            }
            
            response = requests.get(
                f"{_config.base_url}prediction/",
                params=params,
                timeout=_config.api_timeout
            )
            response.raise_for_status()
            data = response.json()
            
            # Store debug info in session state
            st.session_state.debug_api_call = f"GET {response.url}"
            st.session_state.debug_results = data.get("data", [])
            
            # Filter by cm_value
            all_predictions = data.get("data", [])
            filtered_predictions = [item for item in all_predictions if item.get("cm_value") == cm_value_filter]
            
            # Return filtered results with custom pagination info
            return {
                "data": filtered_predictions[:limit],
                "pagination": {
                    "has_more": len(filtered_predictions) > limit or data.get("pagination", {}).get("has_more", False),
                    "total_fetched": len(filtered_predictions),
                    "offset": offset
                }
            }
        else:
            # For unfiltered results, use API pagination directly
            params = {
                "limit": limit,
                "offset": offset,
                "sort_by": "probability",
                "sort_order": sort_order
            }
            
            response = requests.get(
                f"{_config.base_url}prediction/",
                params=params,
                timeout=_config.api_timeout
            )
            response.raise_for_status()
            data = response.json()
            
            # Store debug info in session state
            st.session_state.debug_api_call = f"GET {response.url}"
            st.session_state.debug_results = data.get("data", [])
            
            return data
            
    except Exception as e:
        st.error(f"Failed to fetch prediction data: {str(e)}")
        return None

def fetch_training_data_for_predictions(_config: Config, imdb_ids: List[str]) -> Optional[Dict]:
    """Fetch training data for specific IMDB IDs without caching"""
    try:
        if not imdb_ids:
            return {"data": []}
        
        # Join IMDB IDs with commas for the API call
        imdb_ids_param = ",".join(imdb_ids)
        
        params = {
            "imdb_id": imdb_ids_param,
            "media_type": "movie",
            "limit": len(imdb_ids)  # Set limit to number of IDs we're requesting
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

def find_training_data_by_imdb(training_data: Dict, imdb_id: str) -> Optional[Dict]:
    """Find training data for a specific IMDB ID from fetched data"""
    if not training_data or "data" not in training_data:
        return None
    
    for item in training_data["data"]:
        if item.get("imdb_id") == imdb_id:
            return item
    
    return None

def update_label(_config: Config, imdb_id: str, new_label: str, current_label: str, current_human_labeled: bool) -> bool:
    """Update the label for a training item"""
    try:
        # If new label matches current label, use reviewed endpoint
        if new_label == current_label:
            return mark_as_reviewed(_config, imdb_id)
        
        # If labels differ, use label endpoint with human_labeled=true
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
    
    st.title("prediction-anomalies")
    
    # Initialize session state
    if 'predictions' not in st.session_state:
        st.session_state.predictions = []
    if 'offset' not in st.session_state:
        st.session_state.offset = 0
    if 'has_more' not in st.session_state:
        st.session_state.has_more = True
    if 'current_filter' not in st.session_state:
        st.session_state.current_filter = "all"
    if 'sort_ascending' not in st.session_state:
        st.session_state.sort_ascending = False
    
    # Filter selection at the top
    col1, col2 = st.columns([1, 3])
    
    with col1:
        cm_value_filter = st.selectbox(
            "Filter by Prediction Type:",
            options=["all", "fp", "fn", "tp", "tn"],
            format_func=lambda x: {
                "all": "All Predictions",
                "fp": "False Positives",
                "fn": "False Negatives", 
                "tp": "True Positives",
                "tn": "True Negatives"
            }.get(x, x),
            index=0
        )
        
        # Sort control - Dropdown
        sort_selection = st.selectbox(
            "Sort by Confidence:",
            options=["pred-proba-desc", "pred-proba-asc"],
            index=0 if not st.session_state.sort_ascending else 1,
            format_func=lambda x: "High → Low (desc)" if x == "pred-proba-desc" else "Low → High (asc)",
            key="sort_dropdown"
        )
        
        # Update sort order based on selection
        if sort_selection == "pred-proba-asc" and not st.session_state.sort_ascending:
            st.session_state.sort_ascending = True
            st.session_state.data_loaded = False  # Force reload with new sort
            st.rerun()
        elif sort_selection == "pred-proba-desc" and st.session_state.sort_ascending:
            st.session_state.sort_ascending = False
            st.session_state.data_loaded = False  # Force reload with new sort
            st.rerun()
        
        # Debug: Show API call and results
        if 'debug_api_call' in st.session_state and 'debug_results' in st.session_state:
            with st.expander("🔍 Debug: API Call & Results", expanded=True):
                st.code(st.session_state.debug_api_call, language="bash")
                st.write("**Top 10 Results:**")
                for i, result in enumerate(st.session_state.debug_results[:10], 1):
                    prob = result.get('probability')
                    if prob is not None:
                        try:
                            prob_str = f"{float(prob):.4f}"
                        except (ValueError, TypeError):
                            prob_str = str(prob)
                    else:
                        prob_str = "N/A"
                    st.write(f"{i}. IMDB: {result.get('imdb_id', 'N/A')} | Prob: {prob_str} | CM: {result.get('cm_value', 'N/A')}")
    
    with col2:
        st.write("**Filter Description:**")
        if cm_value_filter == "fp":
            st.info("🔴 **False Positives**: Model predicted 'would_watch' but actual label is 'would_not_watch'")
        elif cm_value_filter == "fn":
            st.info("🟡 **False Negatives**: Model predicted 'would_not_watch' but actual label is 'would_watch'")
        elif cm_value_filter == "tp":
            st.info("🟢 **True Positives**: Model correctly predicted 'would_watch'")
        elif cm_value_filter == "tn":
            st.info("⚪ **True Negatives**: Model correctly predicted 'would_not_watch'")
        else:
            st.info("📊 **All Predictions**: Showing all prediction results")
    
    # Track if we need to reload data
    need_reload = False
    
    # Check if filter changed
    if cm_value_filter != st.session_state.current_filter:
        st.session_state.current_filter = cm_value_filter
        need_reload = True
    
    # Check if this is first load or we need to reload
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    
    st.divider()
    
    # Always fetch fresh data on page load or when parameters change
    if not st.session_state.data_loaded or need_reload:
        with st.spinner("Loading predictions..."):
            sort_order = "asc" if st.session_state.sort_ascending else "desc"
            result = fetch_prediction_data(
                config, 
                cm_value_filter=cm_value_filter, 
                offset=0, 
                limit=20,
                sort_order=sort_order
            )
            
            if result is None:
                return
            
            st.session_state.predictions = result.get("data", [])
            st.session_state.has_more = result.get("pagination", {}).get("has_more", False)
            st.session_state.offset = 20
            st.session_state.data_loaded = True
    
    predictions = st.session_state.predictions
    
    if not predictions:
        st.success("✅ No prediction anomalies found")
        return
    
    st.subheader(f"Showing {len(predictions)} predictions")
    
    # Step 2: Extract IMDB IDs and fetch matching training data
    imdb_ids = [pred.get("imdb_id") for pred in predictions if pred.get("imdb_id")]
    training_data = fetch_training_data_for_predictions(config, imdb_ids)
    
    if not training_data:
        st.error("Failed to fetch training data")
        return
    
    for idx, prediction in enumerate(predictions):
        imdb_id = prediction.get("imdb_id")
        
        # Find training data for this prediction
        training_item = find_training_data_by_imdb(training_data, imdb_id)
        
        if not training_item:
            st.warning(f"No training data found for {imdb_id}")
            continue
            
        with st.container():
            # Main row with basic info and buttons
            col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([2.5, 1, 1, 0.8, 0.6, 1, 1.5, 1.2, 1.2])
            
            with col1:
                st.write(f"**{training_item.get('media_title', 'Unknown')}**")
            
            with col2:
                rt_score = training_item.get('rt_score')
                if rt_score is None:
                    st.progress(0.0)
                    st.caption("RT: NULL")
                else:
                    st.progress(rt_score / 100.0)
                    st.caption(f"RT: {rt_score}%")
            
            with col3:
                imdb_votes = training_item.get('imdb_votes')
                if imdb_votes is None:
                    st.progress(0.0)
                    st.caption("IMDB: NULL")
                else:
                    # Show IMDB votes as progress bar with 100k cap
                    if isinstance(imdb_votes, int):
                        # Cap at 100k for progress bar
                        progress_value = min(imdb_votes / 100000.0, 1.0)
                        st.progress(progress_value)
                        # Format display
                        if imdb_votes >= 1000000:
                            votes_display = f"{imdb_votes/1000000:.1f}M"
                        elif imdb_votes >= 1000:
                            votes_display = f"{imdb_votes/1000:.0f}K"
                        else:
                            votes_display = str(imdb_votes)
                        st.caption(f"IMDB: {votes_display}")
                    else:
                        st.progress(0.0)
                        st.caption(f"IMDB: {imdb_votes}")
            
            with col4:
                release_year = training_item.get('release_year')
                if release_year is None:
                    st.progress(0.0)
                    st.caption("Year: NULL")
                else:
                    # Create 1D scatter plot with year range 1950-current year
                    import datetime
                    min_year = 1950
                    max_year = datetime.datetime.now().year
                    
                    if isinstance(release_year, int):
                        # Clamp years before 1950 to 1950
                        clamped_year = max(release_year, min_year)
                        progress_value = (clamped_year - min_year) / (max_year - min_year)
                        st.progress(progress_value)
                        st.caption(f"Year: {release_year}")
                    else:
                        st.progress(0.0)
                        st.caption(f"Year: {release_year}")
            
            with col5:
                def country_code_to_flag(country_code):
                    """Convert 2-letter country code to flag emoji"""
                    if not country_code or len(country_code) != 2:
                        return country_code
                    # Convert to uppercase and then to flag emoji
                    # Each letter gets converted to its regional indicator symbol
                    return ''.join(chr(ord(c) + 0x1F1A5) for c in country_code.upper())
                
                origin_country = training_item.get('origin_country')
                if origin_country and isinstance(origin_country, list):
                    # Show all flags for multiple countries
                    flags = [country_code_to_flag(country) for country in origin_country]
                    country_display = ''.join(flags)
                elif origin_country:
                    country_display = country_code_to_flag(str(origin_country))
                else:
                    country_display = 'NULL'
                st.write(f"Country: {country_display}")
            
            with col6:
                # Show prediction probability as progress bar
                probability = float(prediction.get('probability', 0))
                st.progress(probability)
                st.caption(f"Pred: {probability:.2f}")
            
            with col7:
                def genre_to_emoji(genre):
                    """Convert genre string to emoji"""
                    genre_map = {
                        "Action": "💥",
                        "Action & Adventure": "💥⛰️",
                        "Adventure": "⛰️",
                        "Animation": "✏️",
                        "Comedy": "🤣",
                        "Crime": "👮‍♂️",
                        "Documentary": "📚",
                        "Drama": "💔",
                        "Family": "🏠",
                        "Fantasy": "🦄",
                        "History": "🏛️",
                        "Horror": "😱",
                        "Kids": "👶",
                        "Music": "🎵",
                        "Mystery": "🔍",
                        "News": "📰",
                        "Reality": "🎪",
                        "Romance": "💕",
                        "Science Fiction": "🚀",
                        "Sci-Fi & Fantasy": "🚀🦄",
                        "Talk": "💬",
                        "Thriller": "⚡",
                        "TV Movie": "📺",
                        "War": "⚔️",
                        "Western": "🤠"
                    }
                    return genre_map.get(genre, "🎬")  # Default movie emoji for unknown genres
                
                genres = training_item.get('genre', [])
                if genres and isinstance(genres, list):
                    # Show all genre emojis
                    genre_emojis = [genre_to_emoji(genre) for genre in genres]
                    genre_display = "".join(genre_emojis)
                else:
                    genre_display = "NULL"
                
                # Add CM value indicator
                cm_value = prediction.get('cm_value', '')
                cm_emoji = {
                    'tp': '🟢',
                    'tn': '⚪', 
                    'fp': '🔴',
                    'fn': '🟡'
                }.get(cm_value, '❓')
                
                st.write(f"{cm_emoji} {genre_display}")
            
            current_label = training_item.get('label', '')
            current_human_labeled = training_item.get('human_labeled', False)
            
            with col8:
                # Would Watch button - blue when active, transparent when inactive
                button_type = "primary" if current_label == "would_watch" else None
                button_kwargs = {"use_container_width": True}
                if button_type:
                    button_kwargs["type"] = button_type
                
                if st.button("would_watch", key=f"would_watch_{imdb_id}", **button_kwargs):
                    if update_label(config, imdb_id, "would_watch", current_label, current_human_labeled):
                        # Remove the updated item from predictions
                        st.session_state.predictions = [p for p in st.session_state.predictions if p.get("imdb_id") != imdb_id]
                        st.rerun()
            
            with col9:
                # Would Not Watch button - red when active, transparent when inactive
                button_type = "tertiary" if current_label == "would_not_watch" else None
                button_kwargs = {"use_container_width": True}
                if button_type:
                    button_kwargs["type"] = button_type
                
                if st.button("would_not", key=f"would_not_watch_{imdb_id}", **button_kwargs):
                    if update_label(config, imdb_id, "would_not_watch", current_label, current_human_labeled):
                        # Remove the updated item from predictions
                        st.session_state.predictions = [p for p in st.session_state.predictions if p.get("imdb_id") != imdb_id]
                        st.rerun()
            
            # Expandable details section
            with st.expander(f"📋 Details for {training_item.get('media_title', 'Unknown')}", expanded=False):
                detail_col1, detail_col2, detail_col3 = st.columns(3)
                
                with detail_col1:
                    st.write("**Basic Info:**")
                    st.write(f"• **IMDB ID:** {training_item.get('imdb_id', 'NULL')}")
                    st.write(f"• **TMDB ID:** {training_item.get('tmdb_id', 'NULL')}")
                    st.write(f"• **Release Year:** {training_item.get('release_year', 'NULL')}")
                    st.write(f"• **Runtime:** {training_item.get('runtime', 'NULL')} min")
                    st.write(f"• **Original Language:** {training_item.get('original_language', 'NULL')}")
                    st.write(f"• **Origin Country:** {training_item.get('origin_country', 'NULL')}")
                    
                    st.write("**Status:**")
                    st.write(f"• **Current Label:** {training_item.get('label', 'NULL')}")
                    st.write(f"• **Human Labeled:** {training_item.get('human_labeled', 'NULL')}")
                    st.write(f"• **Reviewed:** {training_item.get('reviewed', 'NULL')}")
                    st.write(f"• **Anomalous:** {training_item.get('anomalous', 'NULL')}")
                
                with detail_col2:
                    st.write("**Ratings & Scores:**")
                    st.write(f"• **RT Score:** {training_item.get('rt_score', 'NULL')}")
                    st.write(f"• **IMDB Rating:** {training_item.get('imdb_rating', 'NULL')}")
                    st.write(f"• **IMDB Votes:** {training_item.get('imdb_votes', 'NULL')}")
                    st.write(f"• **TMDB Rating:** {training_item.get('tmdb_rating', 'NULL')}")
                    st.write(f"• **TMDB Votes:** {training_item.get('tmdb_votes', 'NULL')}")
                    st.write(f"• **Metascore:** {training_item.get('metascore', 'NULL')}")
                    
                    st.write("**Financial:**")
                    st.write(f"• **Budget:** ${training_item.get('budget', 'NULL'):,}" if training_item.get('budget') else "• **Budget:** NULL")
                    st.write(f"• **Revenue:** ${training_item.get('revenue', 'NULL'):,}" if training_item.get('revenue') else "• **Revenue:** NULL")
                
                with detail_col3:
                    st.write("**Prediction Details:**")
                    st.write(f"• **Prediction:** {'Would Watch' if prediction.get('prediction') == 1 else 'Would Not Watch'}")
                    st.write(f"• **Probability:** {float(prediction.get('probability', 0)):.4f}")
                    st.write(f"• **CM Value:** {prediction.get('cm_value', 'NULL').upper()}")
                    st.write(f"• **Created:** {prediction.get('created_at', 'NULL')}")
                    
                    # Explanation of CM value
                    cm_value = prediction.get('cm_value', '')
                    if cm_value == 'tp':
                        st.success("🟢 **True Positive**: Model correctly predicted 'would_watch'")
                    elif cm_value == 'tn':
                        st.info("⚪ **True Negative**: Model correctly predicted 'would_not_watch'")
                    elif cm_value == 'fp':
                        st.error("🔴 **False Positive**: Model predicted 'would_watch' but actual is 'would_not_watch'")
                    elif cm_value == 'fn':
                        st.warning("🟡 **False Negative**: Model predicted 'would_not_watch' but actual is 'would_watch'")
                
                st.write("**Additional Info:**")
                st.write(f"• **Genres:** {', '.join(training_item.get('genre', [])) if training_item.get('genre') else 'NULL'}")
                st.write(f"• **Production Status:** {training_item.get('production_status', 'NULL')}")
                st.write(f"• **Tagline:** {training_item.get('tagline', 'NULL')}")
                
                if training_item.get('overview'):
                    st.write("**Overview:**")
                    st.write(training_item.get('overview'))
                
                st.write("**Timestamps:**")
                st.write(f"• **Created:** {training_item.get('created_at', 'NULL')}")
                st.write(f"• **Updated:** {training_item.get('updated_at', 'NULL')}")
            
            st.divider()
    
    # Load More button
    st.write("")  # Add some spacing
    if st.session_state.has_more:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🔄 Load More", type="primary", use_container_width=True, key="load_more_btn"):
                with st.spinner("Loading more predictions..."):
                    sort_order = "asc" if st.session_state.sort_ascending else "desc"
                    result = fetch_prediction_data(
                        config, 
                        cm_value_filter=cm_value_filter, 
                        offset=st.session_state.offset, 
                        limit=20,
                        sort_order=sort_order
                    )
                    
                    if result and result.get("data"):
                        new_predictions = result.get("data", [])
                        st.session_state.predictions.extend(new_predictions)
                        st.session_state.offset += len(new_predictions)
                        st.session_state.has_more = result.get("pagination", {}).get("has_more", False)
                        st.rerun()
    else:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.info("✅ All predictions loaded")

if __name__ == "__main__":
    main()