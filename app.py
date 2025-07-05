import streamlit as st

st.set_page_config(
    page_title="Center Console",
    page_icon="🎬",
    layout="wide"
)

st.markdown("""
# 🎬 Center Console

Welcome to the Center Console application for managing the Rear Differential media processing pipeline.

## 📋 Available Pages

Select a page from the sidebar to get started, or click the links below:

### 🔧 [Media Pipeline](media-pipeline)
**Pipeline Status Management**
- Search media items by hash or title
- View and update pipeline status (ingested, parsed, rejected, downloading, complete, etc.)
- Manage error conditions and rejection status
- Comprehensive debugging and API call visibility
- Color-coded status indicators with icons

### 📚 [Training Backlog](training_backlog)
**Movie Review Interface**
- Review unreviewed movies from the training dataset
- Binary classification: "would_watch" vs "would_not_watch"
- Display movie metadata (RT score, IMDB votes, genre)
- Expandable details with comprehensive movie information
- Auto-refresh after each review decision

### 🎬 [Media Library](get_media)
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
""")