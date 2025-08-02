import tiktoken
from typing import List, Dict, Any
import re

class TokenCounter:
    """Token counting utilities for different providers"""
    
    def __init__(self):
        # Token pricing per 1K tokens (2025 pricing)
        self.pricing = {
            "OpenAI": {
                # 2025 OpenAI Model Pricing
                "gpt-4.1": {"input": 0.002, "output": 0.008},  # $2.00/$8.00 per 1M tokens
                "o3": {"input": 0.002, "output": 0.008},  # $2.00/$8.00 per 1M tokens  
                "gpt-4o": {"input": 0.005, "output": 0.015},  # $5.00/$15.00 per 1M tokens
                "o4-mini-deep-research": {"input": 0.0011, "output": 0.0044},  # $1.10/$4.40 per 1M tokens
                "gpt-4.1-mini": {"input": 0.0004, "output": 0.0016},  # $0.40/$1.60 per 1M tokens
                "gpt-4.1-nano": {"input": 0.0001, "output": 0.0004},  # $0.10/$0.40 per 1M tokens
                "o3-pro": {"input": 0.02, "output": 0.08},  # $20.00/$80.00 per 1M tokens
                # Legacy models for compatibility
                "gpt-4": {"input": 0.03, "output": 0.06},
                "gpt-4-turbo": {"input": 0.01, "output": 0.03},
                "gpt-3.5-turbo": {"input": 0.001, "output": 0.002}
            },
            "Anthropic": {
                # 2025 Anthropic Claude 4 Pricing
                "claude-sonnet-4-20250514": {"input": 0.003, "output": 0.015},  # $3.00/$15.00 per 1M tokens
                "claude-opus-4-20250514": {"input": 0.015, "output": 0.075},  # $15.00/$75.00 per 1M tokens
                # Legacy Claude 3 models for compatibility
                "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
                "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
                "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
                "claude-3-7-sonnet-20250219": {"input": 0.003, "output": 0.015},
                "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
                "claude-3-5-haiku-20241022": {"input": 0.001, "output": 0.005}
            },
            "Gemini": {
                # 2025 Google Gemini Pricing
                "gemini-2.5-pro": {"input": 0.00125, "output": 0.005},  # $1.25/$5.00 per 1M tokens
                "gemini-2.5-flash": {"input": 0.0003, "output": 0.0025},  # $0.30/$2.50 per 1M tokens
                "gemini-2.5-flash-lite": {"input": 0.0001, "output": 0.0004},  # $0.10/$0.40 per 1M tokens
                "gemini-2.0-flash": {"input": 0.0000375, "output": 0.00015},  # $0.0375/$0.15 per 1M tokens
                "gemini-2.0-flash-lite": {"input": 0.00001875, "output": 0.000075},  # $0.01875/$0.075 per 1M tokens
                # Legacy models for compatibility
                "gemini-pro": {"input": 0.0005, "output": 0.0015},
                "gemini-pro-vision": {"input": 0.0005, "output": 0.0015}
            }
        }
    
    def is_model_supported(self, provider: str, model: str) -> bool:
        """Check if a model is supported by the provider"""
        provider_models = self.pricing.get(provider, {})
        return model in provider_models
    
    def get_supported_models(self, provider: str) -> List[str]:
        """Get list of supported models for a provider"""
        return list(self.pricing.get(provider, {}).keys())
    
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
            model_lower = model.lower()
            
            # Use appropriate encoding for different model families
            if any(x in model_lower for x in ["gpt-4.1", "o3", "gpt-4o", "o4-mini"]):
                # New 2025 models use GPT-4 encoding
                encoding = tiktoken.encoding_for_model("gpt-4")
            elif "gpt-4" in model_lower:
                encoding = tiktoken.encoding_for_model("gpt-4")
            elif "gpt-3.5-turbo" in model_lower:
                encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            else:
                # Default to cl100k_base for unknown models
                encoding = tiktoken.get_encoding("cl100k_base")
            
            return len(encoding.encode(text))
        except Exception:
            # Fallback estimation: ~1.3 tokens per word for English text
            return int(len(text.split()) * 1.3)
    
    def _count_anthropic_tokens(self, text: str) -> int:
        """Estimate tokens for Anthropic (Claude) models"""
        # Claude models use a similar tokenization approach to GPT models
        # For 2025 Claude 4 models: approximately 1 token ≈ 3.5-4 characters for English text
        # Being slightly more conservative with 3.8 characters per token
        return max(1, int(len(text) / 3.8))
    
    def _count_gemini_tokens(self, text: str) -> int:
        """Estimate tokens for Gemini models"""
        # Gemini 2.5 and 2.0 models have similar tokenization to other modern LLMs
        # Approximately 1 token ≈ 3.5-4 characters for English text
        # Using 3.7 characters per token for better accuracy
        return max(1, int(len(text) / 3.7))
    
    def estimate_cost(self, provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost based on token usage"""
        try:
            provider_pricing = self.pricing.get(provider, {})
            
            # Try exact model match first
            model_pricing = provider_pricing.get(model, {})
            
            # If exact match not found, try fuzzy matching for common model patterns
            if not model_pricing:
                model_lower = model.lower()
                
                # OpenAI fuzzy matching
                if provider == "OpenAI":
                    if "gpt-4.1" in model_lower:
                        if "mini" in model_lower:
                            model_pricing = provider_pricing.get("gpt-4.1-mini", {})
                        elif "nano" in model_lower:
                            model_pricing = provider_pricing.get("gpt-4.1-nano", {})
                        else:
                            model_pricing = provider_pricing.get("gpt-4.1", {})
                    elif "o3" in model_lower:
                        if "pro" in model_lower:
                            model_pricing = provider_pricing.get("o3-pro", {})
                        else:
                            model_pricing = provider_pricing.get("o3", {})
                    elif "gpt-4o" in model_lower:
                        model_pricing = provider_pricing.get("gpt-4o", {})
                    elif "o4-mini" in model_lower:
                        model_pricing = provider_pricing.get("o4-mini-deep-research", {})
                    elif "gpt-4" in model_lower:
                        model_pricing = provider_pricing.get("gpt-4", {})
                
                # Anthropic fuzzy matching
                elif provider == "Anthropic":
                    if "claude-4" in model_lower or "sonnet-4" in model_lower:
                        model_pricing = provider_pricing.get("claude-sonnet-4-20250514", {})
                    elif "opus-4" in model_lower:
                        model_pricing = provider_pricing.get("claude-opus-4-20250514", {})
                    elif "claude-3" in model_lower:
                        if "opus" in model_lower:
                            model_pricing = provider_pricing.get("claude-3-opus-20240229", {})
                        elif "sonnet" in model_lower:
                            model_pricing = provider_pricing.get("claude-3-sonnet-20240229", {})
                        elif "haiku" in model_lower:
                            model_pricing = provider_pricing.get("claude-3-haiku-20240307", {})
                
                # Gemini fuzzy matching
                elif provider == "Gemini":
                    if "2.5" in model_lower:
                        if "pro" in model_lower:
                            model_pricing = provider_pricing.get("gemini-2.5-pro", {})
                        elif "flash-lite" in model_lower or "lite" in model_lower:
                            model_pricing = provider_pricing.get("gemini-2.5-flash-lite", {})
                        elif "flash" in model_lower:
                            model_pricing = provider_pricing.get("gemini-2.5-flash", {})
                    elif "2.0" in model_lower:
                        if "lite" in model_lower:
                            model_pricing = provider_pricing.get("gemini-2.0-flash-lite", {})
                        else:
                            model_pricing = provider_pricing.get("gemini-2.0-flash", {})
                    elif "gemini-pro" in model_lower:
                        model_pricing = provider_pricing.get("gemini-pro", {})
            
            if not model_pricing:
                return 0.0
            
            # Convert from per-1K to per-token, then scale by actual token count
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
        
        # Check if model is supported for accurate pricing
        model_supported = self.is_model_supported(provider, model)
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "estimated_cost": estimated_cost,
            "provider": provider,
            "model": model,
            "model_supported": model_supported,
            "cost_accuracy": "accurate" if model_supported or estimated_cost > 0 else "estimated"
        }
