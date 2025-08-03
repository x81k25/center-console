import streamlit as st
from datetime import datetime

st.set_page_config(page_title="changelog", layout="wide")

st.title("Changelog")

st.markdown("---")

# August 3, 2025
st.subheader("August 3, 2025")

st.markdown("""
### 🆕 New Features
- **Training Search Page**: Added new page for searching and reviewing training data
  - Search movies by title or IMDB ID
  - Real-time search - results update as you type (no search button needed)
  - Shows top 10 results sorted by most recently updated
  - View complete training data with all metadata (ratings, votes, genre, etc.)
  - Update labels (`would_watch` vs `would_not_watch`)
  - Toggle anomalous status for items
  - Interface similar to Training Backlog page with expandable details
  - Dynamic button styling with active/inactive states
  - Now uses the `/rear-diff/training` endpoint with native title search support
  
### 🔧 Prediction Anomalies Page - API Migration
- **Migrated to Movies Endpoint**: Transitioned from prediction and training endpoints to the unified `/rear-diff/movies/` endpoint
  - Single API call now fetches all necessary data (training + prediction information combined)
  - Improved performance by eliminating redundant API calls
  - Maintains all existing filtering capabilities (cm_value, anomalous, etc.)
- **Simplified Data Flow**: Removed complex data merging logic since movies endpoint provides unified data structure
- **Enhanced Load More Functionality**: Updated pagination to work correctly with new endpoint
- **Preserved Training Updates**: All PATCH operations to training endpoint remain unchanged as requested

### 🐛 Bug Fixes
- **Fixed Load More Button**: Resolved pagination issues when loading additional results
- **Improved Filter Handling**: Better state management for filters during pagination
""")

st.markdown("---")

# August 2, 2025
st.subheader("August 2, 2025")

st.markdown("""
### 🎨 UI/UX Improvements
- **Dynamic Button Styling**: Implemented new button styling system across all pages
  - Active buttons: Colored background with white text
  - Inactive buttons: Dark gray background with colored text and colored border
  - Applied to `would_watch`, `would_not_watch`, and `anomalous` buttons

### 🔧 Prediction Anomalies Page
- **Added Anomalous Filter**: New dropdown to filter by anomalous status (any/true/false)
- **Updated Confusion Matrix Filter**: Changed label from "Filter by Prediction Type" to "Filter by Confusion Matrix Value"
- **Removed Caching**: All interactions now fetch fresh data from API
- **Enhanced API Integration**: Anomalous filter now applied directly to prediction API calls
- **Removed Filter Description**: Cleaned up UI by removing redundant filter explanation section

### 🔧 Training Backlog Page
- **Updated Button Styling**: Applied new dynamic button styling system to `would_watch` and `would_not_watch` buttons

### 🗑️ Cleanup
- **Removed Test Page**: Deleted button-test page after implementing styling across production pages

### 🔍 Debug Improvements
- **Enhanced API Call Display**: Debug URL now shows all active filter parameters including anomalous filter

### 🐛 Bug Fixes
- **Fixed Anomalous Filter**: Resolved "No training data found" errors when anomalous filter is applied
- **Fixed Anomalous Filter Display**: Now only displays IMDB IDs that actually match the anomalous filter criteria
- **Fixed Empty Elements**: Eliminated empty prediction elements when anomalous filter reduces available training data
- **Fixed Element Count**: Removed duplicate anomalous filtering to display correct number of items based on prediction API results
""")

st.markdown("---")
st.caption("Changes are listed in reverse chronological order (newest first)")