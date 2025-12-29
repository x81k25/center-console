import streamlit as st
import requests
import pandas as pd
from config import Config
from typing import Dict, List, Optional
import time

st.set_page_config(
    page_title="get-flyway-migrations",
    page_icon="./favicon/android-chrome-192x192.png",
    layout="wide"
)

# Custom CSS for styling
st.markdown("""
<style>
/* Success status */
.status-success { color: #28a745; font-weight: bold; }
.status-failed { color: #dc3545; font-weight: bold; }

/* Migration type styling */
.migration-type-sql { 
    background-color: #e7f3ff; 
    color: #0056b3; 
    padding: 2px 6px; 
    border-radius: 3px; 
    font-size: 0.8em; 
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

def fetch_flyway_data(config: Config, sort_by: str = "version", sort_order: str = "desc") -> Optional[Dict]:
    """Fetch flyway migration data from the API"""
    try:
        params = {
            "sort_by": sort_by,
            "sort_order": sort_order
        }
        
        response = requests.get(
            config.flyway_endpoint,
            params=params,
            timeout=config.api_timeout
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch flyway data: {str(e)}")
        return None

def format_execution_time(execution_time: int) -> str:
    """Format execution time in a human-readable format"""
    if execution_time < 1000:
        return f"{execution_time}ms"
    else:
        return f"{execution_time/1000:.1f}s"

def format_installed_on(installed_on: str) -> str:
    """Format the installed_on timestamp"""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(installed_on.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return installed_on

def main():
    """Main application function"""
    try:
        config = Config()
    except ValueError as e:
        st.error(f"Configuration Error: {str(e)}")
        st.info("Please set the required environment variables: REAR_DIFF_HOST, REAR_DIFF_PORT_EXTERNAL")
        return
    
    st.title("get-flyway-migrations")
    
    # Add sorting controls
    col1, col2, col3 = st.columns([2, 2, 6])
    with col1:
        sort_by = st.selectbox(
            "Sort by", 
            ["version", "installed_rank", "installed_on"], 
            index=0
        )
    with col2:
        sort_order = st.selectbox(
            "Sort order", 
            ["desc", "asc"], 
            index=0
        )
    
    # Debug: Show API call with current parameters
    flyway_params = {
        "sort_by": sort_by,
        "sort_order": sort_order
    }
    param_string = "&".join([f"{k}={v}" for k, v in flyway_params.items()])
    api_url = f"{config.flyway_endpoint}?{param_string}"
    st.code(api_url, language="bash")
    
    data = fetch_flyway_data(config, sort_by=sort_by, sort_order=sort_order)
    
    if not data:
        return
    
    migrations = data.get("data", [])
    
    # Sort migrations client-side if sorting by version to ensure proper numerical order
    if sort_by == "version" and migrations:
        reverse = (sort_order == "desc")
        migrations.sort(key=lambda x: float(x.get('version', '0')), reverse=reverse)
    
    # Display metadata
    st.info(f"Total migrations: {len(migrations)}")
    
    if not migrations:
        st.info("No migrations found")
        return
    
    # Display each migration
    for idx, migration in enumerate(migrations):
        with st.container():
            # Main row with migration info
            col1, col2, col3, col4, col5, col6 = st.columns([1, 3, 1.5, 1.5, 1.5, 1])
            
            with col1:
                st.write(f"**V{migration.get('version', 'N/A')}**")
                st.caption(f"Rank: {migration.get('installed_rank', 'N/A')}")
            
            with col2:
                st.write(f"**{migration.get('description', 'No description')}**")
                st.caption(f"Script: {migration.get('script', 'N/A')}")
            
            with col3:
                migration_type = migration.get('type', 'UNKNOWN')
                st.markdown(f'<span class="migration-type-sql">{migration_type}</span>', unsafe_allow_html=True)
                st.caption("Type")
            
            with col4:
                installed_on = format_installed_on(migration.get('installed_on', ''))
                st.write(installed_on)
                st.caption("Installed On")
            
            with col5:
                installed_by = migration.get('installed_by', 'Unknown')
                st.write(f"**{installed_by}**")
                st.caption("Installed By")
            
            with col6:
                # Show success status
                success = migration.get('success', False)
                execution_time = migration.get('execution_time', 0)
                
                if success:
                    st.markdown('<span class="status-success">✅ SUCCESS</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="status-failed">❌ FAILED</span>', unsafe_allow_html=True)
                
                st.caption(f"Time: {format_execution_time(execution_time)}")
            
            # Expandable details section
            with st.expander(f"📋 Details for V{migration.get('version', 'N/A')}: {migration.get('description', 'No description')}", expanded=False):
                detail_col1, detail_col2 = st.columns(2)
                
                with detail_col1:
                    st.write("**Migration Info:**")
                    st.write(f"• **Version:** {migration.get('version', 'N/A')}")
                    st.write(f"• **Installed Rank:** {migration.get('installed_rank', 'N/A')}")
                    st.write(f"• **Description:** {migration.get('description', 'No description')}")
                    st.write(f"• **Type:** {migration.get('type', 'UNKNOWN')}")
                    st.write(f"• **Script:** {migration.get('script', 'N/A')}")
                    st.write(f"• **Success:** {'✅ Yes' if migration.get('success', False) else '❌ No'}")
                
                with detail_col2:
                    st.write("**Execution Details:**")
                    st.write(f"• **Installed By:** {migration.get('installed_by', 'Unknown')}")
                    st.write(f"• **Installed On:** {format_installed_on(migration.get('installed_on', ''))}")
                    st.write(f"• **Execution Time:** {format_execution_time(migration.get('execution_time', 0))}")
                    
                    checksum = migration.get('checksum')
                    if checksum is not None:
                        st.write(f"• **Checksum:** {checksum}")
                    else:
                        st.write("• **Checksum:** N/A")
            
            st.divider()

if __name__ == "__main__":
    main()