import tiktoken
from typing import List, Dict, Any
import re

class TokenCounter:
    """Token counting utilities for different providers"""
    
    def __init__(self):
        # Token pricing per 1K tokens (approximate)
        self.pricing = {
            "OpenAI": {
                "gpt-4": {"input": 0.03, "output": 0.06},
                "gpt-4-turbo": {"input": 0.01, "output": 0.03},
                "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
                "gpt-3.5-turbo-16k": {"input": 0.003, "output": 0.004}
            },
            "Anthropic": {
                "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
                "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
                "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125}
            },
            "Gemini": {
                "gemini-pro": {"input": 0.0005, "output": 0.0015},
                "gemini-pro-vision": {"input": 0.0005, "output": 0.0015}
            }
        }
    
    def count_tokens(self, provider: str, model: str, text: str) -> int:
        """Count tokens in text for specific provider/model"""
        if provider == "OpenAI":
            return self._count_openai_tokens(model, text)
        elif provider == "Anthropic":
            return self._count_anthropic_tokens(text)
        elif provider == "Gemini":
            return self._count_gemini_tokens(text)
        else:
            return len(text.split())  # Fallback word count
    
    def count_messages_tokens(self, provider: str, model: str, messages: List[Dict[str, str]]) -> int:
        """Count total tokens in message list"""
        total_tokens = 0
        
        for message in messages:
            content = message.get("content", "")
            role = message.get("role", "")
            
            # Count content tokens
            total_tokens += self.count_tokens(provider, model, content)
            
            # Add overhead for role and formatting (approximate)
            total_tokens += 4  # For role and message formatting
        
        # Add conversation overhead
        total_tokens += 3
        
        return total_tokens
    
    def _count_openai_tokens(self, model: str, text: str) -> int:
        """Count tokens using tiktoken for OpenAI models"""
        try:
            if "gpt-4" in model:
                encoding = tiktoken.encoding_for_model("gpt-4")
            elif "gpt-3.5-turbo" in model:
                encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            else:
                encoding = tiktoken.get_encoding("cl100k_base")
            
            return len(encoding.encode(text))
        except Exception:
            # Fallback estimation
            return len(text.split()) * 1.3
    
    def _count_anthropic_tokens(self, text: str) -> int:
        """Estimate tokens for Anthropic (Claude) models"""
        # Claude uses a similar tokenization to GPT models
        # Approximate: 1 token ≈ 4 characters for English text
        return int(len(text) / 4)
    
    def _count_gemini_tokens(self, text: str) -> int:
        """Estimate tokens for Gemini models"""
        # Approximate tokenization for Gemini
        # Similar to other models: roughly 1 token per 4 characters
        return int(len(text) / 4)
    
    def estimate_cost(self, provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost based on token usage"""
        try:
            model_pricing = self.pricing.get(provider, {}).get(model, {})
            if not model_pricing:
                return 0.0
            
            input_cost = (input_tokens / 1000) * model_pricing.get("input", 0)
            output_cost = (output_tokens / 1000) * model_pricing.get("output", 0)
            
            return input_cost + output_cost
        except Exception:
            return 0.0
    
    def get_token_info(self, provider: str, model: str, messages: List[Dict[str, str]], 
                      response_text: str = "") -> Dict[str, Any]:
        """Get comprehensive token information"""
        input_tokens = self.count_messages_tokens(provider, model, messages)
        output_tokens = self.count_tokens(provider, model, response_text) if response_text else 0
        total_tokens = input_tokens + output_tokens
        estimated_cost = self.estimate_cost(provider, model, input_tokens, output_tokens)
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "estimated_cost": estimated_cost,
            "provider": provider,
            "model": model
        }
