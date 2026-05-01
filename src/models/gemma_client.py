#!/usr/bin/env python3
"""Gemma model client implementation (vision and text)."""

import json
import base64
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List

from .base import BaseLLMClient, BaseVisionClient


class GemmaTextClient(BaseLLMClient):
    """Gemma text generation API client."""
    
    def __init__(self, api_base: str, api_key: str, model: str):
        super().__init__(api_base, api_key, model)
        self.endpoint = f"{self.api_base}/chat/completions"
    
    def generate_text(self, prompt: str, system_prompt: str = "You are a helpful assistant.", max_tokens: int = 4096, **kwargs) -> str:
        """Generate text from prompt."""
        headers = self._build_headers()
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.3,
            **kwargs
        }
        
        response = requests.post(self.endpoint, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def generate_json(self, prompt: str, schema: Optional[Dict[str, Any]] = None, system_prompt: str = "You are a helpful assistant that outputs structured JSON.", max_tokens: int = 8192, **kwargs) -> Dict[str, Any]:
        """Generate structured JSON output."""
        if schema:
            schema_prompt = f"\n\nRespond with valid JSON that conforms to this schema:\n{json.dumps(schema, indent=2)}"
            prompt = f"{prompt}{schema_prompt}"
        
        json_requirement = "\n\nIMPORTANT: Output ONLY the JSON object, no other text."
        prompt = f"{prompt}{json_requirement}"
        
        headers = self._build_headers()
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.1,
            **kwargs
        }
        
        response = requests.post(self.endpoint, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        content = content.strip()
        if content.startswith("```"):
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"raw_output": content, "error": "JSON parsing failed"}


class GemmaVisionClient(BaseVisionClient):
    """Gemma vision API client for image description."""
    
    def __init__(self, api_base: str, api_key: str, model: str):
        super().__init__(api_base, api_key, model)
        self.endpoint = f"{self.api_base}/chat/completions"
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64."""
        with open(image_path, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
        return encoded
    
    def describe_image(self, image_path: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Describe an image using vision model."""
        headers = self._build_headers()
        
        image_base64 = self._encode_image(image_path)
        
        # Default system prompt for visual analysis
        system_prompt = kwargs.get("system_prompt", """You are analyzing a trading education video frame.
Describe what you see in detail.
Identify chart type, indicators, annotations, entry/exit markers, support/resistance levels, trendlines.
Be accurate about what is visible.
Return your analysis as structured JSON with: visual_type, chart_description, visible_indicators, visible_levels, trading_interpretation, uncertainty, visible_assets, timeframe, symbol if visible.
""")
        
        user_prompt = f"""{prompt}

Frame analysis:
- What type of chart do you see?
- What indicators are visible?
- Are there any annotations, lines, or markers?
- What trading setup appears to be described?

Return your analysis as JSON."""
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 4096,
            "temperature": 0.2,
            **kwargs
        }
        
        response = requests.post(self.endpoint, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # Try to parse as JSON
        content = content.strip()
        if content.startswith("```"):
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"description": content, "raw": True, "error": "Could not parse as JSON"}
    
    def analyze_frames(self, image_paths: List[str], prompt: str, **kwargs) -> List[Dict[str, Any]]:
        """Analyze multiple frames."""
        results = []
        for image_path in image_paths:
            result = self.describe_image(image_path, prompt, **kwargs)
            results.append(result)
        return results
