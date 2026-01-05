import streamlit as st
import requests
import plotly.graph_objects as go
import math
from config import Config
from typing import Dict, List, Optional

st.set_page_config(
    page_title="prediction", 
    page_icon="./favicon/android-chrome-192x192.png",
    layout="wide"
)

# Sidebar keys
with st.sidebar:
    with st.expander("confusion matrix key", expanded=False):
        st.markdown("""
| icon | meaning |
|:---:|:---|
| 🔵 | True Positive |
| 🔴 | True Negative |
| 🟡 | False Negative |
| 🟣 | False Positive |
""")

    with st.expander("radar chart key", expanded=False):
        st.markdown("""
<style>
.color-box { display: inline-block; width: 14px; height: 14px; border-radius: 2px; margin-right: 6px; vertical-align: middle; }
</style>
<p><span class="color-box" style="background: rgba(214, 39, 40, 0.8);"></span> RT Score</p>
<p><span class="color-box" style="background: rgba(44, 160, 44, 0.8);"></span> Metascore</p>
<p><span class="color-box" style="background: rgba(255, 197, 24, 0.8);"></span> IMDB Rating</p>
<p><span class="color-box" style="background: rgba(153, 115, 0, 0.8);"></span> IMDB Votes</p>
<p><span class="color-box" style="background: rgba(144, 206, 161, 0.8);"></span> TMDB Rating</p>
<p><span class="color-box" style="background: rgba(1, 180, 228, 0.8);"></span> TMDB Votes</p>
<p><span class="color-box" style="background: rgba(80, 80, 80, 0.8);"></span> NULL</p>
""", unsafe_allow_html=True)

# Dynamic CSS for button styling and compact layout
st.markdown("""
<style>
/* Reduce vertical spacing */
.stCaption, [data-testid="stCaptionContainer"], small {
    margin-bottom: -15px !important;
    padding-bottom: 0 !important;
}
[data-testid="stMarkdownContainer"] p {
    margin-bottom: 0.5rem !important;
}
hr {
    margin-top: 0.5rem !important;
    margin-bottom: 0.5rem !important;
}
[data-testid="stBaseButton-secondary"] p,
[data-testid="stBaseButton-primary"] p,
.stButton button p {
    margin: 0 !important;
    padding-top: 2px !important;
}

/* Compact plotly chart container */
[data-testid="stPlotlyChart"] {
    margin-top: -10px !important;
    margin-bottom: -10px !important;
}

/* Mobile: compact chart without overlap */
@media (max-width: 768px) {
    [data-testid="stPlotlyChart"] {
        margin-top: -45px !important;
        margin-bottom: -45px !important;
    }
}

/* Blue button - would_watch */
div[class*="st-key-would_watch_"] button[kind="primary"] {
    background-color: #1f77b4 !important;
    color: white !important;
    border-color: #1f77b4 !important;
}
div[class*="st-key-would_watch_"] button[kind="secondary"] {
    background-color: #2d2d2d !important;
    color: #1f77b4 !important;
    border-color: #1f77b4 !important;
}

/* Red button - would_not_watch */
div[class*="st-key-would_not_watch_"] button[kind="primary"] {
    background-color: #d62728 !important;
    color: white !important;
    border-color: #d62728 !important;
}
div[class*="st-key-would_not_watch_"] button[kind="secondary"] {
    background-color: #2d2d2d !important;
    color: #d62728 !important;
    border-color: #d62728 !important;
}

/* Green button - anomalous */
div[class*="st-key-anomalous_"] button[kind="primary"] {
    background-color: #2ca02c !important;
    color: white !important;
    border-color: #2ca02c !important;
}
div[class*="st-key-anomalous_"] button[kind="secondary"] {
    background-color: #2d2d2d !important;
    color: #2ca02c !important;
    border-color: #2ca02c !important;
}

/* Purple button - rerun */
div[class*="st-key-rerun_"] button[kind="primary"] {
    background-color: #9467bd !important;
    color: white !important;
    border-color: #9467bd !important;
}
div[class*="st-key-rerun_"] button[kind="secondary"] {
    background-color: #2d2d2d !important;
    color: #9467bd !important;
    border-color: #9467bd !important;
}
</style>
""", unsafe_allow_html=True)


