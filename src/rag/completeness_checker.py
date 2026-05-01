#!/usr/bin/env python3
"""Strategy completeness checker for Trading KB."""

from typing import Dict, Any, List, Optional

from src.storage.neo4j_store import Neo4jStore


class CompletenessChecker:
    """Check if a trading strategy has all required components for bot implementation."""
    
    REQUIRED_RULE_TYPES = [
        "setup", "entry", "exit", "stop_loss", "invalidation", "position_sizing"
    ]
    
    def __init__(self, neo4j_store: Neo4jStore = None):
        self.neo4j = neo4j_store or Neo4jStore()
    
    def check(self, strategy_name: str) -> Dict[str, Any]:
        """Check completeness of a strategy.
        
        Args:
            strategy_name: Name of the strategy to check
        
        Returns:
            Completeness report
        """
        # Get strategy rules from Neo4j
        query = """
        MATCH (s:Strategy {name: $name})<-[r:HAS_RULE]-(rule:Rule)
        RETURN collect(DISTINCT rule.rule_type) AS rule_types,
               collect(DISTINCT rule.name) AS rule_names,
               collect(DISTINCT rule.text) AS rule_texts
        """
        results = self.neo4j.execute_query(query, {"name": strategy_name})
        
        if not results or not results[0]:
            return {
                "is_complete": False,
                "missing": ["all_rules"],
                "questions": [
                    f"Which rules does the '{strategy_name}' strategy use?",
                    "What is the entry condition?",
                    "What is the exit condition?",
                    "How is risk managed?"
                ]
            }
        
        rule_data = results[0]
        rule_types = rule_data.get("rule_types", [])
        rule_names = rule_data.get("rule_names", [])
        rule_texts = rule_data.get("rule_texts", [])
        
        # Check for required rule types
        missing_types = []
        for req_type in self.REQUIRED_RULE_TYPES:
            if req_type not in rule_types:
                missing_types.append(req_type)
        
        # Get other strategy properties
        completeness = self._get_strategy_properties(strategy_name)
        
        missing = []
        questions = []
        
        # Check missing rule types
        for missing_type in missing_types:
            missing.append(f"{missing_type}_rule")
            questions.append(f"What is the {missing_type.replace('_', ' ')} rule?")
        
        # Check for indicator parameters
        if not completeness.get("indicators"):
            missing.append("indicator_parameters")
            questions.append("Which indicators does this strategy use and with what parameters?")
        
        # Check for timeframe
        if not completeness.get("timeframes"):
            missing.append("timeframe")
            questions.append("Which timeframe should this bot target?")
        
        # Check for asset class
        if not completeness.get("asset_class"):
            missing.append("asset_class")
            questions.append("Which asset class should this bot trade?")
        
        is_complete = len(missing) == 0
        
        return {
            "is_complete": is_complete,
            "strategy_name": strategy_name,
            "has_entry_rule": "entry" in rule_types,
            "has_exit_rule": "exit" in rule_types,
            "has_stop_loss_rule": "stop_loss" in rule_types,
            "has_invalidation_rule": "invalidation" in rule_types,
            "has_position_sizing_rule": "position_sizing" in rule_types,
            "missing": missing,
            "questions": questions,
            "rules_found": dict(zip(rule_names, rule_texts)),
            "indicators": completeness.get("indicators", []),
            "timeframes": completeness.get("timeframes", []),
            "market_context": completeness.get("market_context", [])
        }
    
    def _get_strategy_properties(self, strategy_name: str) -> Dict[str, Any]:
        """Get additional properties for a strategy."""
        query = """
        MATCH (s:Strategy {name: $name})
        OPTIONAL MATCH (s)-[r:USES]->(i:Indicator)
        OPTIONAL MATCH (s)-[r2:WORKS_IN]->(ctx:MarketContext)
        OPTIONAL MATCH (s)-[r3:USES_TIMEFRAME]->(tf:Timeframe)
        OPTIONAL MATCH (s)-[r4:TARGETS]->(a:AssetClass)
        RETURN 
            collect(DISTINCT i.name) AS indicators,
            collect(DISTINCT ctx.name) AS context,
            collect(DISTINCT tf.name) AS timeframes,
            collect(DISTINCT a.name) AS assets
        """
        results = self.neo4j.execute_query(query, {"name": strategy_name})
        
        if results and results[0]:
            data = results[0]
            return {
                "indicators": data.get("indicators", []),
                "market_context": data.get("context", []),
                "timeframes": data.get("timeframes", []),
                "asset_class": data.get("assets", [])
            }
        
        return {}
    
    def get_missing_components(self, strategy_name: str) -> Dict[str, Any]:
        """Get detailed missing components for a strategy."""
        completeness = self.check(strategy_name)
        return {
            "missing": completeness.get("missing", []),
            "questions": completeness.get("questions", [])
        }
    
    def make_strategy_bot_ready(self, strategy_name: str, 
                                user_answers: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to make a strategy bot-ready with user input.
        
        Args:
            strategy_name: Strategy name
            user_answers: User-provided answers to missing questions
        
        Returns:
            Updated completeness report
        """
        completeness = self.check(strategy_name)
        
        # Apply user answers to fill missing information
        # This is a placeholder - in production, you would update the graph
        completeness["user_answers_applied"] = user_answers
        
        return completeness
