#!/usr/bin/env python3
"""Gemma vision model client."""

import requests
from typing import Dict, Any, Optional
import logging

from utils.retry import retry_gemma
from config.settings import settings


class GemmaVisionClient:
    """Client for Gemma vision model via API."""
    
    def __init__(self, api_base: str = None, api_key: str = None, model: str = None):
        self.api_base = api_base or settings.gemma_api_base
        self.api_key = api_key or settings.gemma_api_key
        self.model = model or settings.gemma_model
        self.logger = logging.getLogger("trading_kb")
    
    @retry_gemma
    def describe_image(self, image_path: str, prompt: str, 
                       system_prompt: str = None) -> Dict[str, Any]:
        """Describe an image using Gemma vision model.
        
        Args:
            image_path: Path to the image file
            prompt: Prompt for description
            system_prompt: Optional system prompt
            
        Returns:
            Description result with text and metadata
        """
        self.logger.info(f"Sending image description request for {image_path}")
        
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        files = {"image": (image_path, image_data)}
        json_data = {
            "prompt": prompt,
            "model": self.model
        }
        
        if system_prompt:
            json_data["system_prompt"] = system_prompt
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        response = requests.post(
            f"{self.api_base}/predict",
            files=files,
            json=json_data,
            headers=headers,
            timeout=300
        )
        
        response.raise_for_status()
        return response.json()
    
    def classify_image(self, image_path: str, classes: list) -> Dict[str, Any]:
        """Classify an image into predefined classes."""
        raise NotImplementedError("Not yet implemented")
