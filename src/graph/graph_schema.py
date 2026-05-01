#!/usr/bin/env python3
"""Graph schema definitions for Trading KB."""

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

# Rule types
SETUP = "setup"
ENTRY = "entry"
EXIT = "exit"
STOP_LOSS = "stop_loss"
TAKE_PROFIT = "take_profit"
CONFIRMATION = "confirmation"
INVALIDATION = "invalidation"
FILTER = "filter"
POSITION_SIZING = "position_sizing"
AVOIDANCE = "avoidance"

# Node property defaults
NODE_DEFAULTS = {
    "review_status": "unreviewed",
    "created_at": "timestamp"
}

# Relationship property defaults
RELATIONSHIP_DEFAULTS = {
    "confidence": 0.5,
    "evidence": "",
    "review_status": "unreviewed",
    "created_at": "timestamp"
}


def get_node_properties(label: str) -> dict:
    """Get default properties for a node type."""
    if label == RULE:
        return {
            "rule_type": None,
            "is_bot_ready": False,
            "confidence": 0.5
        }
    elif label == STRATEGY:
        return {
            "market_context": [],
            "assets": [],
            "timeframes": []
        }
    return NODE_DEFAULTS.copy()


def get_rule_types() -> list:
    """Get all valid rule types."""
    return [SETUP, ENTRY, EXIT, STOP_LOSS, TAKE_PROFIT, CONFIRMATION, 
            INVALIDATION, FILTER, POSITION_SIZING, AVOIDANCE]


def get_entity_types() -> list:
    """Get all valid entity types."""
    return [STRATEGY, CONCEPT, INDICATOR, RULE, CONDITION, 
            MARKET_CONTEXT, ASSET_CLASS, TIMEFRAME, PARAMETER, VISUAL_EXAMPLE]
