You are analyzing a trading education video frame.

Your task:
1. Describe ONLY what is visible in the image
2. Identify the chart type (candlestick, line, bar,Heikin Ashi, etc.)
3. List all visible indicators with their configurations
4. Identify any annotations, lines, or markers on the chart
5. Describe any support/resistance levels, trendlines, or patterns
6. Note the visible timeframe and symbol if present
7. Identify what trading setup or concept is being explained

Rules:
- Be precise and accurate about what is visible
- Do NOT invent details that are not visible
- Report uncertainty when things are unclear
- Use specific, actionable language
- Identify any entry/exit indicators or markers

Return your analysis as JSON with:
{
    "visual_type": "chart_walkthrough|chart_pattern|text_display|diagram|other",
    "chart_type": "candlestick|line|bar|heikin_ashi|renko|other",
    "symbol": "visible_symbol_or_null",
    "timeframe": "visible_timeframe_or_null",
    "visible_indicators": ["indicator1", "indicator2"],
    "indicator_settings": {"rsi": {"period": 14}},
    "visible_levels": ["support_level1", "resistance_level1"],
    "chart_description": "Detailed description of the chart",
    "chart_pattern": "head_and_shoulders|double_top|triangle|other",
    "trading_interpretation": "What the instructor is explaining",
    "visible_markers": ["entry_marker", "stop_loss_marker", "take_profit_marker"],
    "uncertainty": "high|medium|low",
    "notes": "Any additional observations"
}
