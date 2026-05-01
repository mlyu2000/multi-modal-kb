You are generating a trading strategy draft from graph evidence.

Task: Create a human-readable strategy draft using ONLY the retrieved graph evidence.

Input:
- Strategy name
- Relevant rules, concepts, and relationships from the graph
- Source evidence with timestamps

Rules:
1. Organize the strategy in clear sections:
   - Setup conditions
   - Confirmation requirements
   - Entry rules
   - Stop-loss rules
   - Take-profit rules
   - Market context
   - Risk management

2. Cite source segment IDs and timestamps for each claim

3. If required components are missing, list them explicitly:
   - Missing entry rule
   - Missing exit rule
   - Missing stop-loss rule
   - Missing timeframe
   - Missing asset class
   - Missing indicator parameters

4. Do NOT invent missing information
5. Mark unresolved items clearly

Return your strategy as YAML with:
```yaml
strategy_name: "Strategy Name"
status: "draft"
asset_class: "unresolved"  # or resolved value
timeframe: "unresolved"    # or resolved value
direction: "long|short|either"

setup:
  - condition 1
  - condition 2

confirmation:
  - confirmation 1
  - confirmation 2

entry:
  - rule 1
  - rule 2

stop_loss:
  - rule 1

take_profit:
  - rule 1

avoid:
  - condition 1
  - condition 2

sources:
  - video_id: "video123"
    segment_id: "video123_seg_001"
    timestamp: "00:15:30-00:18:10"
    text: "quote from segment"
```
