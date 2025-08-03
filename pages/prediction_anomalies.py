import streamlit as st
import requests
import pandas as pd
from config import Config
from typing import Dict, List, Optional
import time

st.set_page_config(page_title="prediction-anomalies", layout="wide")

# Dynamic CSS for button styling
st.markdown("""
<style>
/* Blue button - would_watch column 8 */
div[data-testid="stHorizontalBlock"] > div:nth-child(8) button[kind="primary"] {
    background-color: #1f77b4 !important;
    color: white !important;
    border-color: #1f77b4 !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(8) button[kind="secondary"] {
    background-color: #2d2d2d !important;
    color: #1f77b4 !important;
    border-color: #1f77b4 !important;
}

/* Red button - would_not column 9 */
div[data-testid="stHorizontalBlock"] > div:nth-child(9) button[kind="primary"] {
    background-color: #d62728 !important;
    color: white !important;
    border-color: #d62728 !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(9) button[kind="secondary"] {
    background-color: #2d2d2d !important;
    color: #d62728 !important;
    border-color: #d62728 !important;
}

/* Green button - anomalous column 10 */
div[data-testid="stHorizontalBlock"] > div:nth-child(10) button[kind="primary"] {
    background-color: #2ca02c !important;
    color: white !important;
    border-color: #2ca02c !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(10) button[kind="secondary"] {
    background-color: #2d2d2d !important;
    color: #2ca02c !important;
    border-color: #2ca02c !important;
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

def fetch_prediction_data(_config: Config, cm_value_filter: str = None, anomalous_filter: str = None, offset: int = 0, limit: int = 20, sort_order: str = "desc") -> Optional[Dict]:
    """Fetch movie data with pagination, filtered by cm_value and anomalous if specified"""
    try:
        # Build API parameters for movies endpoint
        params = {
            "limit": limit,
            "offset": offset,
            "media_type": "movie",
            "sort_by": "probability",
            "sort_order": sort_order
        }
        
        # Add cm_value filter if specified
        if cm_value_filter and cm_value_filter != "all":
            params["cm_value"] = cm_value_filter
        
        # Add anomalous filter if specified
        if anomalous_filter and anomalous_filter != "any":
            params["anomalous"] = anomalous_filter == "true"
        
        response = requests.get(
            f"{_config.base_url}movies/",
            params=params,
            timeout=_config.api_timeout
        )
        response.raise_for_status()
        data = response.json()
        
        # Store debug info in session state
        st.session_state.debug_api_call = response.url
        st.session_state.debug_results = data.get("data", [])
        
        return data
            
    except Exception as e:
        st.error(f"Failed to fetch movie data: {str(e)}")
        return None

def fetch_media_data_for_predictions(_config: Config, imdb_ids: List[str]) -> Optional[Dict]:
    """Fetch media data for specific IMDB IDs without caching"""
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
            _config.media_endpoint,
            params=params,
            timeout=_config.api_timeout
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch media data: {str(e)}")
        return None

def find_media_data_by_imdb(media_data: Dict, imdb_id: str) -> Optional[Dict]:
    """Find media data for a specific IMDB ID from fetched data"""
    if not media_data or "data" not in media_data:
        return None
    
    for item in media_data["data"]:
        if item.get("imdb_id") == imdb_id:
            return item
    
    return None

def update_label(_config: Config, imdb_id: str, new_label: str, current_label: str, current_human_labeled: bool) -> bool:
    """Update the label for a training item"""
    try:
        # If new label matches current label, only set reviewed=True
        if new_label == current_label:
            payload = {
                "imdb_id": imdb_id,
                "reviewed": True
            }
        else:
            # If labels differ, set label, human_labeled=True, and reviewed=True
            payload = {
                "imdb_id": imdb_id,
                "label": new_label,
                "human_labeled": True,
                "reviewed": True
            }
        
        response = requests.patch(
            _config.get_training_update_endpoint(imdb_id),
            json=payload,
            timeout=_config.api_timeout
        )
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Failed to update training item {imdb_id}: {str(e)}")
        return False

def toggle_anomalous(_config: Config, imdb_id: str, current_anomalous: bool) -> bool:
    """Toggle the anomalous status for a training item"""
    try:
        payload = {
            "imdb_id": imdb_id,
            "anomalous": not current_anomalous
        }
        
        response = requests.patch(
            _config.get_training_update_endpoint(imdb_id),
            json=payload,
            timeout=_config.api_timeout
        )
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Failed to toggle anomalous for {imdb_id}: {str(e)}")
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
    if 'current_limit' not in st.session_state:
        st.session_state.current_limit = 20
    if 'current_filter' not in st.session_state:
        st.session_state.current_filter = "all"
    if 'sort_ascending' not in st.session_state:
        st.session_state.sort_ascending = False
    if 'current_anomalous_filter' not in st.session_state:
        st.session_state.current_anomalous_filter = "any"
    
    # Filter selection at the top
    col1, col2 = st.columns([1, 3])
    
    with col1:
        cm_value_filter = st.selectbox(
            "Filter by Confusion Matrix Value:",
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
            st.rerun()
        elif sort_selection == "pred-proba-desc" and st.session_state.sort_ascending:
            st.session_state.sort_ascending = False
            st.rerun()
        
        # Anomalous filter dropdown
        anomalous_filter = st.selectbox(
            "Anomalous:",
            options=["any", "true", "false"],
            format_func=lambda x: {
                "any": "Any",
                "true": "True",
                "false": "False"
            }.get(x, x),
            index=0,
            key="anomalous_dropdown"
        )
    
    with col2:
        pass
    
    # Debug: Show API call (full width) - always display current parameters
    sort_order = "asc" if st.session_state.sort_ascending else "desc"
    debug_params = {
        "limit": st.session_state.current_limit,
        "offset": 0,
        "sort_by": "probability",
        "sort_order": sort_order
    }
    if cm_value_filter and cm_value_filter != "all":
        debug_params["cm_value"] = cm_value_filter
    if anomalous_filter and anomalous_filter != "any":
        debug_params["anomalous"] = anomalous_filter
    
    # Construct URL string for display
    base_url = f"{config.base_url}movies/"
    param_string = "&".join([f"{k}={v}" for k, v in debug_params.items()])
    current_api_url = f"{base_url}?{param_string}"
    
    st.code(current_api_url, language="bash")
    
    # Update filter states
    st.session_state.current_filter = cm_value_filter
    st.session_state.current_anomalous_filter = anomalous_filter
    
    st.divider()
    
    # Check if filters have changed - if so, reset data and limit
    filter_changed = (
        st.session_state.current_filter != cm_value_filter or 
        st.session_state.current_anomalous_filter != anomalous_filter
    )
    
    if filter_changed:
        st.session_state.current_limit = 20
    
    # Always fetch data with current limit
    with st.spinner("Loading movies..."):
        sort_order = "asc" if st.session_state.sort_ascending else "desc"
        result = fetch_prediction_data(
            config, 
            cm_value_filter=cm_value_filter,
            anomalous_filter=anomalous_filter,
            offset=0, 
            limit=st.session_state.current_limit,
            sort_order=sort_order
        )
        
        if result is None:
            return
        
        st.session_state.predictions = result.get("data", [])
    
    predictions = st.session_state.predictions
    
    if not predictions:
        st.success("✅ No prediction anomalies found")
        return
    
    st.subheader(f"Showing {len(predictions)} movies")
    
    for idx, movie_data in enumerate(predictions):
        imdb_id = movie_data.get("imdb_id")
        
        # The movie data already contains all training and prediction information
        training_item = movie_data
            
        with st.container():
            # Main row with basic info and buttons - added col10 for anomalous button
            col1, col2, col3, col4, col5, col6, col7, col8, col9, col10 = st.columns([2.2, 1, 1, 0.8, 0.6, 1, 1.3, 1.1, 1.1, 1.1])
            
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
                probability = float(movie_data.get('probability', 0))
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
                cm_value = movie_data.get('cm_value', '')
                cm_emoji = {
                    'tp': '🟢',
                    'tn': '⚪', 
                    'fp': '🔴',
                    'fn': '🟡'
                }.get(cm_value, '❓')
                
                st.write(f"{cm_emoji} {genre_display}")
            
            current_label = training_item.get('label', '')
            current_human_labeled = training_item.get('human_labeled', False)
            current_anomalous = training_item.get('anomalous', False)
            
            with col8:
                # Would Watch button - dynamic styling based on state
                btn_type = "primary" if current_label == "would_watch" else "secondary"
                if st.button("would_watch", key=f"would_watch_{imdb_id}", type=btn_type, use_container_width=True):
                    if update_label(config, imdb_id, "would_watch", current_label, current_human_labeled):
                        # Refresh data to show updated values
                        st.rerun()
            
            with col9:
                # Would Not Watch button - dynamic styling based on state
                btn_type = "primary" if current_label == "would_not_watch" else "secondary"
                if st.button("would_not", key=f"would_not_watch_{imdb_id}", type=btn_type, use_container_width=True):
                    if update_label(config, imdb_id, "would_not_watch", current_label, current_human_labeled):
                        # Refresh data to show updated values  
                        st.rerun()
            
            with col10:
                # Anomalous button - dynamic styling based on state
                btn_type = "primary" if current_anomalous else "secondary"
                if st.button("anomalous", key=f"anomalous_{imdb_id}", type=btn_type, use_container_width=True):
                    if toggle_anomalous(config, imdb_id, current_anomalous):
                        # Refresh data to show updated values
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
                    st.write(f"• **Prediction:** {'Would Watch' if movie_data.get('prediction') == 1 else 'Would Not Watch'}")
                    st.write(f"• **Probability:** {float(movie_data.get('probability', 0)):.4f}")
                    st.write(f"• **CM Value:** {movie_data.get('cm_value', 'NULL').upper()}")
                    st.write(f"• **Created:** {movie_data.get('prediction_created_at', 'NULL')}")
                    
                    # Explanation of CM value
                    cm_value = movie_data.get('cm_value', '')
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
    
    # Only show load more if we have more results available and haven't hit the 100 limit
    if st.session_state.current_limit < 100 and len(predictions) == st.session_state.current_limit:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🔄 Load More", type="primary", use_container_width=True, key="load_more_btn"):
                # Increase limit by 20, up to 100
                st.session_state.current_limit = min(st.session_state.current_limit + 20, 100)
                st.rerun()
    elif len(predictions) == 100:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.info("✅ Showing maximum 100 movies")
    elif len(predictions) < st.session_state.current_limit:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.info("✅ All movies loaded")

if __name__ == "__main__":
    main()