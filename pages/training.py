import streamlit as st
import requests
from config import Config
from typing import Dict, List, Optional
import datetime

st.set_page_config(
    page_title="training",
    page_icon="./favicon/android-chrome-192x192.png",
    layout="wide"
)

# Dynamic CSS for button styling
st.markdown("""
<style>
/* Blue button - would_watch column 7 */
div[data-testid="stHorizontalBlock"] > div:nth-child(7) button[kind="primary"] {
    background-color: #1f77b4 !important;
    color: white !important;
    border-color: #1f77b4 !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(7) button[kind="secondary"] {
    background-color: #2d2d2d !important;
    color: #1f77b4 !important;
    border-color: #1f77b4 !important;
}

/* Red button - would_not column 8 */
div[data-testid="stHorizontalBlock"] > div:nth-child(8) button[kind="primary"] {
    background-color: #d62728 !important;
    color: white !important;
    border-color: #d62728 !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(8) button[kind="secondary"] {
    background-color: #2d2d2d !important;
    color: #d62728 !important;
    border-color: #d62728 !important;
}

/* Green button - anomalous column 9 */
div[data-testid="stHorizontalBlock"] > div:nth-child(9) button[kind="primary"] {
    background-color: #2ca02c !important;
    color: white !important;
    border-color: #2ca02c !important;
}
div[data-testid="stHorizontalBlock"] > div:nth-child(9) button[kind="secondary"] {
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


def fetch_training_data(config: Config, limit: int = 20, offset: int = 0,
                        search_term: str = None, search_type: str = "title",
                        reviewed_filter: str = "unreviewed",
                        anomalous_filter: str = "all") -> Optional[Dict]:
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


def display_movie_row(item: Dict, config: Config, idx: int):
    """Display a single movie row with all the controls"""
    imdb_id = item.get("imdb_id")

    with st.container():
        # Main row with basic info and buttons
        col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([3, 1, 1, 0.8, 0.6, 1.5, 1.2, 1.2, 1.2])

        with col1:
            st.write(f"**{item.get('media_title', 'Unknown')}**")

        with col2:
            rt_score = item.get('rt_score')
            if rt_score is None:
                st.progress(0.0)
                st.caption("RT: NULL")
            else:
                st.progress(rt_score / 100.0)
                st.caption(f"RT: {rt_score}%")

        with col3:
            imdb_votes = item.get('imdb_votes')
            if imdb_votes is None:
                st.progress(0.0)
                st.caption("IMDB: NULL")
            else:
                if isinstance(imdb_votes, int):
                    progress_value = min(imdb_votes / 100000.0, 1.0)
                    st.progress(progress_value)
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
            release_year = item.get('release_year')
            if release_year is None:
                st.progress(0.0)
                st.caption("Year: NULL")
            else:
                min_year = 1950
                max_year = datetime.datetime.now().year

                if isinstance(release_year, int):
                    clamped_year = max(release_year, min_year)
                    progress_value = (clamped_year - min_year) / (max_year - min_year)
                    st.progress(progress_value)
                    st.caption(f"Year: {release_year}")
                else:
                    st.progress(0.0)
                    st.caption(f"Year: {release_year}")

        with col5:
            origin_country = item.get('origin_country')
            if origin_country and isinstance(origin_country, list):
                flags = [country_code_to_flag(country) for country in origin_country]
                country_display = ''.join(flags)
            elif origin_country:
                country_display = country_code_to_flag(str(origin_country))
            else:
                country_display = 'NULL'
            st.write(f"Country: {country_display}")

        with col6:
            genres = item.get('genre', [])
            if genres and isinstance(genres, list):
                genre_emojis = [genre_to_emoji(genre) for genre in genres]
                genre_display = "".join(genre_emojis)
            else:
                genre_display = "NULL"
            st.write(f"Genre: {genre_display}")

        current_label = item.get('label', '')
        current_anomalous = item.get('anomalous', False)

        with col7:
            btn_type = "primary" if current_label == "would_watch" else "secondary"
            if st.button("would_watch", key=f"would_watch_{imdb_id}_{idx}", type=btn_type, use_container_width=True):
                if update_label(config, imdb_id, "would_watch", current_label):
                    st.rerun()

        with col8:
            btn_type = "primary" if current_label == "would_not_watch" else "secondary"
            if st.button("would_not", key=f"would_not_watch_{imdb_id}_{idx}", type=btn_type, use_container_width=True):
                if update_label(config, imdb_id, "would_not_watch", current_label):
                    st.rerun()

        with col9:
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
        anomalous_filter=st.session_state.anomalous_filter
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
