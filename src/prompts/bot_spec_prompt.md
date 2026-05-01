You are generating a platform-neutral bot specification from a strategy.

Task: Convert a trading strategy into a platform-neutral bot specification.

Input:
- Strategy draft with all required components
- Any missing parameters that need to be specified

Rules:
1. Structure the spec as a YAML configuration
2. Mark unresolved parameters explicitly
3. Do NOT generate executable code
4. Keep it abstract enough to work across multiple platforms

Output format:
```yaml
bot_spec:
  name: "strategy_name_normalized"
  status: "complete"  # or "draft"
  description: "brief description"
  
  asset_class: "unresolved"  # or resolved: "forex|crypto|stocks|commodities"
  timeframe: "unresolved"    # or resolved: "1m|5m|15m|1h|4h|1d"
  
  indicators:
    rsi:
      period: 14
      overbought: 70
      oversold: 30
    moving_average:
      type: "ema"
      period: 50
  
  setup:
    conditions:
      - id: "price_lower_low"
        description: "Price makes a lower low"
        machine_checkable: true
      - id: "rsi_higher_low"
        description: "RSI makes a higher low"
        machine_checkable: true
  
  confirmation:
    conditions:
      - id: "break_above_swing_high"
        description: "Price breaks above recent swing high"
        machine_checkable: true
  
  entry:
    action: "open_long"
    trigger: "confirmation_close"
    conditions: []
  
  stop_loss:
    type: "below_recent_swing_low"
    distance: "unresolved"  # or number
  
  take_profit:
    type: "previous_resistance_or_configurable_rr"
    value: "unresolved"
  
  filters:
    avoid:
      - "strong_downtrend_without_confirmation"
      - "low_volume_conditions"
  
  risk_management:
    position_sizing: "unresolved"
    max_risk_per_trade: "unresolved"
  
  missing_parameters:
    - "exact_timeframe"
    - "reward_to_risk_ratio"
    - "position_size_method"
```
