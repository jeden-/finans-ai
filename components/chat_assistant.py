import streamlit as st
from services.financial_chat_service import FinancialChatService
import logging

logger = logging.getLogger(__name__)

def render_chat_assistant():
    st.subheader("Financial Chat Assistant")
    
    # Initialize chat service
    if 'chat_service' not in st.session_state:
        st.session_state.chat_service = FinancialChatService()
    
    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Chat interface
    st.write("""
    💬 Ask me anything about your finances! For example:
    - "What are my top spending categories this month?"
    - "Am I spending more on groceries compared to last month?"
    - "What's my usual spending pattern during weekends?"
    - "Can you suggest ways to reduce my monthly expenses?"
    """)
    
    # Chat input
    user_input = st.chat_input("Type your question here...")
    
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
            with st.spinner("Analyzing your finances..."):
                try:
                    response = st.session_state.chat_service.get_chat_response(user_input)
                    
                    if 'error' in response:
                        st.error(response['error'])
                        content = "I apologize, but I encountered an error. Please try again."
                    else:
                        content = response['response']
                        st.write(content)
                        
                        # Show context if available
                        if response.get('context_used'):
                            with st.expander("🔍 Relevant Transaction Context"):
                                st.write(response['context_used'])
                    
                    # Add assistant response to chat history
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": content
                    })
                    
                except Exception as e:
                    logger.error(f"Error in chat interface: {str(e)}")
                    st.error("An error occurred while processing your question. Please try again.")
    
    # Clear chat button
    if st.button("Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()
