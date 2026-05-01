#!/usr/bin/env python3
"""Base model client abstractions."""

import abc
from typing import Optional, Dict, Any, List


class BaseLLMClient(abc.ABC):
    """Base class for LLM clients."""
    
    def __init__(self, api_base: str, api_key: str, model: str):
        self.api_base = api_base.rstrip('/')
        self.api_key = api_key
        self.model = model
    
    @abc.abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt."""
        pass
    
    @abc.abstractmethod
    def generate_json(self, prompt: str, schema: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Generate structured JSON output."""
        pass
    
    def _build_headers(self) -> Dict[str, str]:
        """Build HTTP headers for API calls."""
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers


class BaseVisionClient(abc.ABC):
    """Base class for vision model clients."""
    
    def __init__(self, api_base: str, api_key: str, model: str):
        self.api_base = api_base.rstrip('/')
        self.api_key = api_key
        self.model = model
    
    @abc.abstractmethod
    def describe_image(self, image_path: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Describe an image using vision model."""
        pass
    
    @abc.abstractmethod
    def analyze_frames(self, image_paths: List[str], prompt: str, **kwargs) -> List[Dict[str, Any]]:
        """Analyze multiple frames."""
        pass
