import streamlit as st
from utils.helpers import get_text
from services.financial_chat_service import FinancialChatService
import logging

logger = logging.getLogger(__name__)

def render_chat_assistant():
    """Render the financial chat assistant interface."""
    st.subheader(get_text('chat.title'))
    
    try:
        # Initialize chat service
        if 'chat_service' not in st.session_state:
            st.session_state.chat_service = FinancialChatService()
        
        # Initialize chat history if not exists
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # Show chat introduction
        st.write(get_text('chat.intro'))
        
        # Display example questions
        for example in get_text('chat.examples'):
            st.markdown(f"- _{example}_")
        
        # Chat history display
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                if message.get("context"):
                    with st.expander(get_text('chat.context_title')):
                        st.write(message["context"])
        
        # Chat input
        if prompt := st.chat_input(get_text('chat.input_placeholder')):
            # Add user message to chat
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.write(prompt)
            
            # Get AI response
            with st.chat_message("assistant"):
                try:
                    with st.spinner(get_text('chat.analyzing')):
                        response = st.session_state.chat_service.get_chat_response(prompt)
                        
                        if "error" in response:
                            st.error(response["error"])
                        else:
                            st.write(response["response"])
                            
                            # Show context if available
                            if response.get("context_used"):
                                with st.expander(get_text('chat.context_title')):
                                    st.write(response["context_used"])
                            
                            # Add assistant response to chat history
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": response["response"],
                                "context": response.get("context_used")
                            })
                except Exception as e:
                    logger.error(f"Error getting chat response: {str(e)}")
                    st.error(get_text('chat.error'))
        
        # Clear chat button
        if st.button(get_text('chat.clear_chat')):
            st.session_state.chat_history = []
            st.rerun()
            
    except Exception as e:
        logger.error(f"Error in chat assistant: {str(e)}")
        st.error(get_text('error.loading_dashboard'))
