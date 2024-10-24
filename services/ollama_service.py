import requests
import json

class OllamaService:
    def __init__(self):
        self.base_url = "http://localhost:11434/api/generate"
        
    def classify_transaction(self, description):
        prompt = f"""
        Analyze this transaction description and return a JSON with:
        - type: "income" or "expense"
        - cycle: "none", "daily", "weekly", "monthly", or "yearly"
        - category: appropriate category for the transaction

        Transaction: {description}
        
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
                return json.loads(result['response'])
            return None
        except Exception as e:
            print(f"Error calling Ollama: {str(e)}")
            return None
