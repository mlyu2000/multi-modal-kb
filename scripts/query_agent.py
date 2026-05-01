#!/usr/bin/env python3
"""Query the GraphRAG agent."""

import sys
import os
import argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from rag.graphrag_agent import GraphRAGAgent


def main():
    parser = argparse.ArgumentParser(description="Query the Trading KB GraphRAG agent")
    parser.add_argument("--query", "-q", required=True, help="Your query")
    parser.add_argument("--format", "-f", choices=["text", "json"], default="text", help="Output format")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print(f"Query: {args.query}")
    print("=" * 60)
    
    agent = GraphRAGAgent()
    result = agent.answer_query(args.query)
    
    if args.format == "json":
        import json
        print(json.dumps(result, indent=2))
    else:
        print_status(result)
    
    return 0


def print_status(result: dict):
    """Print query results in readable format."""
    print(f"
Status: {result.get('status', 'unknown')}")
    print(f"Strategies found: {result.get('strategy_count', 0)}")
    
    # Strategy draft
    draft = result.get('strategy_draft', {})
    if draft:
        print(f"
--- Strategy Draft ---")
        print(f"Name: {draft.get('strategy_name', 'Unknown')}")
        print(f"Status: {draft.get('status', 'draft')}")
        if draft.get('sources'):
            print(f"
Sources:")
            for src in draft['sources'][:3]:
                print(f"  - {src.get('segment_id', 'unknown')}")
    
    # Completeness
    completeness = result.get('completeness_report', {})
    if completeness:
        print(f"
--- Completeness Report ---")
        print(f"Is complete: {completeness.get('is_complete', False)}")
        if completeness.get('missing'):
            print(f"Missing: {', '.join(completeness.get('missing', []))}")
        if completeness.get('questions'):
            print(f"
Questions to resolve:")
            for q in completeness.get('questions', [])[:3]:
                print(f"  - {q}")
    
    # Bot spec
    bot_spec = result.get('bot_spec')
    if bot_spec:
        print(f"
--- Bot Specification ---")
        print(f"Status: {bot_spec.get('status', 'draft')}")
        print(f"Name: {bot_spec.get('name', 'Unknown')}")
        if bot_spec.get('rules'):
            print(f"Rules found: {len(bot_spec['rules'])}")


if __name__ == "__main__":
    sys.exit(main())
