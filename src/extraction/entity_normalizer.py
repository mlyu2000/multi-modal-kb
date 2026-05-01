#!/usr/bin/env python3
"""Entity normalization module for trading KB."""

import os
from typing import Dict, Any, List, Optional
import json
import re

from src.config.settings import settings
from src.models.qwen_client import QwenClient


class EntityNormalizer:
    """Normalize trading entities by merging synonyms."""
    
    # Common trading term mappings
    COMMON_MAPPINGS = {
        # Break of Structure
        "bos": "Break of Structure",
        "break of structure": "Break of Structure",
        "break of struct": "Break of Structure",
        "break of s/r": "Break of Structure",
        
        # Support and Resistance
        "s/r": "Support and Resistance",
        "support resistance": "Support and Resistance",
        "s and r": "Support and Resistance",
        "support and resistance": "Support and Resistance",
        
        # Reward-to-Risk Ratio
        "rr": "Reward-to-Risk Ratio",
        "risk reward": "Reward-to-Risk Ratio",
        "risk-to-reward": "Reward-to-Risk Ratio",
        "rr ratio": "Reward-to-Risk Ratio",
        
        # Fibonacci
        "fib": "Fibonacci",
        "fibonacci levels": "Fibonacci",
        
        # Weekly/Monthly levels
        "wm": "Weekly Monthly",
        "weekly monthly": "Weekly Monthly",
        "wmr": "Weekly Monthly Resistance",
        
        # Swing High/Low
        "swing high": "Swing High",
        "swing low": "Swing Low",
        "sh": "Swing High",
        "sl": "Swing Low",
        
        # Higher High/Low
        "hh": "Higher High",
        "hl": "Higher Low",
        "lh": "Lower High",
        "ll": "Lower Low",
        
        # Range
        "range bar": "Range Bar",
        "range bar chart": "Range Bar",
        
        # Trend
        "uptrend": "Uptrend",
        "downtrend": "Downtrend",
        "sideways": "Sideways Trade",
        
        # Timeframes
        "1m": "1 Minute",
        "5m": "5 Minutes",
        "15m": "15 Minutes",
        "1h": "1 Hour",
        "4h": "4 Hours",
        "1d": "1 Day",
        "1w": "1 Week",
        
        # Chart patterns
        "double top": "Double Top",
        "double bottom": "Double Bottom",
        "head and shoulders": "Head and Shoulders",
        "hns": "Head and Shoulders",
        "inverse hns": "Inverse Head and Shoulders",
        "triangle": "Triangle Pattern",
        "ascending triangle": "Ascending Triangle",
        "descending triangle": "Descending Triangle",
        "symmetrical triangle": "Symmetrical Triangle",
        "rectangle": "Rectangle Pattern",
        "block pattern": "Block Pattern",
        
        # Candlestick patterns
        "doji": "Doji",
        "hammer": "Hammer",
        "hanging man": "Hanging Man",
        "engulfing": "Engulfing Pattern",
        "bullish engulfing": "Bullish Engulfing",
        "bearish engulfing": "Bearish Engulfing",
        "morning star": "Morning Star",
        "evening star": "Evening Star",
        
        # Indicators
        "rsi": "RSI",
        "relative strength index": "RSI",
        "macd": "MACD",
        "moving average": "Moving Average",
        "ma": "Moving Average",
        "ema": "Exponential Moving Average",
        "sma": "Simple Moving Average",
        "bollinger bands": "Bollinger Bands",
        "bb": "Bollinger Bands",
    }
    
    def __init__(self, api_base: str = None, api_key: str = None, model: str = None):
        self.api_base = api_base or settings.qwen_api_base
        self.api_key = api_key or settings.qwen_api_key
        self.model = model or settings.qwen_model
        
        self.qwen_client = QwenClient(
            api_base=self.api_base,
            api_key=self.api_key,
            model=self.model
        )
    
    def normalize(self, raw_name: str, entity_type: str) -> Dict[str, str]:
        """Normalize a raw entity name to its canonical form.
        
        Args:
            raw_name: The raw/entity name found in the text
            entity_type: The type of entity (Strategy, Concept, Indicator, etc.)
        
        Returns:
            Dictionary with raw_name and canonical_name
        """
        raw_lower = raw_name.lower().strip()
        
        # Check common mappings first
        if raw_lower in self.COMMON_MAPPINGS:
            return {
                "raw_name": raw_name,
                "canonical_name": self.COMMON_MAPPINGS[raw_lower],
                "type": entity_type,
                "method": "common_mapping"
            }
        
        # For other cases, use Qwen to determine canonical form
        try:
            result = self._normalize_with_llm(raw_name, entity_type)
            return result
        except Exception:
            # Fallback: just clean up the name
            cleaned = self._clean_name(raw_name)
            return {
                "raw_name": raw_name,
                "canonical_name": cleaned,
                "type": entity_type,
                "method": "cleaning"
            }
    
    def _normalize_with_llm(self, raw_name: str, entity_type: str) -> Dict[str, str]:
        """Use Qwen to normalize entity names."""
        prompt = f"""Normalize the following trading entity.

Raw name: {raw_name}
Type: {entity_type}

Map this to its canonical/trading-standard name.
Return only the canonical name, no other text.
"""
        
        try:
            canonical = self.qwen_client.generate_text(prompt).strip()
            return {
                "raw_name": raw_name,
                "canonical_name": canonical,
                "type": entity_type,
                "method": "llm"
            }
        except Exception as e:
            return {
                "raw_name": raw_name,
                "canonical_name": self._clean_name(raw_name),
                "type": entity_type,
                "method": "error_fallback",
                "error": str(e)
            }
    
    def _clean_name(self, name: str) -> str:
        """Clean up a name by removing extra whitespace and standardizing."""
        # Remove extra spaces
        name = re.sub(r"\s+", " ", name)
        # Capitalize words
        name = name.strip().title()
        return name
    
    def normalize_batch(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize a batch of entities.
        
        Args:
            entities: List of entity dictionaries with 'name' and 'type' keys
        
        Returns:
            List of normalized entity dictionaries
        """
        normalized = []
        for entity in entities:
            norm = self.normalize(entity.get("name", ""), entity.get("type", ""))
            normalized.append({
                **entity,
                "raw_name": entity.get("name", ""),
                "canonical_name": norm["canonical_name"],
                "normalization_method": norm["method"]
            })
        return normalized


def normalize_entity(raw_name: str, entity_type: str) -> Dict[str, str]:
    """Convenience function to normalize an entity."""
    normalizer = EntityNormalizer()
    return normalizer.normalize(raw_name, entity_type)
