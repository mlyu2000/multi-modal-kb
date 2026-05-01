#!/usr/bin/env python3
"""GraphRAG Strategy Agent for Trading KB."""

import os
from typing import Dict, Any, List, Optional

from src.storage.neo4j_store import Neo4jStore
from src.storage.chroma_store import ChromaStore
from src.storage.sqlite_store import SQLiteStore
from src.rag.vector_retriever import VectorRetriever
from src.rag.graph_retriever import GraphRetriever
from src.rag.completeness_checker import CompletenessChecker


class GraphRAGAgent:
    """GraphRAG agent for trading strategy generation."""
    
    def __init__(self, neo4j_store: Neo4jStore = None, chroma_store: ChromaStore = None, 
                 sqlite_store: SQLiteStore = None):
        self.neo4j = neo4j_store or Neo4jStore()
        self.chroma = chroma_store or ChromaStore()
        self.sqlite = sqlite_store or SQLiteStore()
        
        self.vector_retriever = VectorRetriever(chroma_store=self.chroma, sqlite_store=self.sqlite)
        self.graph_retriever = GraphRetriever(neo4j_store=self.neo4j)
        self.completeness_checker = CompletenessChecker(neo4j_store=self.neo4j)
    
    def answer_query(self, query: str) -> Dict[str, Any]:
        """Answer a trading strategy query using GraphRAG.
        
        Args:
            query: User query about trading strategies
        
        Returns:
            Dictionary with strategy draft, completeness report, and bot spec if possible
        """
        # Step 1: Semantic retrieval
        context = self.vector_retriever.get_context_for_query(query, n_results=10)
        
        # Step 2: Graph traversal for relevant strategies
        strategies_found = self._find_relevant_strategies(query, context)
        
        if not strategies_found:
            return {
                "query": query,
                "status": "no_strategies_found",
                "message": "No relevant trading strategies found in the knowledge base."
            }
        
        # Step 3: Get strategy completeness
        strategy_summary = []
        for strategy in strategies_found:
            completeness = self.completeness_checker.check(strategy["name"])
            strategy_summary.append({
                "strategy": strategy["name"],
                "completeness": completeness
            })
        
        # Step 4: Generate strategy draft
        strategy_draft = self._generate_strategy_draft(strategies_found[0], context)
        
        # Step 5: Check completeness
        completeness_report = self.completeness_checker.check(strategies_found[0]["name"])
        
        # Step 6: Generate bot spec if complete
        bot_spec = None
        if completeness_report.get("is_complete", False):
            bot_spec = self._generate_bot_spec(strategies_found[0], completeness_report)
        
        return {
            "query": query,
            "strategies_found": strategies_found,
            "strategy_count": len(strategies_found),
            "strategy_draft": strategy_draft,
            "completeness_report": completeness_report,
            "bot_spec": bot_spec,
            "source_evidence": self._build_evidence(context)
        }
    
    def _find_relevant_strategies(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find relevant strategies using vector and graph search."""
        strategies = []
        
        # Get strategies from vector search
        strategy_results = context.get("strategies", [])
        for result in strategy_results:
            node_info = result.get("node_info", {})
            if node_info:
                strategies.append({
                    "name": node_info.get("name", result["id"]),
                    "description": node_info.get("description", ""),
                    "confidence": result.get("confidence", 0.5)
                })
        
        # Get strategies from graph search
        if not strategies and "segments" in context:
            # Extract strategy names from segment mentions
            for segment in context["segments"]:
                segment_info = segment.get("segment_info", {})
                if segment_info:
                    strategies.append({
                        "name": segment.get("document", "Unknown Strategy"),
                        "description": segment_info.get("summary", ""),
                        "confidence": 0.5
                    })
        
        return strategies
    
    def _generate_strategy_draft(self, strategy: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a strategy draft from retrieved context."""
        return {
            "strategy_name": strategy.get("name", "Unknown Strategy"),
            "status": "draft",
            "description": strategy.get("description", ""),
            "sources": self._build_evidence(context),
            "next_steps": [
                "Verify rule completeness",
                "Define exact parameters",
                "Backtest on historical data"
            ]
        }
    
    def _generate_bot_spec(self, strategy: Dict[str, Any], completeness: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a platform-neutral bot specification."""
        return {
            "bot_spec": {
                "name": self._normalize_name(strategy.get("name", "unknown")),
                "status": "complete",
                "description": strategy.get("description", ""),
                "rules": completeness.get("rules", []),
                "indicators": completeness.get("indicators", []),
                "timeframes": completeness.get("timeframes", []),
                "asset_class": completeness.get("asset_class", "unresolved")
            }
        }
    
    def _build_evidence(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build source evidence from context."""
        evidence = []
        
        # Add segment evidence
        for segment in context.get("segments", [])[:3]:
            evidence.append({
                "type": "segment",
                "content": segment.get("document", "")[:200] + "...",
                "video_id": segment.get("metadata", {}).get("video_id", "unknown"),
                "segment_id": segment.get("id", "unknown")
            })
        
        return evidence
    
    def _normalize_name(self, name: str) -> str:
        """Normalize a name for bot spec."""
        return name.lower().replace(" ", "_").replace("-", "_")
