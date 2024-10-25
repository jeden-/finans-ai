from typing import Dict, Any, Optional, List
import logging
from services.rag_service import RAGService
from services.openai_service import OpenAIService
from services.ollama_service import OllamaService
from models.transaction import Transaction
from utils.analytics import get_spending_insights, analyze_spending_patterns
import streamlit as st
import pandas as pd

logger = logging.getLogger(__name__)

class FinancialChatService:
    def __init__(self):
        self.rag_service = RAGService()
        # Initialize AI service based on selected model
        self.ai_service = OpenAIService() if st.session_state.ai_model == "OpenAI" else OllamaService()
        self.transaction_model = Transaction()

    def get_chat_response(self, query: str) -> Dict[str, Any]:
        """Get a response from the financial chat assistant."""
        try:
            # Get transaction context
            context = self.rag_service.prepare_chat_context(query)
            
            # Get additional financial insights
            transactions = self.transaction_model.get_all_transactions()
            if transactions:
                df = pd.DataFrame(transactions)
                insights = get_spending_insights(df)
                patterns = analyze_spending_patterns(df)
            else:
                insights = {}
                patterns = {}

            # Create messages for the chat
            messages = [
                {"role": "system", "content": """You are an expert financial advisor assistant. Your role is to:
1. Analyze transaction data and provide specific insights
2. Answer questions about spending patterns and financial habits
3. Give practical financial advice based on the user's actual transaction history
4. Be precise with numbers and calculations
5. Always provide reasoning for your advice
6. Use PLN (Polish Złoty) as the currency

When suggesting improvements or changes:
- Be specific and actionable
- Reference actual transaction data when available
- Consider the user's spending patterns and habits
- Explain the potential benefits of your suggestions"""},
                {"role": "user", "content": f"""Using this context about the user's transactions and financial history:

{context}

Additional insights:
- Total spending: {insights.get('total_spending', 'N/A')} PLN
- Average transaction: {insights.get('avg_transaction', 'N/A')} PLN
- Monthly spending trend: {insights.get('spending_trend', {})}
- Seasonal patterns: {patterns.get('high_spending_months', {})}

Question: {query}"""}
            ]

            # Get response from selected AI model
            if isinstance(self.ai_service, OpenAIService):
                response = self.ai_service.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=500
                )
                response_text = response.choices[0].message.content
            else:
                response_text = self.ai_service.chat_about_transactions(messages, context)

            return {
                'response': response_text,
                'context_used': context,
                'relevant_insights': insights
            }

        except Exception as e:
            logger.error(f"Error getting chat response: {str(e)}")
            return {
                'error': str(e),
                'response': "I apologize, but I encountered an error while processing your question. Please try again."
            }

    def update_knowledge_base(self):
        """Update the RAG knowledge base with new transactions."""
        try:
            self.rag_service.update_transaction_embeddings()
            return True
        except Exception as e:
            logger.error(f"Error updating knowledge base: {str(e)}")
            return False
