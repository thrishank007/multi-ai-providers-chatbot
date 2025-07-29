import streamlit as st
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stSidebar > div {
        padding-top: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .token-counter {
        background-color: #fff3e0;
        padding: 0.5rem;
        border-radius: 0.25rem;
        border: 1px solid #ffb74d;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Check if user is logged in
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    
    if 'username' not in st.session_state:
        st.session_state.username = None
    
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False
    
    if 'login_time' not in st.session_state:
        st.session_state.login_time = None
    
    # Check session timeout
    if st.session_state.user_id and st.session_state.login_time:
        timeout_minutes = int(os.getenv('SESSION_TIMEOUT_MINUTES', 30))
        if datetime.now() - st.session_state.login_time > timedelta(minutes=timeout_minutes):
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.is_admin = False
            st.session_state.login_time = None
            st.warning("Session expired. Please log in again.")
    
    # Navigation
    if st.session_state.user_id is None:
        # User not logged in
        page = st.sidebar.selectbox("Navigation", ["Login", "Register"])
        
        if page == "Login":
            from pages.login import show_login_page
            show_login_page()
        elif page == "Register":
            from pages.register import show_register_page
            show_register_page()
    else:
        # User logged in
        st.sidebar.success(f"Welcome, {st.session_state.username}!")
        
        # Check if user is admin
        from core.auth import is_admin
        if is_admin(st.session_state.user_id):
            page = st.sidebar.selectbox("Navigation", ["Chat", "Admin Dashboard", "Logout"])
        else:
            page = st.sidebar.selectbox("Navigation", ["Chat", "Logout"])
        
        if page == "Chat":
            from pages.chat import show_chat_page
            show_chat_page()
        elif page == "Admin Dashboard":
            from pages.admin import show_admin_page
            show_admin_page()
        elif page == "Logout":
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.is_admin = False
            st.session_state.login_time = None
            if 'history' in st.session_state:
                del st.session_state.history
            st.rerun()

if __name__ == "__main__":
    main()
