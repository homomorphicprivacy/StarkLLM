import requests
import json
import logging
from typing import Generator, List
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        
    def get_available_models(self) -> List[str]:
        url = f"{self.base_url}/api/tags"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            models = response.json().get("models", [])
            return [m["name"] for m in models]
        except Exception as e:
            logger.error(f"Error fetching Ollama models: {e}")
            return []

    def generate_chat(self, model: str, messages: list[dict], stream: bool = False, options: dict = None):
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream
        }
        
        if options:
            payload["options"] = options
        
        if stream:
            return self._stream_response(url, payload)
        else:
            try:
                response = requests.post(url, json=payload, timeout=150)
                if response.status_code == 404:
                    raise ValueError(f"Model '{payload.get('model')}' not found in Ollama. Please ensure it is pulled (e.g. ollama run {payload.get('model')}).")
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.error(f"LLM API Error: {e}")
                raise

    def _stream_response(self, url: str, payload: dict) -> Generator[str, None, None]:
        try:
            with requests.post(url, json=payload, stream=True, timeout=150) as response:
                if response.status_code == 404:
                    yield f"\n\nError: Model '{payload.get('model')}' not found in Ollama. Please ensure it is pulled (e.g. ollama run {payload.get('model')})."
                    return
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM Streaming API Error: {e}")
            raise

    def generate_embeddings(self, model: str, prompt: str) -> list[float]:
        url = f"{self.base_url}/api/embeddings"
        payload = {
            "model": model,
            "prompt": prompt
        }
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json().get("embedding", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM Embeddings API Error: {e}")
            raise

    def generate_embeddings_batch(self, model: str, prompts: List[str]) -> List[List[float]]:
        url = f"{self.base_url}/api/embed"
        payload = {
            "model": model,
            "input": prompts
        }
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json().get("embeddings", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM Batch Embeddings API Error: {e}")
            logger.warning("Falling back to single embedding generation...")
            return [self.generate_embeddings(model, p) for p in prompts]

llm_service = LLMService()
