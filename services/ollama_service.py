import requests
import json
import re
import logging
import time
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaService:
    def __init__(self, max_retries: int = 3, retry_delay: int = 2):
        self.base_url = "http://localhost:11434/api/generate"
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.models_to_try = ["mistral", "llama2:13b", "llama2"]
        
    def _check_ollama_running(self) -> bool:
        """Check if Ollama service is running."""
        try:
            response = requests.get("http://localhost:11434/api/tags")
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            return False

    def _check_model_available(self, model: str) -> bool:
        """Check if specific model is available."""
        try:
            response = requests.get(f"http://localhost:11434/api/show?name={model}")
            return response.status_code == 200
        except:
            return False

    def _get_model_install_instructions(self, model: str) -> str:
        """Get installation instructions for a specific model."""
        return f"""
To install the {model} model:
1. Open a terminal
2. Run: ollama pull {model}
3. Then run: ollama run {model}
"""

    def _retry_connection(self, func) -> Optional[Dict[str, Any]]:
        """Retry mechanism for Ollama API calls."""
        retries = 0
        last_error = None
        last_model_error = None

        while retries < self.max_retries:
            try:
                if not self._check_ollama_running():
                    raise ConnectionError("Ollama service is not running")
                result = func()
                if result:
                    return result
                retries += 1
            except Exception as e:
                last_error = e
                if isinstance(e, requests.exceptions.RequestException) and hasattr(e, 'response'):
                    last_model_error = e.response.json().get('error', str(e)) if e.response else str(e)
                else:
                    last_model_error = str(e)
                logger.error(f"Attempt {retries + 1}/{self.max_retries} failed: {str(e)}")
                retries += 1
                if retries < self.max_retries:
                    time.sleep(self.retry_delay)

        error_msg = f"Failed after {self.max_retries} attempts. Last error: {str(last_error)}"
        if isinstance(last_error, ConnectionError):
            error_msg += "\nPlease ensure Ollama is running and try again:\n" \
                        "1. Open a terminal\n" \
                        "2. Run: ollama run mistral\n" \
                        "If mistral is not installed, run: ollama pull mistral"
        elif last_model_error and "model not found" in last_model_error.lower():
            error_msg += "\nNo compatible model found. Please install one of these models:\n"
            for model in self.models_to_try:
                error_msg += self._get_model_install_instructions(model)
        logger.error(error_msg)
        return None

    def classify_transaction(self, description: str) -> Optional[Dict[str, Any]]:
        """Classify a transaction description using Ollama."""
        logger.info(f"Processing transaction: {description}")
        
        prompt = f"""
        Analyze this Polish transaction description and return a JSON with:
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
        
        Return only the JSON, no other text.
        """
        
        def make_request():
            for model in self.models_to_try:
                logger.info(f"Attempting to use model: {model}")
                
                if not self._check_model_available(model):
                    logger.warning(f"Model {model} is not available")
                    continue
                
                try:
                    response = requests.post(
                        self.base_url,
                        json={
                            "model": model,
                            "prompt": prompt,
                            "stream": False
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        try:
                            classified = json.loads(result['response'])
                            logger.info(f"Successfully classified using model {model}: {classified}")
                            
                            # Fallback amount extraction if AI doesn't detect it
                            if 'amount' not in classified or not classified['amount']:
                                amount = self._extract_amount(description)
                                if amount is not None:
                                    classified['amount'] = amount
                                    logger.info(f"Amount extracted using fallback: {amount}")
                            
                            return classified
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse AI response from model {model}: {e}")
                            continue
                except Exception as e:
                    logger.warning(f"Failed with model {model}: {e}")
                    continue
            
            return None

        return self._retry_connection(make_request)
    
    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract amount from text using regex patterns."""
        # Match different Polish currency formats
        patterns = [
            r'(\d+(?:[.,]\d{1,2})?)\s*(?:PLN|zł|złotych|zl|zlotych)',  # With currency
            r'(\d+(?:[.,]\d{1,2})?)',  # Just numbers
        ]
        
        logger.info(f"Attempting to extract amount from: {text}")
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    # Replace comma with dot for proper float conversion
                    amount_str = match.group(1).replace(',', '.')
                    amount = float(amount_str)
                    logger.info(f"Successfully extracted amount: {amount} using pattern: {pattern}")
                    return amount
                except ValueError as e:
                    logger.warning(f"Failed to convert matched amount: {match.group(1)}, error: {e}")
                    continue
        
        logger.warning("No amount could be extracted from the text")
        return None
