import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from supabase import create_client, Client

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

def show_admin_page():
    """Display the admin dashboard"""
    st.title("👑 Admin Dashboard")
    
    # Check if user is admin
    from core.auth import is_admin
    if not is_admin(st.session_state.user_id):
        st.error("Access denied. Admin privileges required.")
        return
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        days_back = st.selectbox("Time Period", [7, 30, 90, 365], index=1)
    with col2:
        auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)
    
    if auto_refresh:
        st.rerun()
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # Fetch analytics data
    try:
        analytics_data = supabase.table('analytics')\
            .select('*')\
            .gte('created_at', start_date.isoformat())\
            .lte('created_at', end_date.isoformat())\
            .execute()
        
        users_data = supabase.table('users')\
            .select('id, username, email, is_admin, created_at')\
            .execute()
        
        df_analytics = pd.DataFrame(analytics_data.data) if analytics_data.data else pd.DataFrame()
        df_users = pd.DataFrame(users_data.data) if users_data.data else pd.DataFrame()
        
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return
    
    # Overview metrics
    st.subheader("📊 Overview")
    
    if not df_analytics.empty:
        total_requests = len(df_analytics)
        total_tokens = df_analytics['total_tokens'].sum()
        total_cost = df_analytics['estimated_cost'].sum()
        unique_users = df_analytics['user_id'].nunique()
    else:
        total_requests = total_tokens = total_cost = unique_users = 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Requests", f"{total_requests:,}")
    with col2:
        st.metric("Total Tokens", f"{total_tokens:,}")
    with col3:
        st.metric("Estimated Cost", f"${total_cost:.2f}")
    with col4:
        st.metric("Active Users", unique_users)
    
    if df_analytics.empty:
        st.info("No analytics data available for the selected time period.")
        return
    
    # Daily activity chart
    st.subheader("📈 Daily Activity")
    
    df_analytics['date'] = pd.to_datetime(df_analytics['created_at']).dt.date
    daily_stats = df_analytics.groupby('date').agg({
        'id': 'count',
        'total_tokens': 'sum',
        'estimated_cost': 'sum'
    }).rename(columns={'id': 'requests'}).reset_index()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_requests = px.line(
            daily_stats, 
            x='date', 
            y='requests',
            title='Daily Requests',
            markers=True
        )
        fig_requests.update_layout(height=400)
        st.plotly_chart(fig_requests, use_container_width=True)
    
    with col2:
        fig_tokens = px.line(
            daily_stats, 
            x='date', 
            y='total_tokens',
            title='Daily Token Usage',
            markers=True
        )
        fig_tokens.update_layout(height=400)
        st.plotly_chart(fig_tokens, use_container_width=True)
    
    # Provider and model distribution
    st.subheader("🔍 Usage Distribution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        provider_stats = df_analytics.groupby('provider').agg({
            'id': 'count',
            'total_tokens': 'sum'
        }).rename(columns={'id': 'requests'}).reset_index()
        
        fig_providers = px.pie(
            provider_stats, 
            values='requests', 
            names='provider',
            title='Requests by Provider'
        )
        st.plotly_chart(fig_providers, use_container_width=True)
    
    with col2:
        model_stats = df_analytics.groupby('model').agg({
            'id': 'count',
            'total_tokens': 'sum'
        }).rename(columns={'id': 'requests'}).reset_index()
        
        # Top 10 models
        top_models = model_stats.nlargest(10, 'requests')
        
        fig_models = px.bar(
            top_models, 
            x='requests', 
            y='model',
            title='Top 10 Models by Requests',
            orientation='h'
        )
        fig_models.update_layout(height=400)
        st.plotly_chart(fig_models, use_container_width=True)
    
    # User activity
    st.subheader("👥 User Activity")
    
    user_stats = df_analytics.groupby('user_id').agg({
        'id': 'count',
        'total_tokens': 'sum',
        'estimated_cost': 'sum'
    }).rename(columns={'id': 'requests'}).reset_index()
    
    # Merge with user info
    if not df_users.empty:
        user_stats = user_stats.merge(
            df_users[['id', 'username']], 
            left_on='user_id', 
            right_on='id',
            how='left'
        )
        user_stats['username'] = user_stats['username'].fillna('Unknown')
    else:
        user_stats['username'] = 'Unknown'
    
    # Top users table
    st.write("**Top Users by Activity**")
    top_users = user_stats.nlargest(20, 'requests')[['username', 'requests', 'total_tokens', 'estimated_cost']]
    top_users['estimated_cost'] = top_users['estimated_cost'].round(4)
    st.dataframe(top_users, use_container_width=True)
    
    # User list management
    st.subheader("👤 User Management")
    
    if not df_users.empty:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write("**All Users**")
            user_display = df_users[['username', 'email', 'is_admin', 'created_at']].copy()
            user_display['created_at'] = pd.to_datetime(user_display['created_at']).dt.strftime('%Y-%m-%d')
            st.dataframe(user_display, use_container_width=True)
        
        with col2:
            st.write("**User Statistics**")
            total_users = len(df_users)
            admin_users = df_users['is_admin'].sum()
            recent_users = len(df_users[pd.to_datetime(df_users['created_at']) > (datetime.now() - timedelta(days=7))])
            
            st.metric("Total Users", total_users)
            st.metric("Admin Users", admin_users)
            st.metric("New Users (7 days)", recent_users)
    
    # Recent activity log
    st.subheader("📋 Recent Activity")
    
    recent_activity = df_analytics.nlargest(50, 'created_at')
    if not recent_activity.empty and not df_users.empty:
        recent_activity = recent_activity.merge(
            df_users[['id', 'username']], 
            left_on='user_id', 
            right_on='id',
            how='left'
        )
        recent_activity['username'] = recent_activity['username'].fillna('Unknown')
        
        activity_display = recent_activity[[
            'username', 'provider', 'model', 'total_tokens', 'estimated_cost', 'created_at'
        ]].copy()
        activity_display['created_at'] = pd.to_datetime(activity_display['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
        activity_display['estimated_cost'] = activity_display['estimated_cost'].round(4)
        
        st.dataframe(activity_display, use_container_width=True)
    
    # Auto-refresh
    if auto_refresh:
        import time
        time.sleep(30)
        st.rerun()
