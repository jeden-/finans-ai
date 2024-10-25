import requests
import json
import logging
import streamlit as st
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaService:
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.model = st.session_state.get('ollama_model', 'llama2')
        
    def classify_transaction(self, description: str, status_callback=None) -> Optional[Dict[str, Any]]:
        """Classify a transaction description using Ollama."""
        logger.info(f"Processing transaction: {description}")
        
        if status_callback:
            status_callback("Processing transaction with Ollama...")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": f"""Analyze this Polish transaction description and return a JSON with:
- type: "income" or "expense"
- cycle: "none", "daily", "weekly", "monthly", or "yearly"
- category: appropriate category for the transaction
- amount: extract the amount in PLN from the description
  (look for formats like: X PLN, X zł, X złotych, X zl, X zlotych, where X is the number)

Transaction: {description}

Example inputs and outputs:
Input: "internet domowy 20zł miesięcznie"
Output: {{"type": "expense", "cycle": "monthly", "category": "utilities", "amount": 20.00}}

Input: "wypłata 5000 złotych"
Output: {{"type": "income", "cycle": "monthly", "category": "salary", "amount": 5000.00}}

Return only the JSON, no other text.""",
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()["response"]
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
        """Chat about transactions using Ollama."""
        try:
            # Convert messages to a conversation format
            conversation = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": f"""You are an expert financial advisor assistant. 
Context about the user's transactions:
{context}

Conversation history:
{conversation}

Provide a helpful and informative response based on the context and conversation.
Response should be specific, actionable, and reference the actual transaction data when available.""",
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                return response.json()["response"]
            else:
                raise Exception(f"Error from Ollama API: {response.text}")
                
        except Exception as e:
            logger.error(f"Error in chat response: {str(e)}")
            return f"I apologize, but I encountered an error: {str(e)}"
