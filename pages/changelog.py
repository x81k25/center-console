import streamlit as st
from datetime import datetime

st.set_page_config(page_title="changelog", layout="wide")

st.title("Changelog")

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
""")

st.markdown("---")
st.caption("Changes are listed in reverse chronological order (newest first)")