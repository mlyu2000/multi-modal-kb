#!/usr/bin/env python3

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

"""Knowledge extraction module using Qwen model."""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import uuid

from src.config.settings import settings
from src.storage.sqlite_store import SQLiteStore
from src.storage.file_store import FileStore
from src.models.qwen_client import QwenClient


class KnowledgeExtractor:
    """Extract structured knowledge from video segments using Qwen."""
    
    # Entity types
    STRATEGY = "Strategy"
    CONCEPT = "Concept"
    INDICATOR = "Indicator"
    RULE = "Rule"
    CONDITION = "Condition"
    MARKET_CONTEXT = "MarketContext"
    ASSET_CLASS = "AssetClass"
    TIMEFRAME = "Timeframe"
    PARAMETER = "Parameter"
    VISUAL_EXAMPLE = "VisualExample"
    
    # Rule types
    SETUP = "setup"
    ENTRY = "entry"
    EXIT = "exit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    CONFIRMATION = "confirmation"
    INVALIDATION = "invalidation"
    FILTER = "filter"
    POSITION_sizing = "position_sizing"
    AVOIDANCE = "avoidance"
    
    def __init__(self, api_base: str = None, api_key: str = None, model: str = None,
                 sqlite_store: SQLiteStore = None, file_store: FileStore = None):
        self.api_base = api_base or settings.qwen_api_base
        self.api_key = api_key or settings.qwen_api_key
        self.model = model or settings.qwen_model
        
        self.qwen_client = QwenClient(
            api_base=self.api_base,
            api_key=self.api_key,
            model=self.model
        )
        
        self.sqlite = sqlite_store or SQLiteStore()
        self.files = file_store or FileStore()
    
    def extract_knowledge(self, segment: Dict[str, Any], video_id: str) -> Dict[str, Any]:
        """Extract knowledge from a multimodal segment.
        
        Args:
            segment: The segment object with transcript, OCR, and visual context
            video_id: The video ID
        
        Returns:
            Extracted knowledge with entities and relationships
        """
        # Build extraction prompt
        prompt = self._build_extraction_prompt(segment, video_id)
        
        # Add JSON schema for expected output
        schema = {
            "type": "object",
            "properties": {
                "strategies": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "market_context": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                },
                "concepts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"}
                        }
                    }
                },
                "indicators": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {"type": "string"},
                            "description": {"type": "string"}
                        }
                    }
                },
                "rules": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "rule_type": {"type": "string", "enum": ["setup", "entry", "exit", "stop_loss", "take_profit", "confirmation", "invalidation", "filter", "avoidance"]},
                            "text": {"type": "string"},
                            "is_bot_ready": {"type": "boolean"},
                            "confidence": {"type": "number"},
                            "evidence": {"type": "string"}
                        }
                    }
                },
                "conditions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "machine_checkable": {"type": "boolean"}
                        }
                    }
                },
                "relationships": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "subject": {"type": "string"},
                            "subject_type": {"type": "string"},
                            "predicate": {"type": "string"},
                            "object": {"type": "string"},
                            "object_type": {"type": "string"},
                            "confidence": {"type": "number"},
                            "evidence": {"type": "string"}
                        }
                    }
                }
            }
        }
        
        try:
            # Call Qwen for extraction
            result = self.qwen_client.generate_json(
                prompt,
                schema=schema,
                system_prompt="You are extracting structured trading knowledge from video segments."
            )
            
            # Process and store extracted entities
            entities = []
            relationships = []
            
            # Process strategies
            for strategy in result.get("strategies", []):
                entity_id = str(uuid.uuid4())
                entities.append(self._create_entity(
                    entity_id=entity_id,
                    name=strategy["name"],
                    entity_type=self.STRATEGY,
                    description=strategy.get("description", ""),
                    source_segment_id=segment["segment_id"],
                    confidence=0.9
                ))
                
                # Store strategy
                self.sqlite.create_entity(
                    entity_id=entity_id,
                    name=strategy["name"],
                    entity_type=self.STRATEGY,
                    description=strategy.get("description", ""),
                    source_segment_id=segment["segment_id"],
                    confidence=0.9
                )
            
            # Process concepts
            for concept in result.get("concepts", []):
                entity_id = str(uuid.uuid4())
                entities.append(self._create_entity(
                    entity_id=entity_id,
                    name=concept["name"],
                    entity_type=self.CONCEPT,
                    description=concept.get("description", ""),
                    source_segment_id=segment["segment_id"],
                    confidence=0.85
                ))
                
                self.sqlite.create_entity(
                    entity_id=entity_id,
                    name=concept["name"],
                    entity_type=self.CONCEPT,
                    description=concept.get("description", ""),
                    source_segment_id=segment["segment_id"],
                    confidence=0.85
                )
            
            # Process indicators
            for indicator in result.get("indicators", []):
                entity_id = str(uuid.uuid4())
                entities.append(self._create_entity(
                    entity_id=entity_id,
                    name=indicator["name"],
                    entity_type=self.INDICATOR,
                    description=indicator.get("description", ""),
                    source_segment_id=segment["segment_id"],
                    confidence=0.9
                ))
                
                self.sqlite.create_entity(
                    entity_id=entity_id,
                    name=indicator["name"],
                    entity_type=self.INDICATOR,
                    description=indicator.get("description", ""),
                    source_segment_id=segment["segment_id"],
                    confidence=0.9
                )
            
            # Process rules
            for rule in result.get("rules", []):
                entity_id = str(uuid.uuid4())
                entities.append(self._create_entity(
                    entity_id=entity_id,
                    name=rule["name"],
                    entity_type=self.RULE,
                    description=rule.get("text", ""),
                    source_segment_id=segment["segment_id"],
                    confidence=rule.get("confidence", 0.8)
                ))
                
                self.sqlite.create_entity(
                    entity_id=entity_id,
                    name=rule["name"],
                    entity_type=self.RULE,
                    description=rule.get("text", ""),
                    source_segment_id=segment["segment_id"],
                    confidence=rule.get("confidence", 0.8)
                )
                
                # Store rule info
                rule_node = {
                    "id": entity_id,
                    "type": self.RULE,
                    "rule_type": rule["rule_type"],
                    "text": rule["text"],
                    "is_bot_ready": rule["is_bot_ready"],
                    "confidence": rule["confidence"]
                }
                
                # Create relationships for rules
                if rule["rule_type"] in ["entry", "exit", "stop_loss", "take_profit"]:
                    for strategy in result.get("strategies", []):
                        relationships.append({
                            "subject": strategy["name"],
                            "subject_type": self.STRATEGY,
                            "predicate": "HAS_RULE",
                            "object": rule["name"],
                            "object_type": self.RULE,
                            "confidence": rule["confidence"],
                            "evidence": rule.get("evidence", "")
                        })
            
            # Process conditions
            for condition in result.get("conditions", []):
                entity_id = str(uuid.uuid4())
                entities.append(self._create_entity(
                    entity_id=entity_id,
                    name=condition["name"],
                    entity_type=self.CONDITION,
                    description=condition.get("description", ""),
                    source_segment_id=segment["segment_id"],
                    confidence=0.75
                ))
                
                self.sqlite.create_entity(
                    entity_id=entity_id,
                    name=condition["name"],
                    entity_type=self.CONDITION,
                    description=condition.get("description", ""),
                    source_segment_id=segment["segment_id"],
                    confidence=0.75
                )
            
            # Process relationships
            for rel in result.get("relationships", []):
                self.sqlite.create_relationship(
                    rel_id=str(uuid.uuid4()),
                    subject=rel["subject"],
                    subject_type=rel["subject_type"],
                    predicate=rel["predicate"],
                    object_=rel["object"],
                    object_type=rel["object_type"],
                    confidence=rel["confidence"],
                    evidence=rel["evidence"]
                )
                relationships.append(rel)
            
            return {
                "segment_id": segment["segment_id"],
                "video_id": video_id,
                "entities": entities,
                "relationships": relationships,
                "raw_extraction": result
            }
            
        except Exception as e:
            print(f"Error extracting knowledge from {segment.get('segment_id', 'unknown')}: {e}")
            return {
                "segment_id": segment.get("segment_id"),
                "video_id": video_id,
                "error": str(e)
            }
    
    def _build_extraction_prompt(self, segment: Dict[str, Any], video_id: str) -> str:
        """Build the extraction prompt."""
        prompt = f"""You are extracting structured trading knowledge from a multimodal video segment.

Video ID: {video_id}
Segment ID: {segment.get("segment_id", "unknown")}
Time range: {segment.get("start_time", 0):.1f}s - {segment.get("end_time", 0):.1f}s

Transcript:
{segment.get("transcript", "")}

OCR Text:
{segment.get("ocr_text", "")}

Visual Summary:
{segment.get("visual_summary", "")}

Extract the following information:

1. STRATEGIES: Named trading strategies or approaches described
2. CONCEPTS: Key trading concepts or theories
3. INDICATORS: Technical indicators mentioned (RSI, MACD, Moving Averages, etc.)
4. RULES: Trading rules (entry, exit, stop loss, take profit, confirmation, invalidation)
5. CONDITIONS: Specific conditions or requirements for trades
6. RELATIONSHIPS: How strategies, concepts, and rules relate to each other

For each item:
- Extract only what is explicitly stated or clearly implied
- Classify rules as bot_ready if they can be executed by a bot without human discretion
- Include confidence scores
- Cite evidence from the segment

Return your results as structured JSON with:
- strategies: Array of strategy objects
- concepts: Array of concept objects  
- indicators: Array of indicator objects
- rules: Array of rule objects
- conditions: Array of condition objects
- relationships: Array of relationship objects between entities
"""

        return prompt
    
    def _create_entity(self, entity_id: str, name: str, entity_type: str,
                      description: str, source_segment_id: str, confidence: float) -> Dict[str, Any]:
        """Create an entity object."""
        return {
            "id": entity_id,
            "name": name,
            "type": entity_type,
            "description": description,
            "source_segment_id": source_segment_id,
            "confidence": confidence
        }


def extract_knowledge(segment: Dict[str, Any], video_id: str) -> Dict[str, Any]:
    """Convenience function to extract knowledge from a segment."""
    extractor = KnowledgeExtractor()
    return extractor.extract_knowledge(segment, video_id)
