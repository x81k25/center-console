import streamlit as st

st.set_page_config(page_title="button-test", layout="wide")

# Version tracker
VERSION = 12

# Initialize session state for boolean variables
if 'button1_state' not in st.session_state:
    st.session_state.button1_state = False
if 'button2_state' not in st.session_state:
    st.session_state.button2_state = True
if 'button3_state' not in st.session_state:
    st.session_state.button3_state = True

# Dynamic CSS based on button states
st.markdown(f"""
<style>
/* Button 1 - Blue */
div[data-testid="stHorizontalBlock"] > div:nth-child(1) button[kind="primary"] {{
    background-color: #1f77b4 !important;
    color: white !important;
    border-color: #1f77b4 !important;
}}
div[data-testid="stHorizontalBlock"] > div:nth-child(1) button[kind="secondary"] {{
    background-color: #2d2d2d !important;
    color: #1f77b4 !important;
    border-color: #1f77b4 !important;
}}

/* Button 2 - Red */
div[data-testid="stHorizontalBlock"] > div:nth-child(2) button[kind="primary"] {{
    background-color: #d62728 !important;
    color: white !important;
    border-color: #d62728 !important;
}}
div[data-testid="stHorizontalBlock"] > div:nth-child(2) button[kind="secondary"] {{
    background-color: #2d2d2d !important;
    color: #d62728 !important;
    border-color: #d62728 !important;
}}

/* Button 3 - Green */
div[data-testid="stHorizontalBlock"] > div:nth-child(3) button[kind="primary"] {{
    background-color: #2ca02c !important;
    color: white !important;
    border-color: #2ca02c !important;
}}
div[data-testid="stHorizontalBlock"] > div:nth-child(3) button[kind="secondary"] {{
    background-color: #2d2d2d !important;
    color: #2ca02c !important;
    border-color: #2ca02c !important;
}}
</style>
""", unsafe_allow_html=True)

st.title(f"Button Test Page - Version {VERSION}")

col1, col2, col3 = st.columns(3)

with col1:
    btn1_type = "primary" if st.session_state.button1_state else "secondary"
    if st.button("Button 1", key="btn1", type=btn1_type):
        st.session_state.button1_state = not st.session_state.button1_state
        st.rerun()
    st.write(f"Button 1 state: {st.session_state.button1_state}")

with col2:
    btn2_type = "primary" if st.session_state.button2_state else "secondary"
    if st.button("Button 2", key="btn2", type=btn2_type):
        st.session_state.button2_state = not st.session_state.button2_state
        st.rerun()
    st.write(f"Button 2 state: {st.session_state.button2_state}")

with col3:
    btn3_type = "primary" if st.session_state.button3_state else "secondary"
    if st.button("Button 3", key="btn3", type=btn3_type):
        st.session_state.button3_state = not st.session_state.button3_state
        st.rerun()
    st.write(f"Button 3 state: {st.session_state.button3_state}")