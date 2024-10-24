import requests
import json
import re

class OllamaService:
    def __init__(self):
        self.base_url = "http://localhost:11434/api/generate"
        
    def classify_transaction(self, description):
        prompt = f"""
        Analyze this transaction description and return a JSON with:
        - type: "income" or "expense"
        - cycle: "none", "daily", "weekly", "monthly", or "yearly"
        - category: appropriate category for the transaction
        - amount: extract the amount in PLN from the description
          (look for formats like: X PLN, X zł, X złotych, where X is the number)

        Transaction: {description}
        
        Example input: "internet domowy 20zł miesięcznie"
        Example output: {{
            "type": "expense",
            "cycle": "monthly",
            "category": "utilities",
            "amount": 20.00
        }}
        
        Return only the JSON, no other text.
        """
        
        try:
            response = requests.post(
                self.base_url,
                json={
                    "model": "llama2",
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                classified = json.loads(result['response'])
                
                # Fallback amount extraction if AI doesn't detect it
                if 'amount' not in classified or not classified['amount']:
                    amount = self._extract_amount(description)
                    if amount is not None:
                        classified['amount'] = amount
                
                return classified
            return None
        except Exception as e:
            print(f"Error calling Ollama: {str(e)}")
            return None
    
    def _extract_amount(self, text):
        # Match different Polish currency formats
        patterns = [
            r'(\d+(?:\.\d{1,2})?)\s*(?:PLN|zł|złotych|zl|zlotych)',  # With currency
            r'(\d+(?:\.\d{1,2})?)',  # Just numbers
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        return None
