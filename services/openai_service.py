import os
import openai
from openai import OpenAI
import logging
import streamlit as st

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        """Initialize OpenAI client."""
        self.client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
    def get_chat_completion(self, prompt: str) -> str:
        """Get a chat completion from OpenAI."""
        try:
            response = self.client.chat.completions.create(
                model=st.session_state.get('openai_model', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": "You are a helpful financial assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error getting chat completion: {str(e)}")
            raise
            
    def classify_transaction(self, description: str, status_callback=None) -> dict:
        """Classify a transaction description into structured data."""
        try:
            if status_callback:
                status_callback("Processing with OpenAI...")
                
            prompt = f"""Analyze this transaction description and extract the following information:
            Description: "{description}"
            
            Return a JSON object with:
            - amount (float, extract amount in PLN)
            - type (string, either "income" or "expense")
            - category (string, choose an appropriate category)
            - cycle (string, either "none", "daily", "weekly", "monthly", or "yearly")
            
            Common categories: groceries, transportation, housing, utilities, entertainment, income, salary, etc.
            """
            
            response = self.client.chat.completions.create(
                model=st.session_state.get('openai_model', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": "You are a financial transaction classifier."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            # Process the response
            import json
            result = json.loads(response.choices[0].message.content)
            
            # Ensure amount is a float
            if 'amount' in result:
                result['amount'] = float(result['amount'])
                
            return result
            
        except Exception as e:
            logger.error(f"Error classifying transaction: {str(e)}")
            return None
