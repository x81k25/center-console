import streamlit as st
import requests
import pandas as pd
from config import Config
from typing import Dict, List, Optional
import time

st.set_page_config(page_title="training-search", layout="wide")

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

def search_movies(_config: Config, search_term: str, search_type: str = "title") -> Optional[Dict]:
    """Search for movies by title or IMDB ID"""
    try:
        # Build API parameters for movies endpoint
        params = {
            "limit": 10,  # Only top 10 results
            "media_type": "movie",
            "sort_by": "training_updated_at",
            "sort_order": "desc"
        }
        
        # Add search parameter based on type
        if search_type == "title":
            params["media_title"] = search_term
        else:  # imdb_id
            params["imdb_id"] = search_term
        
        response = requests.get(
            f"{_config.base_url}movies/",
            params=params,
            timeout=_config.api_timeout
        )
        response.raise_for_status()
        data = response.json()
        
        # Store debug info in session state
        st.session_state.debug_api_call = response.url
        
        return data
            
    except Exception as e:
        st.error(f"Failed to search movies: {str(e)}")
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

def display_movie_row(movie_data: Dict, config: Config, idx: int):
    """Display a single movie row with all the controls"""
    imdb_id = movie_data.get("imdb_id")
    
    with st.container():
        # Main row with basic info and buttons
        col1, col2, col3, col4, col5, col6, col7, col8, col9, col10 = st.columns([2.2, 1, 1, 0.8, 0.6, 1, 1.3, 1.1, 1.1, 1.1])
        
        with col1:
            st.write(f"**{movie_data.get('media_title', 'Unknown')}**")
        
        with col2:
            rt_score = movie_data.get('rt_score')
            if rt_score is None:
                st.progress(0.0)
                st.caption("RT: NULL")
            else:
                st.progress(rt_score / 100.0)
                st.caption(f"RT: {rt_score}%")
        
        with col3:
            imdb_votes = movie_data.get('imdb_votes')
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
            release_year = movie_data.get('release_year')
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
            
            origin_country = movie_data.get('origin_country')
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
            # Show prediction probability as progress bar if available
            probability = movie_data.get('probability')
            if probability is not None:
                st.progress(float(probability))
                st.caption(f"Pred: {float(probability):.2f}")
            else:
                st.write("Pred: N/A")
        
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
            
            genres = movie_data.get('genre', [])
            if genres and isinstance(genres, list):
                # Show all genre emojis
                genre_emojis = [genre_to_emoji(genre) for genre in genres]
                genre_display = "".join(genre_emojis)
            else:
                genre_display = "NULL"
            
            # Add CM value indicator if available
            cm_value = movie_data.get('cm_value', '')
            cm_emoji = {
                'tp': '🟢',
                'tn': '⚪', 
                'fp': '🔴',
                'fn': '🟡'
            }.get(cm_value, '')
            
            if cm_emoji:
                st.write(f"{cm_emoji} {genre_display}")
            else:
                st.write(genre_display)
        
        current_label = movie_data.get('label', '')
        current_human_labeled = movie_data.get('human_labeled', False)
        current_anomalous = movie_data.get('anomalous', False)
        
        with col8:
            # Would Watch button - dynamic styling based on state
            btn_type = "primary" if current_label == "would_watch" else "secondary"
            if st.button("would_watch", key=f"would_watch_{imdb_id}_{idx}", type=btn_type, use_container_width=True):
                if update_label(config, imdb_id, "would_watch", current_label, current_human_labeled):
                    # Refresh data to show updated values
                    st.rerun()
        
        with col9:
            # Would Not Watch button - dynamic styling based on state
            btn_type = "primary" if current_label == "would_not_watch" else "secondary"
            if st.button("would_not", key=f"would_not_watch_{imdb_id}_{idx}", type=btn_type, use_container_width=True):
                if update_label(config, imdb_id, "would_not_watch", current_label, current_human_labeled):
                    # Refresh data to show updated values
                    st.rerun()
        
        with col10:
            # Anomalous button - dynamic styling based on state
            btn_type = "primary" if current_anomalous else "secondary"
            if st.button("anomalous", key=f"anomalous_{imdb_id}_{idx}", type=btn_type, use_container_width=True):
                if toggle_anomalous(config, imdb_id, current_anomalous):
                    # Refresh data to show updated values
                    st.rerun()
        
        # Expandable details section
        with st.expander(f"📋 Details for {movie_data.get('media_title', 'Unknown')}", expanded=False):
            detail_col1, detail_col2, detail_col3 = st.columns(3)
            
            with detail_col1:
                st.write("**Basic Info:**")
                st.write(f"• **IMDB ID:** {movie_data.get('imdb_id', 'NULL')}")
                st.write(f"• **TMDB ID:** {movie_data.get('tmdb_id', 'NULL')}")
                st.write(f"• **Release Year:** {movie_data.get('release_year', 'NULL')}")
                st.write(f"• **Runtime:** {movie_data.get('runtime', 'NULL')} min")
                st.write(f"• **Original Language:** {movie_data.get('original_language', 'NULL')}")
                st.write(f"• **Origin Country:** {movie_data.get('origin_country', 'NULL')}")
                
                st.write("**Status:**")
                st.write(f"• **Current Label:** {movie_data.get('label', 'NULL')}")
                st.write(f"• **Human Labeled:** {movie_data.get('human_labeled', 'NULL')}")
                st.write(f"• **Reviewed:** {movie_data.get('reviewed', 'NULL')}")
                st.write(f"• **Anomalous:** {movie_data.get('anomalous', 'NULL')}")
            
            with detail_col2:
                st.write("**Ratings & Scores:**")
                st.write(f"• **RT Score:** {movie_data.get('rt_score', 'NULL')}")
                st.write(f"• **IMDB Rating:** {movie_data.get('imdb_rating', 'NULL')}")
                st.write(f"• **IMDB Votes:** {movie_data.get('imdb_votes', 'NULL')}")
                st.write(f"• **TMDB Rating:** {movie_data.get('tmdb_rating', 'NULL')}")
                st.write(f"• **TMDB Votes:** {movie_data.get('tmdb_votes', 'NULL')}")
                st.write(f"• **Metascore:** {movie_data.get('metascore', 'NULL')}")
                
                st.write("**Financial:**")
                st.write(f"• **Budget:** ${movie_data.get('budget', 'NULL'):,}" if movie_data.get('budget') else "• **Budget:** NULL")
                st.write(f"• **Revenue:** ${movie_data.get('revenue', 'NULL'):,}" if movie_data.get('revenue') else "• **Revenue:** NULL")
            
            with detail_col3:
                st.write("**Prediction Details:**")
                if movie_data.get('prediction') is not None:
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
                else:
                    st.write("• **No prediction data available**")
            
            st.write("**Additional Info:**")
            st.write(f"• **Genres:** {', '.join(movie_data.get('genre', [])) if movie_data.get('genre') else 'NULL'}")
            st.write(f"• **Production Status:** {movie_data.get('production_status', 'NULL')}")
            st.write(f"• **Tagline:** {movie_data.get('tagline', 'NULL')}")
            
            if movie_data.get('overview'):
                st.write("**Overview:**")
                st.write(movie_data.get('overview'))
            
            st.write("**Timestamps:**")
            st.write(f"• **Created:** {movie_data.get('created_at', 'NULL')}")
            st.write(f"• **Updated:** {movie_data.get('updated_at', 'NULL')}")
        
        st.divider()

