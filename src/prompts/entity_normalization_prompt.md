You are normalizing trading entity names to their standard forms.

Task: Map raw entity names to their canonical/trading-standard forms.

Examples:
- "BOS" -> "Break of Structure"
- "S/R" -> "Support and Resistance"
- "RR" -> "Reward-to-Risk Ratio"
- "HNS" -> "Head and Shoulders"
- "hh" -> "Higher High"
- "ll" -> "Lower Low"
- "ema" -> "Exponential Moving Average"

Rules:
- Preserve distinct concepts that happen to have similar names
- Use widely-accepted trading terminology
- Return the canonical form as the primary name

Input:
Raw name: {raw_name}
Entity type: {entity_type}

Return:
{
    "raw_name": "{raw_name}",
    "canonical_name": "canonical_form"
}