def country_code_to_flag(country_code: str) -> str:
    """Convert 2-letter country code to flag emoji"""
    if not country_code or len(country_code) != 2:
        return country_code if country_code else ""
    return ''.join(chr(ord(c) + 0x1F1A5) for c in country_code.upper())


def genre_to_emoji(genre: str) -> str:
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
    return genre_map.get(genre, "🎬")


def normalize_imdb_votes(votes: int, max_votes: int = 1000000) -> float:
    """Normalize IMDB votes using log scale (0-100)"""
    if votes is None or votes <= 0:
        return 0
    return min(math.log10(votes) / math.log10(max_votes) * 100, 100)


def normalize_tmdb_votes(votes: int, max_votes: int = 100000) -> float:
    """Normalize TMDB votes using log scale (0-100)"""
    if votes is None or votes <= 0:
        return 0
    return min(math.log10(votes) / math.log10(max_votes) * 100, 100)


def is_null_value(val) -> bool:
    """Check if a value is NULL/None/empty"""
    if val is None:
        return True
    if isinstance(val, str) and val.strip() == '':
        return True
    return False


def safe_float(val, default=0.0) -> float:
    """Safely convert a value to float"""
    if is_null_value(val):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def safe_int(val, default=0) -> int:
    """Safely convert a value to int"""
    if is_null_value(val):
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def get_geometric_midpoint_radius(r1: float, theta1: float, r2: float, theta2: float, theta_mid: float) -> float:
    """
    Calculate the radius at theta_mid where the straight line between
    (r1, theta1) and (r2, theta2) intersects the ray at theta_mid.
    All angles in degrees.
    """
    t1 = math.radians(theta1)
    t2 = math.radians(theta2)
    tm = math.radians(theta_mid)

    x1, y1 = r1 * math.cos(t1), r1 * math.sin(t1)
    x2, y2 = r2 * math.cos(t2), r2 * math.sin(t2)

    dx_ray, dy_ray = math.cos(tm), math.sin(tm)
    dx_line, dy_line = x2 - x1, y2 - y1

    denom = dx_ray * dy_line - dy_ray * dx_line
    if abs(denom) < 1e-10:
        return (r1 + r2) / 2

    t = (x1 * dy_line - y1 * dx_line) / denom
    return max(0, t)


