import streamlit as st

st.set_page_config(
    page_title="Center Console",
    page_icon="🎬",
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

### 🔧 [Media Pipeline](media-pipeline)
**Pipeline Status Management**
- Search media items by hash or title
- View and update pipeline status (`ingested`, `parsed`, `rejected`, `downloading`, `complete`, etc.)
- Manage error conditions and rejection status
- Comprehensive debugging and API call visibility
- Color-coded status indicators with icons

### 📚 [Training Backlog](training-backlog)
**Movie Review Interface**
- Review unreviewed movies from the training dataset
- Binary classification: `would_watch` vs `would_not_watch`
- Display movie metadata (RT score, IMDB votes, genre)
- Expandable details with comprehensive movie information
- Auto-refresh after each review decision

### 🔍 [Prediction Anomalies](prediction-anomalies)
**ML Prediction Analysis**
- Review model predictions with filter by confusion matrix values
- Analyze false positives and false negatives
- Update labels for mispredicted items
- Display prediction probability and actual vs predicted labels
- Filter by: All, False Positives, False Negatives, True Positives, True Negatives

### 🔎 [Training Search](training-search)
**Search and Review Training Data**
- Search movies by title or IMDB ID
- View complete training data with all metadata
- Update labels (`would_watch` vs `would_not_watch`)
- Toggle anomalous status for items
- Similar interface to Prediction Anomalies page

### 🎬 [Media Library](get-media)
**Media Collection Browser**
- Browse complete media collection with pagination
- View detailed metadata for movies and TV shows
- Pipeline status tracking and error monitoring
- Search and filter capabilities
- Color-coded status indicators

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