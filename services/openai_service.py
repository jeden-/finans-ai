import logging
import json
from openai import OpenAI
import streamlit as st
from typing import Optional, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.client = OpenAI()
        self.model = st.session_state.get('openai_model', 'gpt-3.5-turbo')
        
    def classify_transaction(self, description: str, status_callback=None) -> Optional[Dict[str, Any]]:
        """Classify a transaction description using OpenAI."""
        logger.info(f"Processing transaction: {description}")
        
        if status_callback:
            status_callback("Processing transaction with OpenAI...")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": """You are a financial assistant that analyzes transaction descriptions.
Return only a JSON object with the following fields:
- type: "income" or "expense"
- cycle: "none", "daily", "weekly", "monthly", or "yearly"
- category: appropriate category for the transaction
- amount: extract the amount in PLN from the description
  (look for formats like: X PLN, X zł, X złotych, X zl, X zlotych, where X is the number)"""},
                    {"role": "user", "content": description}
                ],
                temperature=0.3,
                max_tokens=150
            )
            
            result = response.choices[0].message.content
            try:
                classified = json.loads(result)
                logger.info(f"Successfully classified: {classified}")
                return classified
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error during classification: {str(e)}")
            if status_callback:
                status_callback(f"Error processing transaction: {str(e)}")
            return None

    def chat_about_transactions(self, messages: list, context: str = "") -> str:
        """Chat about transactions using OpenAI."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error in chat response: {str(e)}")
            return f"I apologize, but I encountered an error: {str(e)}"
