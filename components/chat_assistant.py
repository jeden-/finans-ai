import streamlit as st
from services.financial_chat_service import FinancialChatService
from utils.helpers import get_text
import logging
import os

logger = logging.getLogger(__name__)

def render_chat_assistant():
    st.subheader(get_text('chat.title'))
    
    # Check if OpenAI API key is available
    if not os.environ.get("OPENAI_API_KEY") and st.session_state.ai_model == "OpenAI":
        st.warning(get_text('chat.missing_api_key'))
        return
    
    # Initialize chat service
    if 'chat_service' not in st.session_state:
        st.session_state.chat_service = FinancialChatService()
    
    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Chat interface
    st.write(get_text('chat.intro'))
    for example in get_text('chat.examples'):
        st.write(f"- {example}")
    
    # Chat input
    user_input = st.chat_input(get_text('chat.input_placeholder'))
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Process new message
    if user_input:
        # Add user message to chat
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner(get_text('chat.analyzing')):
                try:
                    response = st.session_state.chat_service.get_chat_response(user_input)
                    
                    if 'error' in response:
                        st.error(response['error'])
                        content = get_text('chat.error')
                    else:
                        content = response['response']
                        st.write(content)
                        
                        # Show context if available
                        if response.get('context_used'):
                            with st.expander(get_text('chat.context_title')):
                                st.write(response['context_used'])
                    
                    # Add assistant response to chat history
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": content
                    })
                    
                except Exception as e:
                    logger.error(f"Error in chat interface: {str(e)}")
                    st.error(get_text('chat.error'))
    
    # Clear chat button
    if st.session_state.chat_history and st.button(get_text('chat.clear_chat')):
        st.session_state.chat_history = []
        st.rerun()