def main():
    """Main application function"""
    try:
        config = Config()
    except ValueError as e:
        st.error(f"Configuration Error: {str(e)}")
        st.info("Please set the required environment variables: REAR_DIFF_HOST, REAR_DIFF_PORT")
        return
    
    st.title("training-search")
    
    # Search section
    st.subheader("Search Movies")
    
    search_col1, search_col2 = st.columns([3, 1])
    
    with search_col1:
        search_term = st.text_input("Search Term", placeholder="Enter title or IMDB ID...", key="search_input")
    
    with search_col2:
        search_type = st.selectbox("Search By", ["title", "imdb_id"], key="search_type")
    
    # Perform search when input changes
    if search_term:
        with st.spinner("Searching..."):
            result = search_movies(config, search_term, search_type)
        
        if result is not None:
            movies = result.get("data", [])
            
            # Display API call debug info
            if 'debug_api_call' in st.session_state:
                st.code(st.session_state.debug_api_call, language="bash")
            
            if not movies:
                st.info("✅ No movies found matching your search criteria")
            else:
                st.subheader(f"Showing top {len(movies)} movie(s)")
                
                # Display each movie
                for idx, movie_data in enumerate(movies):
                    display_movie_row(movie_data, config, idx)
    else:
        st.info("Start typing to search for movies...")

if __name__ == "__main__":
    main()