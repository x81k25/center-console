import streamlit as st
import requests
import plotly.graph_objects as go
import math
from config import Config
from typing import Dict, List, Optional
import datetime

st.set_page_config(
    page_title="training",
    page_icon="./favicon/android-chrome-192x192.png",
    layout="wide"
)

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

</style>
""", unsafe_allow_html=True)

# Sidebar keys
with st.sidebar:
    with st.expander("genre key", expanded=False):
        st.markdown("""
| emoji | genre |
|:---:|:---|
| 💥 | action |
| ⛰️ | adventure |
| ✏️ | animation |
| 🤣 | comedy |
| 👮‍♂️ | crime |
| 📚 | documentary |
| 💔 | drama |
| 🏠 | family |
| 🦄 | fantasy |
| 🏛️ | history |
| 😱 | horror |
| 👶 | kids |
| 🎵 | music |
| 🔍 | mystery |
| 📰 | news |
| 🎪 | reality |
| 💕 | romance |
| 🚀 | science fiction |
| 💬 | talk |
| ⚡ | thriller |
| 📺 | TV movie |
| ⚔️ | war |
| 🤠 | western |
| 🎬 | other |
""")

    with st.expander("country key", expanded=False):
        st.markdown("""
| flag | country |
|:---:|:---|
| 🇺🇸 | US |
| 🇬🇧 | UK |
| 🇨🇦 | Canada |
| 🇦🇺 | Australia |
| 🇫🇷 | France |
| 🇩🇪 | Germany |
| 🇮🇹 | Italy |
| 🇪🇸 | Spain |
| 🇯🇵 | Japan |
| 🇰🇷 | South Korea |
| 🇨🇳 | China |
| 🇮🇳 | India |
| 🇧🇷 | Brazil |
| 🇲🇽 | Mexico |
| 🇷🇺 | Russia |
| 🇸🇪 | Sweden |
| 🇳🇴 | Norway |
| 🇩🇰 | Denmark |
| 🇳🇱 | Netherlands |
| 🇧🇪 | Belgium |
| 🇮🇪 | Ireland |
| 🇳🇿 | New Zealand |
| 🇦🇷 | Argentina |
| 🇿🇦 | South Africa |
""")


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
    # Log scale: log(votes) / log(max_votes) * 100
    return min(math.log10(votes) / math.log10(max_votes) * 100, 100)


def get_geometric_midpoint_radius(r1: float, theta1: float, r2: float, theta2: float, theta_mid: float) -> float:
    """
    Calculate the radius at theta_mid where the straight line between
    (r1, theta1) and (r2, theta2) intersects the ray at theta_mid.
    All angles in degrees.
    """
    # Convert to radians
    t1 = math.radians(theta1)
    t2 = math.radians(theta2)
    tm = math.radians(theta_mid)

    # Convert polar to Cartesian
    x1, y1 = r1 * math.cos(t1), r1 * math.sin(t1)
    x2, y2 = r2 * math.cos(t2), r2 * math.sin(t2)

    # Direction of the midpoint ray
    dx_ray, dy_ray = math.cos(tm), math.sin(tm)

    # Line segment direction
    dx_line, dy_line = x2 - x1, y2 - y1

    # Find intersection using parametric form
    # Ray: (t * dx_ray, t * dy_ray)
    # Line: (x1 + s * dx_line, y1 + s * dy_line)
    # Solve: t * dx_ray = x1 + s * dx_line
    #        t * dy_ray = y1 + s * dy_line

    denom = dx_ray * dy_line - dy_ray * dx_line
    if abs(denom) < 1e-10:
        # Lines are parallel, fall back to average
        return (r1 + r2) / 2

    t = (x1 * dy_line - y1 * dx_line) / denom

    # t is the radius at the midpoint angle
    return max(0, t)


def normalize_tmdb_votes(votes: int, max_votes: int = 100000) -> float:
    """Normalize TMDB votes using log scale (0-100)"""
    if votes is None or votes <= 0:
        return 0
    # Log scale: log(votes) / log(max_votes) * 100
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


def create_radar_chart(item: Dict) -> go.Figure:
    """Create a compact radar chart for movie metrics with color-coded segments centered on each axis"""
    # Dark gray color for NULL values
    NULL_COLOR = 'rgba(80, 80, 80, 0.6)'
    NULL_VALUE = 10  # Normalized display value for NULL metrics

    # Extract raw values (None if NULL)
    rt_score_raw = item.get('rt_score')
    metascore_raw = item.get('metascore')
    imdb_rating_raw = item.get('imdb_rating')
    imdb_votes_raw = item.get('imdb_votes')
    tmdb_rating_raw = item.get('tmdb_rating')
    tmdb_votes_raw = item.get('tmdb_votes')

    # Define metrics with colors and full db names for tooltips
    # Using degrees for precise angular positioning
    # 6 main axes at 0°, 60°, 120°, 180°, 240°, 300°
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

    # Create a wedge for each metric centered on its axis
    # Each wedge spans from midpoint_before -> axis -> midpoint_after
    for i, metric in enumerate(metrics):
        prev_i = (i - 1) % len(metrics)
        next_i = (i + 1) % len(metrics)

        # Calculate midpoint angles (30° offset for 6 metrics with 60° spacing)
        mid_before = (metric['angle'] - 30) % 360
        mid_after = (metric['angle'] + 30) % 360

        # Calculate geometric midpoint values (where straight line intersects midpoint ray)
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

        # Wedge: center -> mid_before -> axis -> mid_after -> center
        r_vals = [0, val_mid_before, metric['value'], val_mid_after, 0]
        theta_vals = [mid_before, mid_before, metric['angle'], mid_after, mid_before]

        # Format raw value (use commas for vote counts, show NULL for missing)
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
            line=dict(color='rgba(0,0,0,0)', width=0),  # Invisible borders
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
                tickvals=[0, 60, 120, 180, 240, 300],  # 6 lines matching data points
            ),
            bgcolor='rgba(0,0,0,0)'
        ),
        showlegend=False,
        dragmode=False,  # Disable drag interactions
        margin=dict(l=20, r=20, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    return fig


def fetch_training_data(config: Config, limit: int = 20, offset: int = 0,
                        search_term: str = None, search_type: str = "title",
                        reviewed_filter: str = "unreviewed",
                        anomalous_filter: str = "all",
                        label_filter: str = "all") -> Optional[Dict]:
    """Fetch training data from the API with filters"""
    try:
        params = {
            "limit": limit,
            "offset": offset,
            "sort_by": "updated_at",
            "sort_order": "desc",
            "media_type": "movie"
        }

        # Add search parameter
        if search_term:
            if search_type == "imdb_id":
                params["imdb_id"] = search_term
            else:
                params["media_title"] = search_term

        # Add reviewed filter
        if reviewed_filter == "unreviewed":
            params["reviewed"] = "false"
        elif reviewed_filter == "reviewed":
            params["reviewed"] = "true"
        # "all" means no filter

        # Add anomalous filter
        if anomalous_filter == "yes":
            params["anomalous"] = "true"
        elif anomalous_filter == "no":
            params["anomalous"] = "false"
        # "all" means no filter

        # Add label filter
        if label_filter != "all":
            params["label"] = label_filter

        response = requests.get(
            config.training_endpoint,
            params=params,
            timeout=config.api_timeout
        )
        response.raise_for_status()

        # Store the actual URL for debugging
        st.session_state.last_api_url = response.url

        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch training data: {str(e)}")
        return None


def fetch_unreviewed_count(config: Config) -> int:
    """Fetch count of unreviewed items"""
    try:
        params = {
            "limit": 1000,
            "reviewed": "false",
            "media_type": "movie"
        }
        response = requests.get(
            config.training_endpoint,
            params=params,
            timeout=config.api_timeout
        )
        response.raise_for_status()
        data = response.json()
        return len(data.get("data", []))
    except Exception:
        return 0


def update_label(config: Config, imdb_id: str, new_label: str, current_label: str) -> bool:
    """Update the label for a training item"""
    try:
        if new_label == current_label:
            payload = {
                "imdb_id": imdb_id,
                "reviewed": True
            }
        else:
            payload = {
                "imdb_id": imdb_id,
                "label": new_label,
                "human_labeled": True,
                "reviewed": True
            }

        response = requests.patch(
            config.get_training_update_endpoint(imdb_id),
            json=payload,
            timeout=config.api_timeout
        )
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Failed to update training item {imdb_id}: {str(e)}")
        return False


def toggle_anomalous(config: Config, imdb_id: str, current_anomalous: bool) -> bool:
    """Toggle the anomalous status for a training item"""
    try:
        payload = {
            "imdb_id": imdb_id,
            "anomalous": not current_anomalous
        }

        response = requests.patch(
            config.get_training_update_endpoint(imdb_id),
            json=payload,
            timeout=config.api_timeout
        )
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Failed to toggle anomalous for {imdb_id}: {str(e)}")
        return False


def would_not_watch_training(config: Config, imdb_id: str) -> bool:
    """Mark a training item as would_not_watch using the would_not_watch endpoint.

    This sets label to would_not_watch, marks as human_labeled and reviewed,
    and attempts to delete associated media files.
    """
    try:
        response = requests.patch(
            config.get_training_would_not_watch_endpoint(imdb_id),
            timeout=config.api_timeout
        )
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Failed to mark training item {imdb_id} as would_not_watch: {str(e)}")
        return False


def would_watch_training(config: Config, imdb_id: str) -> bool:
    """Mark a training item as would_watch using the would_watch endpoint.

    This sets label to would_watch, marks as human_labeled and reviewed.
    """
    try:
        response = requests.patch(
            config.get_training_would_watch_endpoint(imdb_id),
            timeout=config.api_timeout
        )
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Failed to mark training item {imdb_id} as would_watch: {str(e)}")
        return False


def display_movie_row(item: Dict, config: Config, idx: int):
    """Display a single movie row with all the controls"""
    imdb_id = item.get("imdb_id")

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

        # Compact single-line display: Title (year) 🇺🇸 💥🤣
        meta_parts = [p for p in [year_str, country_str, genre_str] if p]
        meta_str = " ".join(meta_parts)
        st.markdown(f"**{title}** <span style='color: rgba(250,250,250,0.7);'>{meta_str}</span>", unsafe_allow_html=True)

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
        current_anomalous = item.get('anomalous', False)

        btn_col1, btn_col2, btn_col3 = st.columns(3)

        with btn_col1:
            btn_type = "primary" if current_label == "would_watch" else "secondary"
            if st.button("would_watch", key=f"would_watch_{imdb_id}_{idx}", type=btn_type, use_container_width=True):
                if would_watch_training(config, imdb_id):
                    st.rerun()

        with btn_col2:
            btn_type = "primary" if current_label == "would_not_watch" else "secondary"
            if st.button("would_not", key=f"would_not_watch_{imdb_id}_{idx}", type=btn_type, use_container_width=True):
                if would_not_watch_training(config, imdb_id):
                    st.rerun()

        with btn_col3:
            btn_type = "primary" if current_anomalous else "secondary"
            if st.button("anomalous", key=f"anomalous_{imdb_id}_{idx}", type=btn_type, use_container_width=True):
                if toggle_anomalous(config, imdb_id, current_anomalous):
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

                st.write("**Financial:**")
                st.write(f"- **Budget:** ${item.get('budget', 'NULL'):,}" if item.get('budget') else "- **Budget:** NULL")
                st.write(f"- **Revenue:** ${item.get('revenue', 'NULL'):,}" if item.get('revenue') else "- **Revenue:** NULL")

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


def main():
    """Main application function"""
    try:
        config = Config()
    except ValueError as e:
        st.error(f"Configuration Error: {str(e)}")
        st.info("Please set the required environment variables: REAR_DIFF_HOST, REAR_DIFF_PORT_EXTERNAL")
        return

    st.title("training")

    # Initialize session state
    if 'search_term' not in st.session_state:
        st.session_state.search_term = ""
    if 'search_type' not in st.session_state:
        st.session_state.search_type = "title"
    if 'reviewed_filter' not in st.session_state:
        st.session_state.reviewed_filter = "unreviewed"
    if 'anomalous_filter' not in st.session_state:
        st.session_state.anomalous_filter = "all"
    if 'label_filter' not in st.session_state:
        st.session_state.label_filter = "all"
    if 'page_offset' not in st.session_state:
        st.session_state.page_offset = 0

    # Fetch unreviewed count for filter label
    unreviewed_count = fetch_unreviewed_count(config)

    # Search and filters row
    search_col1, search_col2, search_col3, search_col4 = st.columns([3, 1, 1, 0.3])

    with search_col1:
        search_term = st.text_input("Search", placeholder="Enter title or IMDB ID...", key="search_input", label_visibility="collapsed")

    with search_col2:
        search_type = st.selectbox("Search By", ["title", "imdb_id"], key="search_type_select", label_visibility="collapsed")

    with search_col3:
        popover_label = f"backlog ({unreviewed_count})" if unreviewed_count > 0 else "filters"
        with st.popover(popover_label, use_container_width=True):
            if unreviewed_count > 0:
                st.markdown(f'<span style="color: #ffc107; font-weight: bold;">{unreviewed_count} items in backlog</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span style="color: #28a745; font-weight: bold;">Backlog cleared</span>', unsafe_allow_html=True)

            st.divider()

            reviewed_options = ["unreviewed", "reviewed", "all"]
            reviewed_filter = st.selectbox(
                "Reviewed Status",
                options=reviewed_options,
                index=reviewed_options.index(st.session_state.reviewed_filter),
                key="reviewed_filter_select"
            )
            if reviewed_filter != st.session_state.reviewed_filter:
                st.session_state.reviewed_filter = reviewed_filter
                st.session_state.page_offset = 0
                st.rerun()

            anomalous_options = ["all", "yes", "no"]
            anomalous_filter = st.selectbox(
                "Anomalous",
                options=anomalous_options,
                index=anomalous_options.index(st.session_state.anomalous_filter),
                key="anomalous_filter_select"
            )
            if anomalous_filter != st.session_state.anomalous_filter:
                st.session_state.anomalous_filter = anomalous_filter
                st.session_state.page_offset = 0
                st.rerun()

            label_options = ["all", "would_watch", "would_not_watch"]
            label_filter = st.selectbox(
                "Label",
                options=label_options,
                index=label_options.index(st.session_state.label_filter),
                key="label_filter_select"
            )
            if label_filter != st.session_state.label_filter:
                st.session_state.label_filter = label_filter
                st.session_state.page_offset = 0
                st.rerun()

    with search_col4:
        if st.button("↻", key="refresh_btn", use_container_width=True):
            st.rerun()

    # Build and display API URL
    page_size = 20
    params = {
        "limit": page_size,
        "offset": st.session_state.page_offset,
        "sort_by": "updated_at",
        "sort_order": "desc",
        "media_type": "movie"
    }

    if search_term:
        if search_type == "imdb_id":
            params["imdb_id"] = search_term
        else:
            params["media_title"] = search_term

    if st.session_state.reviewed_filter == "unreviewed":
        params["reviewed"] = "false"
    elif st.session_state.reviewed_filter == "reviewed":
        params["reviewed"] = "true"

    if st.session_state.anomalous_filter == "yes":
        params["anomalous"] = "true"
    elif st.session_state.anomalous_filter == "no":
        params["anomalous"] = "false"

    if st.session_state.label_filter != "all":
        params["label"] = st.session_state.label_filter

    param_string = "&".join([f"{k}={v}" for k, v in params.items()])
    api_url = f"{config.training_endpoint}?{param_string}"
    st.code(api_url, language="bash")

    # Fetch data
    data = fetch_training_data(
        config,
        limit=page_size,
        offset=st.session_state.page_offset,
        search_term=search_term if search_term else None,
        search_type=search_type,
        reviewed_filter=st.session_state.reviewed_filter,
        anomalous_filter=st.session_state.anomalous_filter,
        label_filter=st.session_state.label_filter
    )

    if not data:
        return

    items = data.get("data", [])

    if not items:
        if st.session_state.reviewed_filter == "unreviewed" and not search_term:
            st.success("Backlog cleared")
        else:
            st.info("No movies found")
        return

    # Display count with filter info
    filter_parts = []
    if st.session_state.reviewed_filter != "all":
        filter_parts.append(st.session_state.reviewed_filter)
    if st.session_state.anomalous_filter != "all":
        filter_parts.append(f"anomalous: {st.session_state.anomalous_filter}")
    filter_desc = f" ({', '.join(filter_parts)})" if filter_parts else ""

    start_idx = st.session_state.page_offset + 1
    end_idx = st.session_state.page_offset + len(items)
    range_str = f"{start_idx}-{end_idx}"

    if search_term:
        st.info(f"showing {range_str}{filter_desc} matching '{search_term}'")
    else:
        st.info(f"showing {range_str}{filter_desc}")

    # Display each movie
    for idx, item in enumerate(items):
        display_movie_row(item, config, idx)

    # Pagination
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
        if len(items) == page_size:
            if st.button("Next →", use_container_width=True):
                st.session_state.page_offset += page_size
                st.rerun()


if __name__ == "__main__":
    main()
