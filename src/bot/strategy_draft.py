#!/usr/bin/env python3
"""Strategy draft generator."""

import os
from typing import Dict, Any, List, Optional

from ..rag.completeness_checker import CompletenessChecker
from ..rag.vector_retriever import VectorRetriever


class StrategyDraftGenerator:
    """Generate human-readable strategy drafts from graph evidence."""
    
    def __init__(self, completeness_checker: CompletenessChecker = None, 
                 vector_retriever: VectorRetriever = None):
        self.completeness = completeness_checker or CompletenessChecker()
        self.vector = vector_retriever or VectorRetriever()
    
    def generate(self, strategy_name: str) -> Dict[str, Any]:
        """Generate a strategy draft.
        
        Args:
            strategy_name: Name of the strategy
        
        Returns:
            Strategy draft dictionary
        """
        # Check completeness first
        completeness = self.completeness.check(strategy_name)
        
        if not completeness.get("is_complete", False):
            return {
                "strategy_name": strategy_name,
                "status": "draft_incomplete",
                "message": "Strategy is incomplete. Missing components need to be specified.",
                "missing": completeness.get("missing", []),
                "questions": completeness.get("questions", []),
                "rules_found": completeness.get("rules_found", {})
            }
        
        # Get vector results for evidence
        context = self.vector.get_context_for_query(strategy_name, n_results=10)
        
        # Generate YAML-style draft
        draft = {
            "strategy_name": strategy_name,
            "status": "draft",
            "asset_class": completeness.get("asset_class", "unresolved"),
            "timeframe": completeness.get("timeframes", ["unresolved"])[0] if completeness.get("timeframes") else "unresolved",
            "description": f"Strategy based on {strategy_name}",
            "sources": self._build_evidence(context),
            "next_steps": [
                "Verify all rules have machine-checkable conditions",
                "Backtest on historical data",
                "Optimize parameters",
                "Set up paper trading"
            ]
        }
        
        # Add rules by category
        if completeness.get("rules_found"):
            rules_by_type = {}
            for rule_name, rule_text in completeness["rules_found"].items():
                # Try to determine rule type from name
                rule_type = "unknown"
                if "entry" in rule_name.lower():
                    rule_type = "entry"
                elif "exit" in rule_name.lower():
                    rule_type = "exit"
                elif "stop" in rule_name.lower():
                    rule_type = "stop_loss"
                elif "profit" in rule_name.lower():
                    rule_type = "take_profit"
                elif "invalid" in rule_name.lower():
                    rule_type = "invalidation"
                elif "position" in rule_name.lower():
                    rule_type = "position_sizing"
                
                if rule_type not in rules_by_type:
                    rules_by_type[rule_type] = []
                rules_by_type[rule_type].append(rule_text)
            
            draft["rules_by_type"] = rules_by_type
        
        return draft
    
    def _build_evidence(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build source evidence from context."""
        evidence = []
        for segment in context.get("segments", [])[:3]:
            evidence.append({
                "type": "segment",
                "content": segment.get("document", "")[:200] + "...",
                "segment_id": segment.get("id", "unknown")
            })
        return evidence
    
    def generate_from_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a draft from raw context (no strategy name required)."""
        strategies = context.get("strategies", [])
        
        if not strategies:
            return {
                "status": "no_strategies_found",
                "message": "No relevant strategies found in the provided context."
            }
        
        # Use the first strategy as basis
        strategy = strategies[0]
        
        return {
            "strategy_name": strategy.get("document", "Unknown Strategy"),
            "status": "draft",
            "evidence": strategy,
            "source": {
                "segment_id": strategy.get("segment_info", {}).get("segment_id", "unknown"),
                "video_id": strategy.get("segment_info", {}).get("video_id", "unknown")
            }
        }
