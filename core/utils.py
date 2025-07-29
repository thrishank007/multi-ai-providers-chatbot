import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import os
from supabase import create_client, Client

def get_supabase_client():
    """Get Supabase client with lazy initialization"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        # Return None if credentials not available (for testing)
        return None
    
    return create_client(supabase_url, supabase_key)

def generate_conversation_id() -> str:
    """Generate a unique conversation ID"""
    return str(uuid.uuid4())

def format_chat_history_for_export(history: List[Dict[str, Any]], format_type: str = "json") -> str:
    """Format chat history for export"""
    if format_type == "json":
        return json.dumps(history, indent=2, ensure_ascii=False)
    elif format_type == "md":
        md_content = "# Chat History\n\n"
        md_content += f"*Exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        
        for message in history:
            role = message.get("role", "").title()
            content = message.get("content", "")
            timestamp = message.get("timestamp", "")
            
            md_content += f"## {role}\n"
            if timestamp:
                md_content += f"*{timestamp}*\n\n"
            md_content += f"{content}\n\n---\n\n"
        
        return md_content
    else:
        return str(history)

def log_analytics(user_id: int, provider: str, model: str, prompt_tokens: int, 
                 completion_tokens: int, estimated_cost: float, conversation_id: Optional[str] = None) -> bool:
    """Log analytics data to Supabase"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        data = {
            'user_id': user_id,
            'provider': provider,
            'model': model,
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'total_tokens': prompt_tokens + completion_tokens,
            'estimated_cost': estimated_cost,
            'conversation_id': conversation_id,
            'timestamp': datetime.now().isoformat(),
            'created_at': 'now()'
        }
        
        result = supabase.table('analytics').insert(data).execute()
        return len(result.data) > 0
        
    except Exception as e:
        print(f"Error logging analytics: {e}")
        return False

def get_user_stats(user_id: int, days: int = 30) -> Dict[str, Any]:
    """Get user statistics for the last N days"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return {
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "favorite_provider": "None",
                "favorite_model": "None"
            }
        
        # Calculate date threshold
        from datetime import timedelta
        threshold_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Get user analytics
        result = supabase.table('analytics')\
            .select('*')\
            .eq('user_id', user_id)\
            .gte('created_at', threshold_date)\
            .execute()
        
        if not result.data:
            return {
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "favorite_provider": "None",
                "favorite_model": "None"
            }
        
        data = result.data
        
        # Calculate statistics
        total_requests = len(data)
        total_tokens = sum(row['total_tokens'] for row in data)
        total_cost = sum(row['estimated_cost'] for row in data)
        
        # Find favorite provider and model
        providers = {}
        models = {}
        
        for row in data:
            provider = row['provider']
            model = row['model']
            
            providers[provider] = providers.get(provider, 0) + 1
            models[model] = models.get(model, 0) + 1
        
        favorite_provider = max(providers.items(), key=lambda x: x[1])[0] if providers else "None"
        favorite_model = max(models.items(), key=lambda x: x[1])[0] if models else "None"
        
        return {
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "total_cost": round(total_cost, 4),
            "favorite_provider": favorite_provider,
            "favorite_model": favorite_model
        }
        
    except Exception as e:
        print(f"Error getting user stats: {e}")
        return {
            "total_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "favorite_provider": "None",
            "favorite_model": "None"
        }

def validate_api_key(provider: str, api_key: str) -> bool:
    """Basic API key validation"""
    if not api_key or len(api_key.strip()) < 10:
        return False
    
    if provider == "OpenAI":
        return api_key.startswith("sk-")
    elif provider == "Anthropic":
        return api_key.startswith("sk-ant-")
    elif provider == "Gemini":
        return len(api_key) > 20  # Basic length check
    
    return True

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for export"""
    import re
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple underscores
    filename = re.sub(r'_+', '_', filename)
    # Remove leading/trailing underscores
    filename = filename.strip('_')
    
    return filename if filename else "chat_export"
