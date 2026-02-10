import requests
from app.core.config import config

class OllamaService:
    """Service for interacting with Ollama LLM"""
    
    def __init__(self):
        self.host = config.OLLAMA_HOST
        self.model = config.OLLAMA_MODEL
        print(f"Initialized Ollama service with model: {self.model}")
    
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 500) -> str:
        """Generate text using Ollama"""
        try:
            url = f"{self.host}/api/generate"
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "temperature": temperature,
                "num_predict": max_tokens
            }
            
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "").strip()
        
        except requests.exceptions.RequestException as e:
            print(f"Error calling Ollama: {e}")
            return f"Error: Could not generate response. Make sure Ollama is running at {self.host}"
    
    def check_connection(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama (if not already present)"""
        try:
            url = f"{self.host}/api/pull"
            payload = {"name": model_name, "stream": False}
            response = requests.post(url, json=payload, timeout=600)
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            print(f"Error pulling model: {e}")
            return False

# Global Ollama service instance
ollama_service = OllamaService()
