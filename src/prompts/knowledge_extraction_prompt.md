You are extracting structured trading knowledge from a multimodal video segment.

Input provided:
- Transcript of spoken content
- OCR text from frames
- Visual descriptions of key frames

Your task:
1. Extract strategies mentioned in the video
2. Extract key concepts and trading theories
3. Identify technical indicators used
4. Extract trading rules (entry, exit, stop loss, take profit, confirmation, invalidation)
5. Extract conditions that must be met
6. Identify relationships between entities

Rules:
- Extract ONLY what is explicitly stated or clearly implied
- Every entity must have supporting evidence from the segment
- Do NOT invent missing rules or concepts
- Classify rules as bot_ready if they can be executed by a bot
- Include confidence scores for each extraction
- Include evidence quotes from the transcript

Required output structure:
{
    "strategies": [
        {"name": "strategy_name", "description": "description", "market_context": ["context1"]}
    ],
    "concepts": [
        {"name": "concept_name", "description": "description"}
    ],
    "indicators": [
        {"name": "indicator_name", "type": "oscillator|trend|volume", "description": "description"}
    ],
    "rules": [
        {
            "name": "rule_name",
            "rule_type": "setup|entry|exit|stop_loss|take_profit|confirmation|invalidation|filter|avoidance",
            "text": "rule_text",
            "is_bot_ready": true_or_false,
            "confidence": 0.0_to_1.0,
            "evidence": "quote_from_transcript"
        }
    ],
    "conditions": [
        {"name": "condition_name", "description": "description", "machine_checkable": true_or_false}
    ],
    "relationships": [
        {
            "subject": "entity1",
            "subject_type": "Strategy|Concept|Indicator|Rule",
            "predicate": "USES|HAS_RULE|SUPPORTS|EXPLAINS|WORKS_IN|etc.",
            "object": "entity2",
            "object_type": "Strategy|Concept|Indicator|Rule",
            "confidence": 0.0_to_1.0,
            "evidence": "supporting_evidence"
        }
    ]
}