def create_radar_chart(item: Dict) -> go.Figure:
    """Create a compact radar chart for movie metrics with color-coded segments centered on each axis"""
    NULL_COLOR = 'rgba(80, 80, 80, 0.6)'
    NULL_VALUE = 10

    rt_score_raw = item.get('rt_score')
    metascore_raw = item.get('metascore')
    imdb_rating_raw = item.get('imdb_rating')
    imdb_votes_raw = item.get('imdb_votes')
    tmdb_rating_raw = item.get('tmdb_rating')
    tmdb_votes_raw = item.get('tmdb_votes')

    metrics = [
        {
            'name': 'RT', 'db_name': 'rt_score', 'angle': 0,
            'value': safe_float(rt_score_raw) if not is_null_value(rt_score_raw) else NULL_VALUE,
            'raw': rt_score_raw,
            'is_null': is_null_value(rt_score_raw),
            'color': 'rgba(214, 39, 40, 0.6)' if not is_null_value(rt_score_raw) else NULL_COLOR,
        },
        {
            'name': 'Meta', 'db_name': 'metascore', 'angle': 60,
            'value': safe_float(metascore_raw) if not is_null_value(metascore_raw) else NULL_VALUE,
            'raw': metascore_raw,
            'is_null': is_null_value(metascore_raw),
            'color': 'rgba(44, 160, 44, 0.6)' if not is_null_value(metascore_raw) else NULL_COLOR,
        },
        {
            'name': 'IMDB', 'db_name': 'imdb_rating', 'angle': 120,
            'value': safe_float(imdb_rating_raw) if not is_null_value(imdb_rating_raw) else NULL_VALUE,
            'raw': imdb_rating_raw,
            'is_null': is_null_value(imdb_rating_raw),
            'color': 'rgba(255, 197, 24, 0.6)' if not is_null_value(imdb_rating_raw) else NULL_COLOR,
        },
        {
            'name': 'iVotes', 'db_name': 'imdb_votes', 'angle': 180,
            'value': normalize_imdb_votes(safe_int(imdb_votes_raw)) if not is_null_value(imdb_votes_raw) else NULL_VALUE,
            'raw': imdb_votes_raw,
            'is_null': is_null_value(imdb_votes_raw),
            'color': 'rgba(153, 115, 0, 0.6)' if not is_null_value(imdb_votes_raw) else NULL_COLOR,
        },
        {
            'name': 'TMDB', 'db_name': 'tmdb_rating', 'angle': 240,
            'value': safe_float(tmdb_rating_raw) * 10 if not is_null_value(tmdb_rating_raw) else NULL_VALUE,
            'raw': tmdb_rating_raw,
            'is_null': is_null_value(tmdb_rating_raw),
            'color': 'rgba(144, 206, 161, 0.6)' if not is_null_value(tmdb_rating_raw) else NULL_COLOR,
        },
        {
            'name': 'tVotes', 'db_name': 'tmdb_votes', 'angle': 300,
            'value': normalize_tmdb_votes(safe_int(tmdb_votes_raw)) if not is_null_value(tmdb_votes_raw) else NULL_VALUE,
            'raw': tmdb_votes_raw,
            'is_null': is_null_value(tmdb_votes_raw),
            'color': 'rgba(1, 180, 228, 0.6)' if not is_null_value(tmdb_votes_raw) else NULL_COLOR,
        },
    ]

    fig = go.Figure()

    for i, metric in enumerate(metrics):
        prev_i = (i - 1) % len(metrics)
        next_i = (i + 1) % len(metrics)

        mid_before = (metric['angle'] - 30) % 360
        mid_after = (metric['angle'] + 30) % 360

        val_mid_before = get_geometric_midpoint_radius(
            metrics[prev_i]['value'], metrics[prev_i]['angle'],
            metric['value'], metric['angle'],
            mid_before
        )
        val_mid_after = get_geometric_midpoint_radius(
            metric['value'], metric['angle'],
            metrics[next_i]['value'], metrics[next_i]['angle'],
            mid_after
        )

        r_vals = [0, val_mid_before, metric['value'], val_mid_after, 0]
        theta_vals = [mid_before, mid_before, metric['angle'], mid_after, mid_before]

        if metric['is_null']:
            raw_display = "NULL"
        elif 'votes' in metric['db_name']:
            raw_display = f"{safe_int(metric['raw']):,}"
        else:
            raw_display = f"{safe_float(metric['raw']):.1f}"

        fig.add_trace(go.Scatterpolar(
            r=r_vals,
            theta=theta_vals,
            fill='toself',
            fillcolor=metric['color'],
            line=dict(color='rgba(0,0,0,0)', width=0),
            mode='lines',
            name=metric['db_name'],
            hovertemplate=f"{metric['db_name']}: {raw_display}<extra></extra>"
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                showticklabels=False,
                ticks='',
                gridcolor='rgba(255,255,255,0.2)'
            ),
            angularaxis=dict(
                showticklabels=False,
                gridcolor='rgba(255,255,255,0.2)',
                tickvals=[0, 60, 120, 180, 240, 300],
            ),
            bgcolor='rgba(0,0,0,0)'
        ),
        showlegend=False,
        dragmode=False,
        margin=dict(l=20, r=20, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    return fig


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


def rerun_metadata(_config: Config, imdb_id: str) -> bool:
    """Re-collect metadata from TMDB and OMDB APIs for a training item"""
    try:
        response = requests.patch(
            _config.get_training_rerun_metadata_endpoint(imdb_id),
            timeout=_config.api_timeout
        )
        response.raise_for_status()
        result = response.json()
        if result.get("success"):
            # Mark this item as recently rerun in session state
            if 'rerun_ids' not in st.session_state:
                st.session_state.rerun_ids = set()
            st.session_state.rerun_ids.add(imdb_id)
        return True
    except Exception as e:
        st.error(f"Failed to rerun metadata for {imdb_id}: {str(e)}")
        return False

def main():
    """Main application function"""
    try:
        config = Config()
    except ValueError as e:
        st.error(f"Configuration Error: {str(e)}")
        st.info("Please set the required environment variables: REAR_DIFF_HOST, REAR_DIFF_PORT")
        return
    
    st.title("prediction")
    
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
        item = movie_data

        with st.container():
            # Build compact metadata string
            title = item.get('media_title', 'Unknown')

            # Year
            release_year = item.get('release_year')
            year_str = f"({release_year})" if release_year else ""

            # Country flags
            origin_country = item.get('origin_country')
            if origin_country and isinstance(origin_country, list):
                flags = [country_code_to_flag(country) for country in origin_country]
                country_str = ''.join(flags)
            elif origin_country:
                country_str = country_code_to_flag(str(origin_country))
            else:
                country_str = ''

            # Genre emojis
            genres = item.get('genre', [])
            if genres and isinstance(genres, list):
                genre_emojis = [genre_to_emoji(genre) for genre in genres]
                genre_str = "".join(genre_emojis)
            else:
                genre_str = ''

            # Compact single-line display: 🔵 Title (year) 🇺🇸 💥🤣
            cm_value = movie_data.get('cm_value', '')
            cm_emoji = {'tp': '🔵', 'tn': '🔴', 'fn': '🟡', 'fp': '🟣'}.get(cm_value, '❓')
            probability = float(movie_data.get('probability', 0))

            meta_parts = [p for p in [year_str, country_str, genre_str] if p]
            meta_str = " ".join(meta_parts)
            st.markdown(f"{cm_emoji} **{title}** <span style='color: rgba(250,250,250,0.7);'>{meta_str}</span>", unsafe_allow_html=True)

            # Prediction confidence bar - color matches CM value
            bar_color = {'tp': '#1f77b4', 'tn': '#d62728', 'fp': '#9467bd', 'fn': '#f0c000'}.get(cm_value, '#888888')
            st.markdown(f"""
            <div style="background: #2d2d2d; border-radius: 4px; height: 8px; width: 100%; margin: 8px 0;">
                <div style="background: {bar_color}; border-radius: 4px; height: 100%; width: {probability * 100}%;"></div>
            </div>
            """, unsafe_allow_html=True)

            # Radar chart row
            fig = create_radar_chart(item)
            st.plotly_chart(fig, use_container_width=True, key=f"radar_{imdb_id}_{idx}", config={
                'displayModeBar': False,
                'scrollZoom': False,
                'doubleClick': False,
                'modeBarButtonsToRemove': ['zoom', 'pan', 'zoomIn', 'zoomOut', 'resetScale'],
            })

            # Button row
            current_label = item.get('label', '')
            current_human_labeled = item.get('human_labeled', False)
            current_anomalous = item.get('anomalous', False)

            btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)

            with btn_col1:
                btn_type = "primary" if current_label == "would_watch" else "secondary"
                if st.button("would_watch", key=f"would_watch_{imdb_id}_{idx}", type=btn_type, use_container_width=True):
                    if update_label(config, imdb_id, "would_watch", current_label, current_human_labeled):
                        st.rerun()

            with btn_col2:
                btn_type = "primary" if current_label == "would_not_watch" else "secondary"
                if st.button("would_not", key=f"would_not_watch_{imdb_id}_{idx}", type=btn_type, use_container_width=True):
                    if update_label(config, imdb_id, "would_not_watch", current_label, current_human_labeled):
                        st.rerun()

            with btn_col3:
                btn_type = "primary" if current_anomalous else "secondary"
                if st.button("anomalous", key=f"anomalous_{imdb_id}_{idx}", type=btn_type, use_container_width=True):
                    if toggle_anomalous(config, imdb_id, current_anomalous):
                        st.rerun()

            with btn_col4:
                # Check if this item was recently rerun
                recently_rerun = imdb_id in st.session_state.get('rerun_ids', set())
                btn_type = "primary" if recently_rerun else "secondary"
                if st.button("rerun", key=f"rerun_{imdb_id}_{idx}", type=btn_type, use_container_width=True):
                    if rerun_metadata(config, imdb_id):
                        st.rerun()
            
            # Expandable details section
            with st.expander(f"Details for {item.get('media_title', 'Unknown')}", expanded=False):
                detail_col1, detail_col2 = st.columns(2)

                with detail_col1:
                    st.write("**Basic Info:**")
                    st.write(f"- **IMDB ID:** {item.get('imdb_id', 'NULL')}")
                    st.write(f"- **TMDB ID:** {item.get('tmdb_id', 'NULL')}")
                    st.write(f"- **Release Year:** {item.get('release_year', 'NULL')}")
                    st.write(f"- **Runtime:** {item.get('runtime', 'NULL')} min")
                    st.write(f"- **Original Language:** {item.get('original_language', 'NULL')}")
                    st.write(f"- **Origin Country:** {item.get('origin_country', 'NULL')}")

                    st.write("**Status:**")
                    st.write(f"- **Current Label:** {item.get('label', 'NULL')}")
                    st.write(f"- **Human Labeled:** {item.get('human_labeled', 'NULL')}")
                    st.write(f"- **Reviewed:** {item.get('reviewed', 'NULL')}")
                    st.write(f"- **Anomalous:** {item.get('anomalous', 'NULL')}")

                with detail_col2:
                    st.write("**Ratings & Scores:**")
                    st.write(f"- **RT Score:** {item.get('rt_score', 'NULL')}")
                    st.write(f"- **IMDB Rating:** {item.get('imdb_rating', 'NULL')}")
                    st.write(f"- **IMDB Votes:** {item.get('imdb_votes', 'NULL')}")
                    st.write(f"- **TMDB Rating:** {item.get('tmdb_rating', 'NULL')}")
                    st.write(f"- **TMDB Votes:** {item.get('tmdb_votes', 'NULL')}")
                    st.write(f"- **Metascore:** {item.get('metascore', 'NULL')}")

                    st.write("**Prediction Details:**")
                    st.write(f"- **Prediction:** {'Would Watch' if item.get('prediction') == 1 else 'Would Not Watch'}")
                    st.write(f"- **Probability:** {float(item.get('probability', 0)):.4f}")
                    st.write(f"- **CM Value:** {item.get('cm_value', 'NULL').upper() if item.get('cm_value') else 'NULL'}")

                    # Explanation of CM value
                    if cm_value == 'tp':
                        st.success("🟢 **True Positive**: Model correctly predicted 'would_watch'")
                    elif cm_value == 'tn':
                        st.info("⚪ **True Negative**: Model correctly predicted 'would_not_watch'")
                    elif cm_value == 'fp':
                        st.error("🔴 **False Positive**: Model predicted 'would_watch' but actual is 'would_not_watch'")
                    elif cm_value == 'fn':
                        st.warning("🟡 **False Negative**: Model predicted 'would_not_watch' but actual is 'would_watch'")

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