#!/usr/bin/env python3
"""Graph retrieval module using Neo4j."""

from typing import Dict, Any, List, Optional

from src.storage.neo4j_store import Neo4jStore


class GraphRetriever:
    """Retrieve knowledge using graph traversal."""
    
    def __init__(self, neo4j_store: Neo4jStore = None):
        self.neo4j = neo4j_store or Neo4jStore()
    
    def traverse_from_entity(self, entity_id: str, entity_type: str, 
                            max_depth: int = 2) -> Dict[str, Any]:
        """Traverse the graph from an entity.
        
        Args:
            entity_id: Starting entity ID
            entity_type: Type of starting entity
            max_depth: Maximum traversal depth
        
        Returns:
            Dictionary with nodes and relationships found
        """
        query = f"""
        MATCH (start {{id: $id, type: $type}})
        OPTIONAL MATCH path = (start)-[*1..{max_depth}]-(connected)
        RETURN start, collect(DISTINCT connected) AS connected_nodes, collect(DISTINCT relationships(path)) AS relationships
        """
        
        results = self.neo4j.execute_query(query, {"id": entity_id, "type": entity_type})
        if results:
            return results[0]
        return {"start": None, "connected_nodes": [], "relationships": []}
    
    def find_strategies_using_indicator(self, indicator_name: str) -> List[Dict[str, Any]]:
        """Find strategies that use a specific indicator.
        
        Args:
            indicator_name: Indicator name
        
        Returns:
            List of strategies
        """
        query = """
        MATCH (i:Indicator {name: $name})<-[:USES]-(s:Strategy)
        RETURN s.id AS id, s.name AS name, s.description AS description
        ORDER BY s.name
        """
        return self.neo4j.execute_query(query, {"name": indicator_name})
    
    def find_strategies_compatible_with(self, strategy_name: str) -> List[Dict[str, Any]]:
        """Find strategies that can combine with the given strategy.
        
        Args:
            strategy_name: Strategy name
        
        Returns:
            List of compatible strategies
        """
        query = """
        MATCH (s:Strategy {name: $name})-[r:CAN_COMBINE_WITH]->(other:Strategy)
        RETURN other.id AS id, other.name AS name, other.description AS description, r.confidence AS confidence
        UNION
        MATCH (s:Strategy {name: $name})<-[r:CAN_COMBINE_WITH]-(other:Strategy)
        RETURN other.id AS id, other.name AS name, other.description AS description, r.confidence AS confidence
        ORDER BY name
        """
        return self.neo4j.execute_query(query, {"name": strategy_name})
    
    def find_rules_conflicting_with(self, rule_name: str) -> List[Dict[str, Any]]:
        """Find rules that conflict with the given rule.
        
        Args:
            rule_name: Rule name
        
        Returns:
            List of conflicting rules
        """
        query = """
        MATCH (r:Rule {name: $name})-[r2:CONFLICTS_WITH]->(other:Rule)
        RETURN other.id AS id, other.name AS name, other.rule_type AS rule_type, r2.evidence AS evidence
        ORDER BY other.name
        """
        return self.neo4j.execute_query(query, {"name": rule_name})
    
    def get_path_to_rule(self, strategy_name: str, rule_type: str) -> List[Dict[str, Any]]:
        """Get the path from a strategy to a rule of a specific type.
        
        Args:
            strategy_name: Strategy name
            rule_type: Rule type (entry, exit, stop_loss, etc.)
        
        Returns:
            Path information
        """
        query = """
        MATCH (s:Strategy {name: $name})-[r:HAS_RULE]->(rule:Rule {rule_type: $type})
        RETURN s.name AS strategy, rule.name AS rule, rule.text AS rule_text, r.confidence AS confidence
        """
        return self.neo4j.execute_query(query, {"name": strategy_name, "type": rule_type})
    
    def get_completeness_report(self, strategy_name: str) -> Dict[str, Any]:
        """Get completeness report for a strategy.
        
        Args:
            strategy_name: Strategy name
        
        Returns:
           Completeness report with missing components
        """
        query = """
        MATCH (s:Strategy {name: $name})<-[r:HAS_RULE]-(rule:Rule)
        WITH s, collect(DISTINCT rule.rule_type) AS rule_types
        
        WITH s, rule_types,
             "entry" IN rule_types AS has_entry,
             "exit" IN rule_types AS has_exit,
             "stop_loss" IN rule_types AS has_stop_loss,
             "invalidation" IN rule_types AS has_invalidation
        
        MATCH (s)-[r:WORKS_IN]->(ctx:MarketContext)
        WITH s, rule_types, has_entry, has_exit, has_stop_loss, has_invalidation,
             collect(ctx.name) AS contexts
        
        MATCH (s)<-[r:USES]-(i:Indicator)
        WITH s, rule_types, has_entry, has_exit, has_stop_loss, has_invalidation, contexts,
             collect(i.name) AS indicators
        
        MATCH (s)-[r:USES_TIMEFRAME]->(tf:Timeframe)
        WITH s, rule_types, has_entry, has_exit, has_stop_loss, has_invalidation, contexts, indicators,
             collect(tf.name) AS timeframes
        
        RETURN {
            strategy: s.name,
            has_entry: has_entry,
            has_exit: has_exit,
            has_stop_loss: has_stop_loss,
            has_invalidation: has_invalidation,
            missing: [
                CASE WHEN NOT has_entry THEN "entry_rule" ELSE null END,
                CASE WHEN NOT has_exit THEN "exit_rule" ELSE null END,
                CASE WHEN NOT has_stop_loss THEN "stop_loss_rule" ELSE null END,
                CASE WHEN NOT has_invalidation THEN "invalidation_rule" ELSE null END
            ],
            contexts: contexts,
            indicators: indicators,
            timeframes: timeframes
        } AS result
        """
        results = self.neo4j.execute_query(query, {"name": strategy_name})
        if results:
            return results[0].get("result", {"is_complete": False})
        return {"is_complete": False}
