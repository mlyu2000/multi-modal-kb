#!/usr/bin/env python3
"""Platform-neutral bot specification generator."""

import os
from typing import Dict, Any, List, Optional

from ..rag.completeness_checker import CompletenessChecker


class BotSpecGenerator:
    """Generate platform-neutral bot specifications from strategies."""
    
    def __init__(self, completeness_checker: CompletenessChecker = None):
        self.completeness = completeness_checker or CompletenessChecker()
    
    def generate(self, strategy_name: str) -> Dict[str, Any]:
        """Generate a bot specification.
        
        Args:
            strategy_name: Name of the strategy
        
        Returns:
            Bot spec dictionary (or incomplete status)
        """
        # Check completeness
        completeness = self.completeness.check(strategy_name)
        
        if not completeness.get("is_complete", False):
            return {
                "status": "incomplete",
                "strategy": strategy_name,
                "missing_parameters": completeness.get("missing", []),
                "questions": completeness.get("questions", []),
                "note": "Bot spec cannot be generated until strategy is complete."
            }
        
        # Generate spec
        spec = {
            "bot_spec": {
                "name": self._normalize_name(strategy_name),
                "status": "complete",
                "description": f"Bot based on {strategy_name} strategy",
                "asset_class": completeness.get("asset_class", "unresolved"),
                "timeframe": completeness.get("timeframes", ["unresolved"])[0] if completeness.get("timeframes") else "unresolved"
            }
        }
        
        # Add indicators
        if completeness.get("indicators"):
            spec["bot_spec"]["indicators"] = self._format_indicators(completeness["indicators"])
        
        # Add rules
        if completeness.get("rules_found"):
            spec["bot_spec"]["rules"] = self._format_rules(completeness["rules_found"])
        
        # Add missing parameters section
        missing_params = self._identify_missing_params(completeness)
        if missing_params:
            spec["bot_spec"]["missing_parameters"] = missing_params
        
        return spec
    
    def _normalize_name(self, name: str) -> str:
        """Normalize a name for bot spec."""
        return name.lower().replace(" ", "_").replace("-", "_")
    
    def _format_indicators(self, indicators: List[str]) -> Dict[str, Any]:
        """Format indicators configuration."""
        formatted = {}
        for indicator in indicators:
            indicator_lower = indicator.lower()
            if "rsi" in indicator_lower:
                formatted["rsi"] = {
                    "period": 14,
                    "overbought": 70,
                    "oversold": 30
                }
            elif "ma" in indicator_lower or "moving average" in indicator_lower:
                formatted["moving_average"] = {
                    "type": "ema",
                    "period": 50
                }
            elif "macd" in indicator_lower:
                formatted["macd"] = {
                    "fast": 12,
                    "slow": 26,
                    "signal": 9
                }
            elif "bollinger" in indicator_lower:
                formatted["bollinger"] = {
                    "period": 20,
                    "std_dev": 2
                }
            else:
                formatted[indicator_lower] = {"parameters": "unspecified"}
        
        return formatted
    
    def _format_rules(self, rules_found: Dict[str, str]) -> List[Dict[str, Any]]:
        """Format rules configuration."""
        formatted = []
        for rule_name, rule_text in rules_found.items():
            rule_lower = rule_name.lower()
            
            # Determine rule type from name
            rule_type = "unknown"
            if "entry" in rule_lower:
                rule_type = "entry"
            elif "exit" in rule_lower:
                rule_type = "exit"
            elif "stop" in rule_lower:
                rule_type = "stop_loss"
            elif "profit" in rule_lower:
                rule_type = "take_profit"
            elif "invalid" in rule_lower:
                rule_type = "invalidation"
            elif "position" in rule_lower:
                rule_type = "position_sizing"
            
            formatted.append({
                "name": rule_name,
                "type": rule_type,
                "description": rule_text[:100] + "..." if len(rule_text) > 100 else rule_text,
                "machine_checkable": "condition" in rule_lower.lower()
            })
        
        return formatted
    
    def _identify_missing_params(self, completeness: Dict[str, Any]) -> List[str]:
        """Identify missing parameters from completeness report."""
        missing = completeness.get("missing", [])
        
        # Map missing rule types to specific parameters
        param_mapping = {
            "stop_loss_rule": ["stop_loss_method", "stop_loss_distance"],
            "take_profit_rule": ["take_profit_method", "take_profit_target"],
            "position_sizing_rule": ["position_size_method", "risk_percentage"],
            "entry_rule": ["entry_trigger", "entry_timing"],
            "exit_rule": ["exit_trigger", "exit_timing"]
        }
        
        result = []
        for m in missing:
            if m in param_mapping:
                result.extend(param_mapping[m])
        
        # Add general missing params
        result.extend([
            "exact_timeframe",
            "asset_class_to_trade",
            "capital_allocation",
            "max_drawdown_limit"
        ])
        
        return list(set(result))  # Remove duplicates
