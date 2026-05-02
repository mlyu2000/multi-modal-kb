#!/usr/bin/env python3
"""Vector retrieval module using ChromaDB."""

import os
from typing import Dict, Any, List, Optional

from src.storage.chroma_store import ChromaStore
from src.storage.sqlite_store import SQLiteStore


class VectorRetriever:
    """Retrieve relevant knowledge using vector search."""
    
    def __init__(self, chroma_store: ChromaStore = None, sqlite_store: SQLiteStore = None):
        self.chroma = chroma_store or ChromaStore()
        self.sqlite = sqlite_store or SQLiteStore()
    
    def search_segments(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant segments.
        
        Args:
            query: Search query
            n_results: Number of results to return
        
        Returns:
            List of matching segments with metadata
        """
        results = self.chroma.search_segments(query, n_results)
        
        # Enrich with SQLite data
        enriched = []
        for result in results:
            segment_id = result["id"]
            segment = self.sqlite.get_segment(segment_id)
            if segment:
                enriched.append({
                    **result,
                    "segment_info": segment
                })
            else:
                enriched.append(result)
        
        return enriched
    
    def search_rules(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant rules.
        
        Args:
            query: Search query
            n_results: Number of results to return
        
        Returns:
            List of matching rules with metadata
        """
        results = self.chroma.search_rules(query, n_results)
        
        # Enrich with SQLite data
        enriched = []
        for result in results:
            entity = self.sqlite.get_entity(result["id"])
            if entity:
                enriched.append({
                    **result,
                    "entity_info": entity
                })
            else:
                enriched.append(result)
        
        return enriched
    
    def search_concepts(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant concepts.
        
        Args:
            query: Search query
            n_results: Number of results to return
        
        Returns:
            List of matching concepts with metadata
        """
        results = self.chroma.search_concepts(query, n_results)
        
        enriched = []
        for result in results:
            entity = self.sqlite.get_entity(result["id"])
            if entity:
                enriched.append({
                    **result,
                    "entity_info": entity
                })
            else:
                enriched.append(result)
        
        return enriched
    
    def search_strategies(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant strategies.
        
        Args:
            query: Search query
            n_results: Number of results to return
        
        Returns:
            List of matching strategies with metadata
        """
        results = self.chroma.search_strategies(query, n_results)
        
        enriched = []
        for result in results:
            # For strategies, try to get the node from Neo4j
            try:
                from src.storage.neo4j_store import Neo4jStore
                neo4j = Neo4jStore()
                node = neo4j.get_node("Strategy", result["id"])
                if node:
                    enriched.append({
                        **result,
                        "node_info": node
                    })
                else:
                    enriched.append(result)
            except:
                enriched.append(result)
        
        return enriched
    
    def rerank_results(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rerank search results based on query relevance.
        
        Args:
            query: Original query
            results: Search results to rerank
        
        Returns:
            Reranked results
        """
        # Simple reranking: sort by distance (lower = more relevant)
        return sorted(results, key=lambda x: x.get("distance", 1.0))
    
    def get_context_for_query(self, query: str, n_results: int = 10) -> Dict[str, Any]:
        """Get comprehensive context for a query.
        
        Args:
            query: Search query
            n_results: Number of each type to retrieve
        
        Returns:
            Dictionary with segments, rules, concepts, and strategies
        """
        return {
            "segments": self.search_segments(query, n_results),
            "rules": self.search_rules(query, n_results),
            "concepts": self.search_concepts(query, n_results),
            "strategies": self.search_strategies(query, n_results)
        }

    def get_categories(self) -> List[str]:
        """Get all available categories from ChromaDB collections."""
        categories = set()
        for collection in self.chroma_store.client.list_collections():
            md = collection.metadata or {}
            if md.get("category"):
                categories.add(md["category"])
        return sorted(list(categories))

    def get_schools(self) -> List[str]:
        """Get all available schools of thought from ChromaDB collections."""
        schools = set()
        for collection in self.chroma_store.client.list_collections():
            # Get metadata from first document in collection
            try:
                docs = collection.peek(limit=1)
                if docs and docs.get("metadatas"):
                    for md in docs["metadatas"]:
                        if md.get("school"):
                            schools.add(md["school"])
            except:
                pass
        return sorted(list(schools))
