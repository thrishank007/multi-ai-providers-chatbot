"""
Authentication module for user management
"""
import bcrypt
import os
from typing import Optional, Dict, Any
from supabase import create_client, Client

def get_supabase_client() -> Client:
    """Get Supabase client with lazy initialization"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("Supabase URL and key must be set in environment variables")
    
    return create_client(supabase_url, supabase_key)

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    if not password:
        raise ValueError("Password cannot be empty")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    if not password or not hashed:
        return False
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def register_user(username: str, email: str, password: str) -> Dict[str, Any]:
    """Register a new user"""
    try:
        # Validate input parameters
        if not username or not username.strip():
            return {"success": False, "error": "Username is required"}
        
        if not password or not password.strip():
            return {"success": False, "error": "Password is required"}
        
        if len(password.strip()) < 6:
            return {"success": False, "error": "Password must be at least 6 characters long"}
        
        # Clean up inputs
        username = username.strip()
        email = email.strip() if email else ""
        password = password.strip()
        
        supabase = get_supabase_client()
        
        # Check if username already exists
        existing = supabase.table("users").select("username").eq("username", username).execute()
        if existing.data:
            return {"success": False, "error": "Username already exists"}
        
        # Hash password
        password_hash = hash_password(password)
        
        # Insert user
        result = supabase.table("users").insert({
            "username": username,
            "email": email,
            "password_hash": password_hash
        }).execute()
        
        if result.data:
            return {"success": True, "user": result.data[0]}
        else:
            return {"success": False, "error": "Failed to create user"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def login_user(username: str, password: str) -> Dict[str, Any]:
    """Login user and return user data if successful"""
    try:
        # Validate input parameters
        if not username or not username.strip():
            return {"success": False, "error": "Username is required"}
        
        if not password or not password.strip():
            return {"success": False, "error": "Password is required"}
        
        # Clean up inputs
        username = username.strip()
        password = password.strip()
        
        supabase = get_supabase_client()
        
        # Get user by username
        result = supabase.table("users").select("*").eq("username", username).execute()
        
        if not result.data:
            return {"success": False, "error": "User not found"}
        
        user = result.data[0]
        
        # Verify password
        if verify_password(password, user["password_hash"]):
            # Remove password hash from returned data
            user_data = {k: v for k, v in user.items() if k != "password_hash"}
            return {"success": True, "user": user_data}
        else:
            return {"success": False, "error": "Invalid password"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by ID"""
    try:
        supabase = get_supabase_client()
        result = supabase.table("users").select("*").eq("id", user_id).execute()
        
        if result.data:
            user = result.data[0]
            # Remove password hash
            return {k: v for k, v in user.items() if k != "password_hash"}
        return None
        
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

def is_admin(user_id: str) -> bool:
    """Check if user is admin"""
    try:
        supabase = get_supabase_client()
        result = supabase.table("users").select("is_admin").eq("id", user_id).execute()
        
        if result.data:
            return result.data[0].get("is_admin", False)
        return False
        
    except Exception as e:
        print(f"Error checking admin status: {e}")
        return False

def get_all_users() -> list:
    """Get all users (admin only)"""
    try:
        supabase = get_supabase_client()
        result = supabase.table("users").select("id, username, email, is_admin, created_at").execute()
        return result.data or []
        
    except Exception as e:
        print(f"Error getting all users: {e}")
        return []