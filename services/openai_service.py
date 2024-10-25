from openai import OpenAI
import json
import re
import logging
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.client = OpenAI()
    
    def classify_transaction(self, description: str, status_callback=None) -> Optional[Dict[str, Any]]:
        """Classify a transaction description using OpenAI."""
        logger.info(f"Processing transaction: {description}")
        
        if status_callback:
            status_callback("Processing transaction with OpenAI...")
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{
                    'role': 'user',
                    'content': f"""Analyze this Polish transaction description and return a JSON with:
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

Return only the JSON, no other text."""
                }]
            )
            
            result = response.choices[0].message.content
            try:
                classified = json.loads(result)
                logger.info(f"Successfully classified: {classified}")
                
                # Fallback amount extraction if AI doesn't detect it
                if 'amount' not in classified or not classified['amount']:
                    amount = self._extract_amount(description)
                    if amount is not None:
                        classified['amount'] = amount
                        logger.debug(f"Amount extracted using fallback: {amount}")
                
                return classified
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error during classification: {str(e)}")
            if status_callback:
                status_callback(f"Error processing transaction: {str(e)}")
            return None
    
    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract amount from text using regex patterns."""
        patterns = [
            r'(\d+(?:[.,]\d{1,2})?)\s*(?:PLN|zł|złotych|zl|zlotych)',  # With currency
            r'(\d+(?:[.,]\d{1,2})?)',  # Just numbers
        ]
        
        logger.debug(f"Attempting to extract amount from: {text}")
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '.')
                    amount = float(amount_str)
                    logger.debug(f"Successfully extracted amount: {amount} using pattern: {pattern}")
                    return amount
                except ValueError as e:
                    logger.warning(f"Failed to convert matched amount: {match.group(1)}, error: {e}")
                    continue
        
        logger.warning("No amount could be extracted from the text")
        return None
