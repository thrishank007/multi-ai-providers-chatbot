import openai
import anthropic
import google.generativeai as genai
from typing import List, Dict, Any, Iterator
import json

class LLMBridge:
    """Bridge class to handle multiple LLM providers"""
    
    def __init__(self):
        self.providers = {
            "OpenAI": {
                "models": [
                    # 2025 OpenAI Models
                    "gpt-4.1",
                    "o3", 
                    "gpt-4o",
                    "o4-mini-deep-research",
                    "gpt-4.1-mini",
                    "gpt-4.1-nano",
                    "o3-pro",
                    # Legacy models for compatibility
                    "gpt-4",
                    "gpt-4-turbo",
                    "gpt-3.5-turbo"
                ],
                "default_model": "gpt-4.1"
            },
            "Anthropic": {
                "models": [
                    # 2025 Claude 4 Models
                    "claude-sonnet-4-20250514",
                    "claude-opus-4-20250514", 
                    # Legacy Claude 3 models for compatibility
                    "claude-3-7-sonnet-20250219",
                    "claude-3-5-sonnet-20241022",
                    "claude-3-5-haiku-20241022",
                    "claude-3-opus-20240229",
                    "claude-3-sonnet-20240229",
                    "claude-3-haiku-20240307"
                ],
                "default_model": "claude-sonnet-4-20250514"
            },
            "Gemini": {
                "models": [
                    # 2025 Gemini Models
                    "gemini-2.5-pro",
                    "gemini-2.5-flash",
                    "gemini-2.5-flash-lite",
                    "gemini-2.0-flash",
                    "gemini-2.0-flash-lite",
                    # Legacy models for compatibility
                    "gemini-pro",
                    "gemini-pro-vision"
                ],
                "default_model": "gemini-2.5-pro"
            }
        }
    
    def get_available_models(self, provider: str) -> List[str]:
        """Get available models for a provider"""
        return self.providers.get(provider, {}).get("models", [])
    
    def get_default_model(self, provider: str) -> str:
        """Get default model for a provider"""
        return self.providers.get(provider, {}).get("default_model", "")
    
    def chat(self, provider: str, model: str, api_key: str, messages: List[Dict[str, str]], 
             temperature: float = 0.7, max_tokens: int = 1000, stream: bool = False) -> Any:
        """Send chat request to specified provider"""
        
        if provider == "OpenAI":
            return self._chat_openai(api_key, model, messages, temperature, max_tokens, stream)
        elif provider == "Anthropic":
            return self._chat_anthropic(api_key, model, messages, temperature, max_tokens, stream)
        elif provider == "Gemini":
            return self._chat_gemini(api_key, model, messages, temperature, max_tokens, stream)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def _chat_openai(self, api_key: str, model: str, messages: List[Dict[str, str]], 
                     temperature: float, max_tokens: int, stream: bool) -> Any:
        """Handle OpenAI chat requests"""
        client = openai.OpenAI(api_key=api_key)
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            return response
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def _chat_anthropic(self, api_key: str, model: str, messages: List[Dict[str, str]], 
                        temperature: float, max_tokens: int, stream: bool) -> Any:
        """Handle Anthropic chat requests"""
        client = anthropic.Anthropic(api_key=api_key)
        
        # Convert messages format for Anthropic
        system_message = ""
        claude_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                claude_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        try:
            response = client.messages.create(
                model=model,
                system=system_message,
                messages=claude_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            return response
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def _chat_gemini(self, api_key: str, model: str, messages: List[Dict[str, str]], 
                     temperature: float, max_tokens: int, stream: bool) -> Any:
        """Handle Gemini chat requests"""
        genai.configure(api_key=api_key)
        model_instance = genai.GenerativeModel(model)
        
        # Convert messages to Gemini format
        conversation = []
        for msg in messages:
            if msg["role"] == "user":
                conversation.append(msg["content"])
            elif msg["role"] == "assistant":
                conversation.append(msg["content"])
        
        # Use the last user message as the prompt
        prompt = conversation[-1] if conversation else ""
        
        try:
            response = model_instance.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens
                ),
                stream=stream
            )
            return response
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def extract_content(self, provider: str, response: Any) -> str:
        """Extract content from provider response"""
        try:
            if provider == "OpenAI":
                return response.choices[0].message.content
            elif provider == "Anthropic":
                return response.content[0].text
            elif provider == "Gemini":
                return response.text
            else:
                return str(response)
        except Exception as e:
            return f"Error extracting content: {str(e)}"
    
    def extract_stream_content(self, provider: str, chunk: Any) -> str:
        """Extract content from streaming response chunk"""
        try:
            if provider == "OpenAI":
                delta = chunk.choices[0].delta
                return delta.content if delta.content else ""
            elif provider == "Anthropic":
                if chunk.type == "content_block_delta":
                    return chunk.delta.text
                return ""
            elif provider == "Gemini":
                return chunk.text if hasattr(chunk, 'text') else ""
            else:
                return ""
        except Exception:
            return ""
