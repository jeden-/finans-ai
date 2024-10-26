import requests
import json
import logging
import streamlit as st

logger = logging.getLogger(__name__)

class OllamaService:
    def __init__(self):
        """Initialize Ollama service."""
        self.base_url = "http://localhost:11434/api"
        
    def get_chat_completion(self, prompt: str) -> str:
        """Get a chat completion from Ollama."""
        try:
            response = requests.post(
                f"{self.base_url}/generate",
                json={
                    "model": st.session_state.get('ollama_model', 'llama2'),
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            return response.json().get('response', '')
            
        except Exception as e:
            logger.error(f"Error getting chat completion: {str(e)}")
            raise
            
    def classify_transaction(self, description: str, status_callback=None) -> dict:
        """Classify a transaction description into structured data."""
        try:
            if status_callback:
                status_callback("Processing with Ollama...")
                
            prompt = f"""Analyze this transaction description and extract the following information:
            Description: "{description}"
            
            Return a JSON object with:
            - amount (float, extract amount in PLN)
            - type (string, either "income" or "expense")
            - category (string, choose an appropriate category)
            - cycle (string, either "none", "daily", "weekly", "monthly", or "yearly")
            
            Common categories: groceries, transportation, housing, utilities, entertainment, income, salary, etc.
            Format your response as a valid JSON object.
            """
            
            response = requests.post(
                f"{self.base_url}/generate",
                json={
                    "model": st.session_state.get('ollama_model', 'llama2'),
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            
            # Process the response
            result = json.loads(response.json().get('response', '{}'))
            
            # Ensure amount is a float
            if 'amount' in result:
                result['amount'] = float(result['amount'])
                
            return result
            
        except Exception as e:
            logger.error(f"Error classifying transaction: {str(e)}")
            return None
