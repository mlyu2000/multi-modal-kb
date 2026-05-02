#!/usr/bin/env python3
"""ChromaDB vector store for trading KB."""

import os
from typing import Optional, Dict, Any, List
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


class ChromaStore:
    """ChromaDB vector store for trading KB."""
    
    def __init__(self, persist_dir: str = None):
        if not CHROMADB_AVAILABLE:
            raise ImportError("chromadb is not installed. Install with: pip install chromadb")
        
        self.persist_dir = Path(persist_dir or os.getenv("CHROMA_PERSIST_DIR", "./db/chroma"))
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        
        # Initialize collections
        self.segments_collection = self.client.get_or_create_collection(
            name="segments",
            metadata={"hnsw:space": "cosine"}
        )
        
        self.concepts_collection = self.client.get_or_create_collection(
            name="concepts",
            metadata={"hnsw:space": "cosine"}
        )
        
        self.rules_collection = self.client.get_or_create_collection(
            name="rules",
            metadata={"hnsw:space": "cosine"}
        )
        
        self.strategies_collection = self.client.get_or_create_collection(
            name="strategies",
            metadata={"hnsw:space": "cosine"}
        )
        
        self.visual_examples_collection = self.client.get_or_create_collection(
            name="visual_examples",
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_segment(self, segment_id: str, text: str, metadata: Dict[str, Any]) -> str:
        """Add a segment to the vector store."""
        self.segments_collection.add(
            ids=[segment_id],
            documents=[text],
            metadatas=[metadata]
        )
        return segment_id
    
    def add_concept(self, concept_id: str, text: str, metadata: Dict[str, Any]) -> str:
        """Add a concept to the vector store."""
        self.concepts_collection.add(
            ids=[concept_id],
            documents=[text],
            metadatas=[metadata]
        )
        return concept_id
    
    def add_segment_with_embedding(self, segment_id: str, text: str, 
                                   embedding: List[float], metadata: Dict[str, Any]) -> str:
        """Add a segment with pre-computed embedding."""
        self.segments_collection.add(
            ids=[segment_id],
            documents=[text],
            embeddings=[embedding],
            metadatas=[metadata]
        )
        return segment_id
    
    def add_rule(self, rule_id: str, text: str, metadata: Dict[str, Any]) -> str:
        """Add a rule to the vector store."""
        self.rules_collection.add(
            ids=[rule_id],
            documents=[text],
            metadatas=[metadata]
        )
        return rule_id
    
    def add_strategy(self, strategy_id: str, text: str, metadata: Dict[str, Any]) -> str:
        """Add a strategy to the vector store."""
        self.strategies_collection.add(
            ids=[strategy_id],
            documents=[text],
            metadatas=[metadata]
        )
        return strategy_id
    
    def add_visual_example(self, example_id: str, text: str, metadata: Dict[str, Any]) -> str:
        """Add a visual example to the vector store."""
        self.visual_examples_collection.add(
            ids=[example_id],
            documents=[text],
            metadatas=[metadata]
        )
        return example_id
    
    def search_segments(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search segments by query."""
        results = self.segments_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return self._format_results(results)
    
    def search_concepts(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search concepts by query."""
        results = self.concepts_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return self._format_results(results)
    
    def search_rules(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search rules by query."""
        results = self.rules_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return self._format_results(results)
    
    def search_strategies(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant strategies."""
        results = self.strategies_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        formatted = []
        for i, doc in enumerate(results["documents"][0]):
            formatted.append({
                "id": results["ids"][0][i],
                "text": doc,
                "distance": results["distances"][0][i],
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {}
            })
        return formatted

    def _format_results(self, results) -> List[Dict[str, Any]]:
        """Format ChromaDB results."""
        formatted = []
        for i in range(len(results["ids"][0])):
            formatted.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results.get("distances") else None
            })
        return formatted
    
    def get_by_id(self, collection_name: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID."""
        collection = getattr(self, f"{collection_name}_collection", None)
        if not collection:
            return None
        results = collection.get(ids=[document_id])
        if results and results["ids"]:
            return {
                "id": results["ids"][0],
                "document": results["documents"][0],
                "metadata": results["metadatas"][0]
            }
        return None
    
    def get_collection(self, name: str):
        """Get a collection by name."""
        return getattr(self, f"{name}_collection", None)
    
    def delete(self, collection_name: str, document_id: str) -> bool:
        """Delete a document from collection."""
        collection = getattr(self, f"{collection_name}_collection", None)
        if collection:
            collection.delete(ids=[document_id])
            return True
        return False
