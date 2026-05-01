#!/usr/bin/env python3
"""Qwen model client implementation."""

import json
import requests
from typing import Optional, Dict, Any

from .base import BaseLLMClient


class QwenClient(BaseLLMClient):
    """Qwen3 Next 80B API client."""
    
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
        # Add JSON schema hint to prompt if provided
        if schema:
            schema_prompt = f"\n\nRespond with valid JSON that conforms to this schema:\n{json.dumps(schema, indent=2)}"
            prompt = f"{prompt}{schema_prompt}"
        
        # Add requirement to output only JSON
        json_requirement = "\n\nIMPORTANT: Output ONLY the JSON object, no other text, no markdown formatting."
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
        
        # Try to parse JSON from the response
        # Remove markdown code blocks if present
        content = content.strip()
        if content.startswith("```"):
            # Remove markdown code blocks
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            # If parsing fails, return raw content
            return {"raw_output": content, "error": str(e)}
