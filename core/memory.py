"""
Memory management using pgvector for conversation context
"""
import os
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client

def get_supabase_client() -> Client:
    """Get Supabase client with lazy initialization"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("Supabase URL and key must be set in environment variables")
    
    return create_client(supabase_url, supabase_key)

class MemoryManager:
    def __init__(self):
        """Initialize the memory manager with embedding model"""
        model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.embedding_model = SentenceTransformer(model_name)
    
    def add_message(self, user_id: str, role: str, content: str, conversation_id: str) -> bool:
        """Add a message to memory with embedding"""
        try:
            supabase = get_supabase_client()
            
            # Generate embedding
            embedding = self.embedding_model.encode(content).tolist()
            
            # Store in database
            result = supabase.table("memory_vectors").insert({
                "user_id": user_id,
                "role": role,
                "content": content,
                "conversation_id": conversation_id,
                "embedding": embedding
            }).execute()
            
            return bool(result.data)
            
        except Exception as e:
            print(f"Error adding message to memory: {e}")
            return False
    
    def recall(self, user_id: str, query: str, k: int = 4, conversation_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Recall relevant context using vector similarity"""
        try:
            supabase = get_supabase_client()
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Use the RPC function for similarity search
            result = supabase.rpc("match_memory_vectors", {
                "query_embedding": query_embedding,
                "match_threshold": 0.7,
                "match_count": k,
                "p_user_id": user_id,
                "p_conversation_id": conversation_id
            }).execute()
            
            return result.data or []
            
        except Exception as e:
            print(f"Error recalling context: {e}")
            return []
    
    def get_conversation_messages(self, user_id: str, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent messages from a conversation"""
        try:
            supabase = get_supabase_client()
            
            result = supabase.table("memory_vectors")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("conversation_id", conversation_id)\
                .order("created_at", desc=False)\
                .limit(limit)\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            print(f"Error getting conversation messages: {e}")
            return []
    
    def delete_conversation(self, user_id: str, conversation_id: str) -> bool:
        """Delete all messages from a conversation"""
        try:
            supabase = get_supabase_client()
            
            result = supabase.table("memory_vectors")\
                .delete()\
                .eq("user_id", user_id)\
                .eq("conversation_id", conversation_id)\
                .execute()
            
            return True
            
        except Exception as e:
            print(f"Error deleting conversation: {e}")
            return False
    
    def summarize_conversation(self, user_id: str, conversation_id: str, summary: str, message_count: int) -> bool:
        """Store conversation summary"""
        try:
            supabase = get_supabase_client()
            
            result = supabase.table("summaries").insert({
                "user_id": user_id,
                "conversation_id": conversation_id,
                "summary": summary,
                "messages_count": message_count
            }).execute()
            
            return bool(result.data)
            
        except Exception as e:
            print(f"Error storing summary: {e}")
            return False
    
    def get_user_conversations(self, user_id: str) -> List[str]:
        """Get list of conversation IDs for a user"""
        try:
            supabase = get_supabase_client()
            
            result = supabase.table("memory_vectors")\
                .select("conversation_id")\
                .eq("user_id", user_id)\
                .execute()
            
            # Get unique conversation IDs
            conversation_ids = list(set(item["conversation_id"] for item in result.data if item.get("conversation_id")))
            return conversation_ids
            
        except Exception as e:
            print(f"Error getting user conversations: {e}")
            return []
    
    def count_messages(self, user_id: str, conversation_id: str) -> int:
        """Count messages in a conversation"""
        try:
            supabase = get_supabase_client()
            
            result = supabase.table("memory_vectors")\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .eq("conversation_id", conversation_id)\
                .execute()
            
            return result.count if result.count else 0
            
        except Exception as e:
            print(f"Error counting messages: {e}")
            return 0
    
    def summarize_and_prune(self, user_id: str, conversation_id: str, llm_bridge, provider: str, model: str, api_key: str) -> bool:
        """Summarize old messages and prune vectors"""
        try:
            supabase = get_supabase_client()
            if not supabase:
                return False
            
            # Get messages older than last 10
            messages = self.get_conversation_messages(user_id, conversation_id, limit=100)
            
            if len(messages) < 20:
                return False
            
            # Take messages except the last 10
            messages_to_summarize = messages[:-10]
            
            # Create summary prompt
            conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages_to_summarize])
            summary_prompt = f"Please provide a concise summary of the following conversation:\n\n{conversation_text}"
            
            # Generate summary using LLM
            summary_messages = [{"role": "user", "content": summary_prompt}]
            response = llm_bridge.chat(provider, model, api_key, summary_messages, temperature=0.3, max_tokens=500)
            summary = llm_bridge.extract_content(provider, response)
            
            # Store summary
            self.summarize_conversation(user_id, conversation_id, summary, len(messages_to_summarize))
            
            # Delete old vectors (keep last 10 messages)
            if len(messages_to_summarize) > 0:
                oldest_timestamp = messages_to_summarize[-1]['created_at']
                supabase.table("memory_vectors")\
                    .delete()\
                    .eq("user_id", user_id)\
                    .eq("conversation_id", conversation_id)\
                    .lte("created_at", oldest_timestamp)\
                    .execute()
            
            return True
            
        except Exception as e:
            print(f"Error in summarize_and_prune: {e}")
            return False