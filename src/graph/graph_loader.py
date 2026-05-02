#!/usr/bin/env python3
"""Graph loader for Trading KB."""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

from ..config.settings import settings
from src.storage.neo4j_store import Neo4jStore
from src.extraction.entity_normalizer import EntityNormalizer
from .graph_schema import (
    STRATEGY, CONCEPT, INDICATOR, RULE, CONDITION, 
    MARKET_CONTEXT, ASSET_CLASS, TIMEFRAME, PARAMETER, VISUAL_EXAMPLE
)


class GraphLoader:
    """Load extracted knowledge into Neo4j graph."""
    
    def __init__(self, neo4j_store: Neo4jStore = None, normalizer: EntityNormalizer = None):
        self.neo4j = neo4j_store or Neo4jStore()
        self.normalizer = normalizer or EntityNormalizer()
    
    def load_video(self, video_id: str, segments: List[Dict[str, Any]]) -> bool:
        """Load a video and its segments into the graph.
        
        Args:
            video_id: The video ID
            segments: List of segment dictionaries
        
        Returns:
            Success status
        """
        # Create Video node
        self.neo4j.create_node(
            label=Neo4jStore.VIDEO,
            node_id=video_id,
            properties={
                "id": video_id,
                "type": Neo4jStore.VIDEO,
                "source": "trading_kb"
            }
        )
        
        for segment in segments:
            # Create Segment node
            self.neo4j.create_node(
                label=Neo4jStore.SEGMENT,
                node_id=segment["segment_id"],
                properties={
                    "id": segment["segment_id"],
                    "start_time": segment.get("start_time", 0),
                    "end_time": segment.get("end_time", 0),
                    "summary": segment.get("transcript", "")[:200]
                }
            )
            
            # Link to video
            self.neo4j.create_relationship(
                subject_id=video_id,
                subject_type=Neo4jStore.VIDEO,
                predicate=Neo4jStore.HAS_SEGMENT,
                object_id=segment["segment_id"],
                object_type=Neo4jStore.SEGMENT
            )
            
            # Create Frame nodes
            keyframes = segment.get("keyframes", [])
            for i, frame_path in enumerate(keyframes):
                # Use frame filename stem to avoid collision
                frame_id = Path(frame_path).stem
                if not frame_id:
                    frame_id = f"{video_id}_{segment['segment_id']}_frame_{i}"
                self.neo4j.create_node(
                    label=Neo4jStore.FRAME,
                    node_id=frame_id,
                    properties={
                        "id": frame_id,
                        "path": frame_path
                    }
                )
                
                self.neo4j.create_relationship(
                    subject_id=segment["segment_id"],
                    subject_type=Neo4jStore.SEGMENT,
                    predicate=Neo4jStore.HAS_FRAME,
                    object_id=frame_id,
                    object_type=Neo4jStore.FRAME
                )
        
        return True
    
    def load_entities(self, entities: List[Dict[str, Any]]) -> bool:
        """Load entities into the graph.
        
        Args:
            entities: List of entity dictionaries
        
        Returns:
            Success status
        """
        for entity in entities:
            # Normalize the entity name
            norm = self.normalizer.normalize(entity["name"], entity["type"])
            
            # Create node
            self.neo4j.create_node(
                label=entity["type"],
                node_id=entity["id"],
                properties={
                    "id": entity["id"],
                    "name": norm["canonical_name"],
                    "raw_name": entity["name"],
                    "type": entity["type"],
                    "description": entity.get("description", ""),
                    "confidence": entity.get("confidence", 0.5)
                }
            )
        
        return True
    
    def load_relationships(self, relationships: List[Dict[str, Any]]) -> bool:
        """Load relationships into the graph.
        
        Args:
            relationships: List of relationship dictionaries
        
        Returns:
            Success status
        """
        for rel in relationships:
            self.neo4j.create_relationship(
                subject_id=rel["subject"],
                subject_type=rel["subject_type"],
                predicate=rel["predicate"],
                object_id=rel["object"],
                object_type=rel["object_type"],
                properties={
                    "confidence": rel.get("confidence", 0.5),
                    "evidence": rel.get("evidence", "")
                }
            )
        
        return True
    
    def load_knowledge(self, video_id: str, knowledge: Dict[str, Any]) -> bool:
        """Load extracted knowledge for a video.
        
        Args:
            video_id: The video ID
            knowledge: The extracted knowledge dictionary
        
        Returns:
            Success status
        """
        # Load entities
        if "entities" in knowledge:
            self.load_entities(knowledge["entities"])
        
        # Load relationships
        if "relationships" in knowledge:
            self.load_relationships(knowledge["relationships"])
        
        return True
    
    def get_strategies(self) -> List[Dict[str, Any]]:
        """Get all strategies from the graph."""
        query = """
        MATCH (s:Strategy)
        RETURN s.id AS id, s.name AS name, s.description AS description, s.confidence AS confidence
        ORDER BY s.name
        """
        return self.neo4j.execute_query(query)
    
    def get_rules_for_strategy(self, strategy_name: str) -> List[Dict[str, Any]]:
        """Get rules associated with a strategy."""
        query = """
        MATCH (s:Strategy {name: $name})-[r:HAS_RULE]->(rule:Rule)
        RETURN rule.id AS id, rule.name AS name, rule.rule_type AS rule_type, r.confidence AS confidence, r.evidence AS evidence
        ORDER BY rule.rule_type
        """
        return self.neo4j.execute_query(query, {"name": strategy_name})
    
    def get_indicators_for_strategy(self, strategy_name: str) -> List[Dict[str, Any]]:
        """Get indicators used by a strategy."""
        query = """
        MATCH (s:Strategy {name: $name})<-[r:USES]-(i:Indicator)
        RETURN i.id AS id, i.name AS name, i.description AS description, r.confidence AS confidence
        ORDER BY i.name
        """
        return self.neo4j.execute_query(query, {"name": strategy_name})
    
    def find_similar_strategies(self, strategy_name: str) -> List[Dict[str, Any]]:
        """Find strategies that can combine with the given strategy."""
        query = """
        MATCH (s1:Strategy {name: $name})-[r:CAN_COMBINE_WITH]->(s2:Strategy)
        RETURN s2.name AS name, s2.description AS description, r.confidence AS confidence
        UNION
        MATCH (s1:Strategy {name: $name})<-[r:CAN_COMBINE_WITH]-(s2:Strategy)
        RETURN s2.name AS name, s2.description AS description, r.confidence AS confidence
        ORDER BY name
        """
        return self.neo4j.execute_query(query, {"name": strategy_name})
