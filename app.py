import streamlit as st

st.set_page_config(
    page_title="center-console",
    page_icon="./favicon/android-chrome-192x192.png",
    layout="wide"
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

# Main content in markdown-styled container
st.markdown("""
<div class="markdown-container">

# 🎬 Center Console

Welcome to the Center Console application for managing the Rear Differential media processing pipeline.

## 📋 Available Pages

Select a page from the sidebar to get started, or click the links below:

### 🎬 [Media](media)
**Media Browser & Pipeline Management**
- Browse most recent 20 media items by default
- Search media items by hash or title
- View detailed metadata for movies and TV shows
- Update pipeline status, error conditions, and rejection status
- Color-coded status indicators with expandable details

### 📚 [Training](training)
**Movie Review & Search Interface**
- Review unreviewed movies from the training dataset (backlog)
- Search movies by title or IMDB ID
- Binary classification: `would_watch` vs `would_not_watch`
- Toggle anomalous status for items
- Filter by reviewed status and anomalous flag
- Display movie metadata (RT score, IMDB votes, genre)
- Expandable details with comprehensive movie information
- Pagination and auto-refresh after each review decision

### 🔍 [Prediction Anomalies](prediction-anomalies)
**ML Prediction Analysis**
- Review model predictions with filter by confusion matrix values
- Analyze false positives and false negatives
- Update labels for mispredicted items
- Display prediction probability and actual vs predicted labels
- Filter by: All, False Positives, False Negatives, True Positives, True Negatives

### 🗃️ [Database Migrations](get-flyway-migrations)
**Flyway Migration History**
- View database migration history and status
- Track successful and failed migrations
- Monitor database schema changes over time
- Debugging tool for database-related issues

---

## 🔧 System Information

This application connects to the Rear Differential API to provide a web interface for:
- **Media Pipeline Management**: Track items through the processing pipeline
- **Training Data Curation**: Review and label media for machine learning
- **System Monitoring**: Database migrations and system health
- **Data Exploration**: Browse and search the media collection

Use the sidebar navigation to access any of these features.

</div>
""", unsafe_allow_html=True)