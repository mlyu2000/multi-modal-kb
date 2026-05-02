#!/usr/bin/env python3
"""Graph queries for Trading KB."""

from typing import Dict, Any, List, Optional

from src.storage.neo4j_store import Neo4jStore


class GraphQueries:
    """Common graph queries for Trading KB."""
    
    def __init__(self, neo4j_store: Neo4jStore = None):
        self.neo4j = neo4j_store or Neo4jStore()
    
    def find_strategy_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find a strategy by name."""
        query = """
        MATCH (s:Strategy {name: $name})
        RETURN s
        """
        results = self.neo4j.execute_query(query, {"name": name})
        if results:
            return results[0].get("s", {})
        return None
    
    def find_rules_by_type(self, rule_type: str) -> List[Dict[str, Any]]:
        """Find all rules of a given type."""
        query = """
        MATCH (r:Rule {rule_type: $type})
        RETURN r.id AS id, r.name AS name, r.rule_type AS rule_type, r.is_bot_ready AS is_bot_ready
        ORDER BY r.name
        """
        return self.neo4j.execute_query(query, {"type": rule_type})
    
    def find_entities_connected_to(self, entity_id: str, entity_type: str) -> List[Dict[str, Any]]:
        """Find all entities connected to a given entity."""
        query = """
        MATCH (n {id: $id, type: $type})
        OPTIONAL MATCH (n)-[r]->(target)
        RETURN n.id AS source_id, type(r) AS relationship, target.id AS target_id, labels(target)[0] AS target_type, r.confidence AS confidence
        UNION
        MATCH (n {id: $id, type: $type})
        OPTIONAL MATCH (n)<-[r]-(source)
        RETURN n.id AS source_id, type(r) AS relationship, source.id AS target_id, labels(source)[0] AS target_type, r.confidence AS confidence
        ORDER BY relationship, target_id
        """
        return self.neo4j.execute_query(query, {"id": entity_id, "type": entity_type})
    
    def find_path_between(self, start_id: str, end_id: str, max_depth: int = 3) -> List[List[Dict[str, Any]]]:
        """Find paths between two entities."""
        query = f"""
        MATCH path = (start {{id: $start_id}})-[*1..{max_depth}]-(end {{id: $end_id}})
        RETURN path
        """
        results = self.neo4j.execute_query(query, {"start_id": start_id, "end_id": end_id})
        
        paths = []
        for record in results:
            path_data = record.get("path", {})
            if path_data:
                paths.append(path_data)
        return paths
    
    def get_all_strategies(self) -> List[Dict[str, Any]]:
        """Get all strategies."""
        query = """
        MATCH (s:Strategy)
        RETURN s.id AS id, s.name AS name, s.description AS description, s.confidence AS confidence
        ORDER BY s.name
        """
        return self.neo4j.execute_query(query)
    
    def get_all_rules(self) -> List[Dict[str, Any]]:
        """Get all rules."""
        query = """
        MATCH (r:Rule)
        RETURN r.id AS id, r.name AS name, r.rule_type AS rule_type, r.is_bot_ready AS is_bot_ready, r.confidence AS confidence
        ORDER BY r.rule_type, r.name
        """
        return self.neo4j.execute_query(query)
    
    def get_all_indicators(self) -> List[Dict[str, Any]]:
        """Get all indicators."""
        query = """
        MATCH (i:Indicator)
        RETURN i.id AS id, i.name AS name, i.description AS description, i.confidence AS confidence
        ORDER BY i.name
        """
        return self.neo4j.execute_query(query)
    
    def find_rules_for_bot(self, strategy_name: str) -> Dict[str, Any]:
        """Find all rules needed for a bot for a given strategy."""
        query = """
        MATCH (s:Strategy {name: $name})<-[r1:HAS_RULE]-(rule:Rule)
        WITH s, collect(rule) AS all_rules
        
        MATCH (s)<-[r2:USES]-(i:Indicator)
        WITH s, all_rules, collect(i) AS indicators
        
        MATCH (s)-[r3:WORKS_IN]->(ctx:MarketContext)
        WITH s, all_rules, indicators, collect(ctx) AS contexts
        
        RETURN {
            strategy: s.name,
            rules: [r IN all_rules | {
                name: r.name,
                rule_type: r.rule_type,
                is_bot_ready: r.is_bot_ready
            }],
            indicators: [i IN indicators | i.name],
            market_contexts: [c IN contexts | c.name]
        } AS result
        """
        results = self.neo4j.execute_query(query, {"name": strategy_name})
        if results:
            return results[0].get("result", {})
        return {}
    
    def get_completeness_for_strategy(self, strategy_name: str) -> Dict[str, Any]:
        """Get completeness check for a strategy."""
        query = """
        MATCH (s:Strategy {name: $name})<-[r:HAS_RULE]-(rule:Rule)
        WITH s, collect(DISTINCT rule.rule_type) AS rule_types
        
        // Check for required rule types
        WITH s, rule_types,
             "setup" IN rule_types AS has_setup,
             "entry" IN rule_types AS has_entry,
             "exit" IN rule_types AS has_exit,
             "stop_loss" IN rule_types AS has_stop_loss,
             "invalidation" IN rule_types AS has_invalidation,
             "position_sizing" IN rule_types AS has_position_sizing
        
        // Get market context
        MATCH (s)-[r:WORKS_IN]->(ctx:MarketContext)
        WITH s, rule_types, has_setup, has_entry, has_exit, has_stop_loss, has_invalidation, has_position_sizing,
             collect(ctx.name) AS contexts
        
        // Get indicators
        MATCH (s)<-[r:USES]-(i:Indicator)
        WITH s, rule_types, has_setup, has_entry, has_exit, has_stop_loss, has_invalidation, has_position_sizing, contexts,
             collect(i.name) AS indicators
        
        // Get timeframe
        MATCH (s)-[r:USES_TIMEFRAME]->(tf:Timeframe)
        WITH s, rule_types, has_setup, has_entry, has_exit, has_stop_loss, has_invalidation, has_position_sizing, contexts, indicators,
             collect(tf.name) AS timeframes
        
        RETURN {
            strategy: s.name,
            has_setup: has_setup,
            has_entry: has_entry,
            has_exit: has_exit,
            has_stop_loss: has_stop_loss,
            has_invalidation: has_invalidation,
            has_position_sizing: has_position_sizing,
            market_contexts: contexts,
            indicators: indicators,
            timeframes: timeframes,
            is_complete: has_setup AND has_entry AND has_exit AND has_stop_loss AND has_invalidation AND has_position_sizing
        } AS result
        """
        results = self.neo4j.execute_query(query, {"name": strategy_name})
        if results:
            return results[0].get("result", {})
        return {"is_complete": False}


    def search_knowledge_by_category(self, query: str, category: str, 
                                     n_results: int = 5) -> List[Dict]:
        """
        Search knowledge graph with category filter.
        
        Args:
            query: Search query text
            category: Category to filter by
            n_results: Maximum results to return
        """
        # First search by entity labels, then filter by category
        results = self.driver.session().run("""
            MATCH (e:Entity)-[:MENTIONED_IN]->(s:Segment)-[:PART_OF]->(v:Video)
            WHERE s.text CONTAINS $query AND v.category = $category
            RETURN e.name as entity, e.type as entity_type, 
                   s.text as segment_text, v.category as category,
                   s.start_sec as start, s.end_sec as end
            LIMIT $n_results
        """, query=query, category=category, n_results=n_results)
        
        return [dict(r) for r in results]

    def get_category_stats(self) -> Dict[str, int]:
        """Get segment counts by category."""
        results = self.driver.session().run("""
            MATCH (v:Video)
            RETURN v.category as category, count(*) as segment_count
            ORDER BY segment_count DESC
        """)
        
        return {r["category"]: r["segment_count"] for r in results}

    def get_school_of_thought_stats(self) -> Dict[str, int]:
        """Get segment counts by school of thought."""
        results = self.driver.session().run("""
            MATCH (v:Video)
            RETURN v.school_of_thought as school, count(*) as segment_count
            ORDER BY segment_count DESC
        """)
        
        return {r["school"]: r["segment_count"] for r in results}
