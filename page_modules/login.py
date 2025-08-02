import streamlit as st
from datetime import datetime
from core.auth import login_user

def show_login_page():
    """Display the login page"""
    st.title("🔐 Login")
    
    with st.form("login_form"):
        st.markdown("### Please enter your credentials")
        
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        submit_button = st.form_submit_button("Login", use_container_width=True)
        
        if submit_button:
            if not username or not password:
                st.error("Please enter both username and password")
            else:
                with st.spinner("Logging in..."):
                    result = login_user(username, password)
                    
                    if result["success"]:
                        user_data = result["user"]
                        st.session_state.user_id = user_data["id"]
                        st.session_state.username = user_data["username"]
                        st.session_state.is_admin = user_data.get("is_admin", False)
                        st.session_state.login_time = datetime.now()
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error(f"Login failed: {result['error']}")
    
    st.markdown("---")
    st.markdown("Don't have an account? Switch to **Register** in the sidebar.")
