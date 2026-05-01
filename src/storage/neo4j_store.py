#!/usr/bin/env python3
"""Neo4j graph store for trading KB."""

import os

from typing import Optional, Dict, Any, List
import time

try:
    from neo4j import GraphDatabase, Driver
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False


class Neo4jStore:
    """Neo4j graph store for trading KB."""
    
    # Node labels
    VIDEO = "Video"
    SEGMENT = "Segment"
    FRAME = "Frame"
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
    BOT_SPEC = "BotSpec"
    PLATFORM = "Platform"
    
    # Relationship types
    HAS_SEGMENT = "HAS_SEGMENT"
    HAS_FRAME = "HAS_FRAME"
    MENTIONS = "MENTIONS"
    SUPPORTS = "SUPPORTS"
    EXPLAINS = "EXPLAINS"
    SHOWS = "SHOWS"
    DERIVED_FROM = "DERIVED_FROM"
    BASED_ON = "BASED_ON"
    USES = "USES"
    HAS_RULE = "HAS_RULE"
    WORKS_IN = "WORKS_IN"
    AVOIDS = "AVOIDS"
    APPLIES_TO = "APPLIES_TO"
    USES_TIMEFRAME = "USES_TIMEFRAME"
    REQUIRES = "REQUIRES"
    REQUIRES_CONDITION = "REQUIRES_CONDITION"
    TRIGGERS = "TRIGGERS"
    CONFIRMS = "CONFIRMS"
    INVALIDATES = "INVALIDATES"
    CONFLICTS_WITH = "CONFLICTS_WITH"
    COMPLEMENTS = "COMPLEMENTS"
    PARAMETERIZED_BY = "PARAMETERIZED_BY"
    RELATED_TO = "RELATED_TO"
    IS_TYPE_OF = "IS_TYPE_OF"
    CAN_COMBINE_WITH = "CAN_COMBINE_WITH"
    IMPLEMENTED_BY = "IMPLEMENTED_BY"
    TARGETS = "TARGETS"
    USES_RULE = "USES_RULE"
    REQUIRES_PARAMETER = "REQUIRES_PARAMETER"
    
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        if not NEO4J_AVAILABLE:
            raise ImportError("neo4j is not installed. Install with: pip install neo4j")
        
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "")
        
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        self._verify_connection()
    
    def _verify_connection(self):
        """Verify Neo4j connection."""
        try:
            with self.driver.session() as session:
                session.run("RETURN 1 AS result").single()
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Neo4j: {e}")
    
    def close(self):
        """Close Neo4j connection."""
        self.driver.close()
    
    def create_node(self, label: str, node_id: str, properties: Dict[str, Any] = None) -> bool:
        """Create or merge a node."""
        properties = properties or {}
        properties["id"] = node_id
        properties["type"] = label
        properties["review_status"] = properties.get("review_status", "unreviewed")
        properties["created_at"] = properties.get("created_at", time.strftime("%Y-%m-%dT%H:%M:%SZ"))
        
        props_str = ", ".join([f"n.{k} = ${k}" for k in properties.keys()])
        
        query = f"""
        MERGE (n:{label} {{id: $id}})
        ON CREATE SET {props_str}
        ON MATCH SET {props_str}
        RETURN n
        """
        
        try:
            with self.driver.session() as session:
                session.run(query, **properties).single()
            return True
        except Exception as e:
            print(f"Error creating node {label} {node_id}: {e}")
            return False
    
    def create_relationship(self, subject_id: str, subject_type: str, 
                           predicate: str, object_id: str, object_type: str,
                           properties: Dict[str, Any] = None) -> bool:
        """Create or merge a relationship."""
        properties = properties or {}
        properties["predicate"] = predicate
        properties["confidence"] = properties.get("confidence", 0.5)
        properties["review_status"] = properties.get("review_status", "unreviewed")
        properties["created_at"] = properties.get("created_at", time.strftime("%Y-%m-%dT%H:%M:%SZ"))
        
        query = f"""
        MATCH (a), (b)
        WHERE a.id = $subject_id AND labels(a)[0] = $subject_type
          AND b.id = $object_id AND labels(b)[0] = $object_type
        MERGE (a)-[r:{predicate}]->(b)
        ON CREATE SET r += $props
        ON MATCH SET r += $props
        RETURN r
        """
        
        props = {
            "subject_id": subject_id,
            "subject_type": subject_type,
            "object_id": object_id,
            "object_type": object_type,
            "props": properties
        }
        
        try:
            with self.driver.session() as session:
                session.run(query, **props).single()
            return True
        except Exception as e:
            print(f"Error creating relationship {subject_type} -[{predicate}]-> {object_type}: {e}")
            return False
    
    def get_node(self, label: str, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a node by label and ID."""
        query = f"MATCH (n:{label} {{id: $id}}) RETURN n"
        try:
            with self.driver.session() as session:
                result = session.run(query, id=node_id).single()
                if result:
                    node = result["n"]
                    return {
                        "id": node.get("id"),
                        "type": node.get("type", label),
                        **{k: v for k, v in dict(node).items() if k not in ["id", "type"]}
                    }
        except Exception as e:
            print(f"Error getting node {label} {node_id}: {e}")
        return None
    
    def get_relationships(self, node_id: str, node_type: str, 
                         direction: str = "outgoing") -> List[Dict[str, Any]]:
        """Get relationships for a node."""
        if direction == "outgoing":
            query = """
            MATCH (a)-[r]->(b)
            WHERE a.id = $node_id AND labels(a)[0] = $node_type
            RETURN r, b
            """
        elif direction == "incoming":
            query = """
            MATCH (a)-[r]->(b)
            WHERE b.id = $node_id AND labels(b)[0] = $node_type
            RETURN r, a
            """
        else:
            query = """
            MATCH (a)-[r]-(b)
            WHERE a.id = $node_id OR b.id = $node_id
            RETURN r, CASE WHEN a.id = $node_id THEN b ELSE a END AS other
            """
        
        try:
            with self.driver.session() as session:
                results = session.run(query, node_id=node_id)
                relationships = []
                for record in results:
                    rel = record["r"]
                    other = record["other"]
                    relationships.append({
                        "type": type(rel).__name__,
                        "predicate": rel.get("predicate", ""),
                        "confidence": rel.get("confidence", 0.5),
                        "evidence": rel.get("evidence", ""),
                        "other_id": other.get("id"),
                        "other_type": labels(other)[0]
                    })
                return relationships
        except Exception as e:
            print(f"Error getting relationships for {node_type} {node_id}: {e}")
            return []
    
    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a raw Cypher query."""
        try:
            with self.driver.session() as session:
                results = session.run(query, parameters or {})
                return [dict(record) for record in results]
        except Exception as e:
            print(f"Error executing query: {e}")
            return []
    
    def clear_graph(self):
        """Clear all data from the graph."""
        query = "MATCH (n) DETACH DELETE n"
        try:
            with self.driver.session() as session:
                session.run(query)
            return True
        except Exception as e:
            print(f"Error clearing graph: {e}")
            return False
