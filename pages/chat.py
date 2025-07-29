import streamlit as st
import json
from datetime import datetime
from core.providers import LLMBridge
from core.memory import MemoryManager
from core.counters import TokenCounter
from core.utils import generate_conversation_id, format_chat_history_for_export, log_analytics, validate_api_key

def show_chat_page():
    """Display the main chat interface"""
    st.title("🤖 AI Chatbot")
    
    # Initialize components
    llm_bridge = LLMBridge()
    memory_manager = MemoryManager()
    token_counter = TokenCounter()
    
    # Initialize session state
    if 'history' not in st.session_state:
        st.session_state.history = []
    
    if 'conversation_id' not in st.session_state:
        st.session_state.conversation_id = generate_conversation_id()
    
    if 'total_tokens_used' not in st.session_state:
        st.session_state.total_tokens_used = 0
    
    if 'total_cost' not in st.session_state:
        st.session_state.total_cost = 0.0
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Provider selection
        provider = st.selectbox(
            "AI Provider",
            ["OpenAI", "Anthropic", "Gemini"],
            key="provider"
        )
        
        # Model selection
        available_models = llm_bridge.get_available_models(provider)
        model = st.selectbox(
            "Model",
            available_models,
            index=0 if available_models else 0,
            key="model"
        )
        
        # API Key input
        api_key = st.text_input(
            "API Key",
            type="password",
            placeholder=f"Enter your {provider} API key",
            key="api_key"
        )
        
        # Validate API key
        if api_key and not validate_api_key(provider, api_key):
            st.error("Invalid API key format")
        
        # Parameters
        st.subheader("Parameters")
        temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
        max_tokens = st.slider("Max Tokens", 100, 4000, 1000, 100)
        
        # Memory settings
        st.subheader("Memory")
        use_memory = st.checkbox("Use conversation memory", value=True)
        recall_count = st.slider("Memory recall count", 1, 10, 4, 1)
        
        # Token usage display
        st.subheader("📊 Token Usage")
        st.metric("Session Tokens", st.session_state.total_tokens_used)
        st.metric("Estimated Cost", f"${st.session_state.total_cost:.4f}")
    
    # Main chat interface
    col1, col2 = st.columns([3, 1])
    
    with col2:
        # Export buttons
        if st.session_state.history:
            # JSON export
            json_data = format_chat_history_for_export(st.session_state.history, "json")
            st.download_button(
                "📥 Download JSON",
                json_data,
                f"chat_{st.session_state.conversation_id[:8]}.json",
                "application/json"
            )
            
            # Markdown export
            md_data = format_chat_history_for_export(st.session_state.history, "md")
            st.download_button(
                "📄 Download MD",
                md_data,
                f"chat_{st.session_state.conversation_id[:8]}.md",
                "text/markdown"
            )
            
            # Clear conversation
            if st.button("🗑️ Clear Chat", type="secondary"):
                st.session_state.history = []
                st.session_state.conversation_id = generate_conversation_id()
                st.rerun()
    
    with col1:
        # Display chat history
        for message in st.session_state.history:
            role = message["role"]
            content = message["content"]
            timestamp = message.get("timestamp", "")
            
            if role == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>You</strong> <small>{timestamp}</small><br>
                    {content}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>Assistant</strong> <small>{timestamp}</small><br>
                    {content}
                </div>
                """, unsafe_allow_html=True)
        
        # Chat input
        user_input = st.chat_input("Type your message here...")
        
        if user_input and api_key and validate_api_key(provider, api_key):
            # Add user message to history
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user_message = {
                "role": "user",
                "content": user_input,
                "timestamp": timestamp
            }
            st.session_state.history.append(user_message)
            
            # Prepare messages for API
            messages = []
            
            # Add system message
            system_msg = "You are a helpful AI assistant. Be concise and helpful."
            
            # Add memory context if enabled
            if use_memory:
                relevant_memories = memory_manager.recall(
                    st.session_state.user_id,
                    user_input,
                    k=recall_count,
                    conversation_id=st.session_state.conversation_id
                )
                
                if relevant_memories:
                    memory_context = "\n".join([
                        f"Previous {mem['role']}: {mem['content']}"
                        for mem in relevant_memories
                    ])
                    system_msg += f"\n\nRelevant context from previous conversation:\n{memory_context}"
            
            messages.append({"role": "system", "content": system_msg})
            
            # Add recent conversation history (last 10 messages)
            recent_history = st.session_state.history[-10:]
            for msg in recent_history:
                if msg["role"] in ["user", "assistant"]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            
            # Count input tokens
            input_tokens = token_counter.count_messages_tokens(provider, model, messages)
            
            # Display token counter
            st.markdown(f"""
            <div class="token-counter">
                <strong>Input tokens:</strong> {input_tokens} | 
                <strong>Estimated cost:</strong> ${token_counter.estimate_cost(provider, model, input_tokens, 0):.4f}
            </div>
            """, unsafe_allow_html=True)
            
            try:
                with st.spinner("Generating response..."):
                    # Call LLM
                    response = llm_bridge.chat(
                        provider=provider,
                        model=model,
                        api_key=api_key,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        stream=False
                    )
                    
                    # Extract response content
                    assistant_content = llm_bridge.extract_content(provider, response)
                    
                    # Count output tokens
                    output_tokens = token_counter.count_tokens(provider, model, assistant_content)
                    
                    # Calculate cost
                    estimated_cost = token_counter.estimate_cost(provider, model, input_tokens, output_tokens)
                    
                    # Update session totals
                    st.session_state.total_tokens_used += input_tokens + output_tokens
                    st.session_state.total_cost += estimated_cost
                    
                    # Add assistant response to history
                    assistant_message = {
                        "role": "assistant",
                        "content": assistant_content,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.history.append(assistant_message)
                    
                    # Store in memory
                    if use_memory:
                        memory_manager.add_message(
                            st.session_state.user_id,
                            "user",
                            user_input,
                            st.session_state.conversation_id
                        )
                        memory_manager.add_message(
                            st.session_state.user_id,
                            "assistant",
                            assistant_content,
                            st.session_state.conversation_id
                        )
                    
                    # Log analytics
                    log_analytics(
                        st.session_state.user_id,
                        provider,
                        model,
                        input_tokens,
                        output_tokens,
                        estimated_cost,
                        st.session_state.conversation_id
                    )
                    
                    # Check for auto-summary
                    if use_memory:
                        message_count = memory_manager.count_messages(
                            st.session_state.user_id,
                            st.session_state.conversation_id
                        )
                        
                        if message_count >= 20:
                            with st.spinner("Creating summary..."):
                                memory_manager.summarize_and_prune(
                                    st.session_state.user_id,
                                    st.session_state.conversation_id,
                                    llm_bridge,
                                    provider,
                                    model,
                                    api_key
                                )
                    
                    st.rerun()
                    
            except Exception as e:
                st.error(f"Error generating response: {str(e)}")
        
        elif user_input and not api_key:
            st.error("Please enter your API key in the sidebar")
        elif user_input and not validate_api_key(provider, api_key):
            st.error("Please enter a valid API key")
