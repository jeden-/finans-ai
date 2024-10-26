import os
import logging
from services.rag_service import RAGService
from services.openai_service import OpenAIService
from services.ollama_service import OllamaService

logger = logging.getLogger(__name__)

class FinancialChatService:
    def __init__(self):
        """Initialize the chat service with RAG and AI services."""
        self.rag_service = RAGService()
        
    def _get_ai_service(self):
        """Get the appropriate AI service based on user settings."""
        import streamlit as st
        return OpenAIService() if st.session_state.ai_model == "OpenAI" else OllamaService()
    
    def get_chat_response(self, query: str) -> dict:
        """Get a response from the AI model with relevant financial context."""
        try:
            # Get relevant transaction context using RAG
            context = self.rag_service.prepare_chat_context(query)
            
            # Prepare the prompt with context
            prompt = f"""You are a helpful financial assistant. Use the following context about the user's transactions to answer their question.
            If the context is not relevant or empty, you can answer based on general financial knowledge.
            
            Context:
            {context}
            
            User Question: {query}
            
            Please provide a clear and concise answer focusing on the financial aspects and any relevant insights from the provided transaction history.
            """
            
            # Get response from AI model
            ai_service = self._get_ai_service()
            response = ai_service.get_chat_completion(prompt)
            
            return {
                'response': response,
                'context_used': context if context != "No relevant transaction history found." else None
            }
            
        except Exception as e:
            logger.error(f"Error getting chat response: {str(e)}")
            return {
                'error': str(e),
                'response': None
            }
