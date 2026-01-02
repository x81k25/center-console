import streamlit as st

st.set_page_config(
    page_title="center-console",
    page_icon="./favicon/android-chrome-192x192.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Add custom CSS for markdown-like appearance
st.markdown("""
<style>
.markdown-container {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', 'Menlo', monospace;
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #30363d;
    margin: 10px 0;
    line-height: 1.6;
}

.markdown-container h1 {
    color: #58a6ff;
    border-bottom: 2px solid #21262d;
    padding-bottom: 8px;
    margin-bottom: 16px;
}

.markdown-container h2 {
    color: #7c3aed;
    border-bottom: 1px solid #21262d;
    padding-bottom: 6px;
    margin-top: 24px;
    margin-bottom: 12px;
}

.markdown-container h3 {
    color: #f78166;
    margin-top: 20px;
    margin-bottom: 8px;
}

.markdown-container strong {
    color: #ffa657;
    font-weight: 600;
}

.markdown-container ul {
    padding-left: 20px;
}

.markdown-container li {
    margin: 4px 0;
    color: #c9d1d9;
}

.markdown-container code {
    background-color: #161b22;
    color: #f85149;
    padding: 2px 4px;
    border-radius: 3px;
    font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', 'Menlo', monospace;
}

.markdown-container a {
    color: #58a6ff;
    text-decoration: none;
}

.markdown-container a:hover {
    text-decoration: underline;
}

.markdown-container hr {
    border: none;
    height: 1px;
    background-color: #30363d;
    margin: 24px 0;
}

.markdown-container blockquote {
    border-left: 4px solid #30363d;
    padding-left: 16px;
    margin: 16px 0;
    color: #8b949e;
}
</style>
""", unsafe_allow_html=True)

# Page title outside the container
st.title("center console")

# Changelog in collapsible expander (default collapsed)
with st.expander("changelog", expanded=False):
    # January 2, 2026
    st.subheader("January 2, 2026")
    st.markdown("""
### training page
- **radar chart visualization**: added 6-axis radar chart for movie metrics
  - displays rt_score, metascore, imdb_rating, imdb_votes, tmdb_rating, tmdb_votes
  - color-coded wedges with geometric midpoint calculations
  - NULL values shown as dark gray with value of 10
  - hover tooltips show full database field names
  - disabled zoom/pan while keeping tooltips
- **compact layout**: consolidated title, year, country flags, and genre emojis into single line
- **would_watch endpoint**: updated `would_watch` button to use dedicated endpoint
- **removed mobile enter button**: simplified search interface

### media page
- **edit subpage improvements**:
  - compact key-value display with inline HTML formatting
  - yellow back button with full width
  - horizontally scrollable filename on mobile
  - lowercase text throughout for consistency
  - light blue refresh button styling
- **removed mobile enter button**: simplified search interface

### renamed pages
- **prediction page**: renamed `prediction_anomalies` to `prediction`
  - file renamed from `prediction_anomalies.py` to `prediction.py`
  - updated page title and header to match
""")

    st.markdown("---")

    # August 3, 2025
    st.subheader("August 3, 2025")
    st.markdown("""
### new features
- **training search page**: added new page for searching and reviewing training data
  - search movies by title or IMDB ID
  - real-time search - results update as you type (no search button needed)
  - shows top 10 results sorted by most recently updated
  - view complete training data with all metadata (ratings, votes, genre, etc.)
  - update labels (`would_watch` vs `would_not_watch`)
  - toggle anomalous status for items
  - interface similar to training backlog page with expandable details
  - dynamic button styling with active/inactive states
  - now uses the `/rear-diff/training` endpoint with native title search support

### prediction anomalies page - API migration
- **migrated to movies endpoint**: transitioned from prediction and training endpoints to the unified `/rear-diff/movies/` endpoint
  - single API call now fetches all necessary data (training + prediction information combined)
  - improved performance by eliminating redundant API calls
  - maintains all existing filtering capabilities (cm_value, anomalous, etc.)
- **simplified data flow**: removed complex data merging logic since movies endpoint provides unified data structure
- **enhanced load more functionality**: updated pagination to work correctly with new endpoint
- **preserved training updates**: all PATCH operations to training endpoint remain unchanged as requested

### bug fixes
- **fixed load more button**: resolved pagination issues when loading additional results
- **improved filter handling**: better state management for filters during pagination
""")

    st.markdown("---")

    # August 2, 2025
    st.subheader("August 2, 2025")
    st.markdown("""
### UI/UX improvements
- **dynamic button styling**: implemented new button styling system across all pages
  - active buttons: colored background with white text
  - inactive buttons: dark gray background with colored text and colored border
  - applied to `would_watch`, `would_not_watch`, and `anomalous` buttons

### prediction anomalies page
- **added anomalous filter**: new dropdown to filter by anomalous status (any/true/false)
- **updated confusion matrix filter**: changed label from "filter by prediction type" to "filter by confusion matrix value"
- **removed caching**: all interactions now fetch fresh data from API
- **enhanced API integration**: anomalous filter now applied directly to prediction API calls
- **removed filter description**: cleaned up UI by removing redundant filter explanation section

### training backlog page
- **updated button styling**: applied new dynamic button styling system to `would_watch` and `would_not_watch` buttons

### cleanup
- **removed test page**: deleted button-test page after implementing styling across production pages

### debug improvements
- **enhanced API call display**: debug URL now shows all active filter parameters including anomalous filter

### bug fixes
- **fixed anomalous filter**: resolved "no training data found" errors when anomalous filter is applied
- **fixed anomalous filter display**: now only displays IMDB IDs that actually match the anomalous filter criteria
- **fixed empty elements**: eliminated empty prediction elements when anomalous filter reduces available training data
- **fixed element count**: removed duplicate anomalous filtering to display correct number of items based on prediction API results
""")

    st.caption("changes are listed in reverse chronological order (newest first)")

# Main content in markdown-styled container
st.markdown("""
<div class="markdown-container">

welcome to the Center Console application for managing the Rear Differential media processing pipeline.

## available pages

select a page from the sidebar to get started, or click the links below:

### [media](media)
**media browser & pipeline management**
- browse most recent 20 media items by default
- search media items by hash or title
- view detailed metadata for movies and TV shows
- update pipeline status, error conditions, and rejection status
- color-coded status indicators with expandable details

### [training](training)
**movie review & search interface**
- review unreviewed movies from the training dataset (backlog)
- search movies by title or IMDB ID
- binary classification: `would_watch` vs `would_not_watch`
- toggle anomalous status for items
- filter by reviewed status and anomalous flag
- display movie metadata (RT score, IMDB votes, genre)
- expandable details with comprehensive movie information
- pagination and auto-refresh after each review decision

### [prediction](prediction)
**ML prediction analysis**
- review model predictions with filter by confusion matrix values
- analyze false positives and false negatives
- update labels for mispredicted items
- display prediction probability and actual vs predicted labels
- filter by: all, false positives, false negatives, true positives, true negatives

### [database migrations](flyway)
**Flyway migration history**
- view database migration history and status
- track successful and failed migrations
- monitor database schema changes over time
- debugging tool for database-related issues

---

## system information

this application connects to the Rear Differential API to provide a web interface for:
- **media pipeline management**: track items through the processing pipeline
- **training data curation**: review and label media for machine learning
- **system monitoring**: database migrations and system health
- **data exploration**: browse and search the media collection

use the sidebar navigation to access any of these features.

</div>
""", unsafe_allow_html=True)