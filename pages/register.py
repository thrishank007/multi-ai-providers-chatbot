import streamlit as st
from core.auth import register_user

def show_register_page():
    """Display the registration page"""
    st.title("📝 Register")
    
    with st.form("register_form"):
        st.markdown("### Create a new account")
        
        username = st.text_input("Username", placeholder="Choose a username")
        email = st.text_input("Email (optional)", placeholder="Enter your email")
        password = st.text_input("Password", type="password", placeholder="Choose a password")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
        
        submit_button = st.form_submit_button("Register", use_container_width=True)
        
        if submit_button:
            # Validation
            if not username or not password:
                st.error("Username and password are required")
                return
            
            if len(username) < 3:
                st.error("Username must be at least 3 characters long")
                return
            
            if len(password) < 6:
                st.error("Password must be at least 6 characters long")
                return
            
            if password != confirm_password:
                st.error("Passwords do not match")
                return
            
            with st.spinner("Creating account..."):
                email_value = email.strip() if email and email.strip() else ""
                result = register_user(username, email_value, password)
                
                if result["success"]:
                    st.success("Account created successfully! Please login.")
                    st.balloons()
                else:
                    st.error(f"Registration failed: {result['error']}")
    
    st.markdown("---")
    st.markdown("Already have an account? Switch to **Login** in the sidebar.")
