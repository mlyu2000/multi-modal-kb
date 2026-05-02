"""LiteLLM embedding service for ChromaDB integration."""

import requests
from typing import List, Optional, Dict, Any
from pathlib import Path
import yaml


class LiteLMEmbeddingService:
    """
    Embedding service using LiteLLM proxy server.
    
    Supports any embedding model configured in LiteLLM.
    """
    
    def __init__(self, config_path: str = None):
        """Initialize with config or defaults."""
        # Use config path from settings or default to project root
        from config.settings import PROJECT_ROOT
        actual_path = config_path or PROJECT_ROOT / "config.yaml"
        self.config = self._load_config(actual_path)
        
        # Get embedding model config
        embed_model = self.config.get("embedding_model", "nv-embedqa-mistral-7b-v2")
        base_url = self.config.get("embedding_endpoint", "http://127.0.0.1:4000")
        api_key = self.config.get("embedding_api_key", "sk-12345")
        
        self.model = embed_model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._check_health()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load config from YAML file."""
        config_path = Path(config_path)
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f) or {}
                return config.get("embedding", {})
            except Exception:
                pass
        return {}
    
    def _check_health(self) -> bool:
        """Check if LiteLLM embedding endpoint is available."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Warning: Could not connect to LiteLLM: {e}")
            return False
    
    def embed(self, text: str, input_type: str = "passage", **kwargs) -> List[float]:
        """Embed a single text string."""
        result = self.embed_batch([text], input_type=input_type, **kwargs)
        return result[0]
    
    def embed_batch(self, texts: List[str], input_type: str = "passage", **kwargs) -> List[List[float]]:
        """
        Embed multiple text strings.
        
        Args:
            texts: List of text strings to embed
            input_type: Type of input ('passage' or 'query') - required by NVIDIA embeddings
            **kwargs: Additional parameters passed to LiteLLM
            
        Returns:
            List of embedding vectors
        """
        url = f"{self.base_url}/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "input": texts,
            "input_type": input_type,
            "encoding_format": "float",
            **kwargs
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            # Extract embeddings from response
            embeddings = [item["embedding"] for item in data.get("data", [])]
            return embeddings
            
        except Exception as e:
            raise RuntimeError(f"Embedding request failed: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the embedding model."""
        return {
            "model": self.model,
            "endpoint": self.base_url,
            "healthy": self._check_health()
        }


def test_embedding():
    """Test the embedding service."""
    print("=== Testing LiteLM Embedding Service ===")
    
    # Initialize service
    service = LiteLMEmbeddingService()
    print(f"Model: {service.model}")
    print(f"Endpoint: {service.base_url}")
    
    # Test single embedding
    test_text = "This is a test sentence for gradient descent learning rate."
    embedding = service.embed(test_text)
    print(f"\nEmbedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
    
    # Test batch embedding
    batch_texts = [
        "Gradient descent optimization with learning rate adjusts convergence.",
        "Loss curve shows overshooting when learning rate is too high.",
        "Optimal learning rate provides stable convergence."
    ]
    batch_embeddings = service.embed_batch(batch_texts)
    print(f"\nBatch embeddings: {len(batch_embeddings)} items")
    for i, emb in enumerate(batch_embeddings):
        print(f"  [{i}] dim={len(emb)}, first 3={emb[:3]}")
    
    print("\n✓ Embedding service working correctly!")
    return service


if __name__ == "__main__":
    test_embedding()
