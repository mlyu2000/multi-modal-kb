"""ChromaDB vector store for multimodal trading video knowledge base."""

from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb


class ChromaVectorStore:
    """
    ChromaDB vector store with proper metadata schema.
    
    Stores multimodal segment embeddings with metadata for
    retrieval in the trading video knowledge base.
    """
    
    def __init__(self, persist_dir: str = "/home/ml/trading_kb/db/chroma"):
        """Initialize ChromaDB client."""
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = None
    
    def create_collection(self, name: str = "trading_kb", embedding_function = None):
        """
        Create or get a collection.
        
        Args:
            name: Collection name
            embedding_function: Optional embedding function for Chroma
        """
        self.collection = self.client.get_or_create_collection(
            name=name,
            embedding_function=embedding_function
        )
        return self.collection
    
    def add_segment(self, segment_id: str, document: str, 
                    metadata: Dict[str, Any], embedding: List[float]):
        """
        Add a single segment to the collection.
        
        Args:
            segment_id: Unique segment identifier
            document: The embedded text content
            metadata: Segment metadata (video_id, timestamps, tags, etc.)
            embedding: Pre-computed embedding vector
        """
        if self.collection is None:
            raise RuntimeError("Collection not initialized. Call create_collection() first.")
        
        self.collection.add(
            ids=[segment_id],
            documents=[document],
            embeddings=[embedding],
            metadatas=[metadata]
        )
    
    def add_batch(self, segments: List[Dict[str, Any]]):
        """
        Add multiple segments at once.
        
        Args:
            segments: List of dicts with segment_id, document, metadata, embedding
        """
        if self.collection is None:
            raise RuntimeError("Collection not initialized.")
        
        ids = [s["id"] for s in segments]
        documents = [s["document"] for s in segments]
        embeddings = [s["embedding"] for s in segments]
        metadatas = [s["metadata"] for s in segments]
        
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
    
    def query(self, query_embedding: List[float], n_results: int = 5, 
              where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Query the collection for similar segments.
        
        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            Results dict with documents, distances, and metadata
        """
        if self.collection is None:
            raise RuntimeError("Collection not initialized.")
        
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
    
    def get_segment(self, segment_id: str) -> Optional[Dict[str, Any]]:
        """Get a single segment by ID."""
        if self.collection is None:
            return None
        
        result = self.collection.get(ids=[segment_id])
        if result and result["ids"]:
            return {
                "id": result["ids"][0],
                "document": result["documents"][0],
                "metadata": result["metadatas"][0]
            }
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        if self.collection is None:
            return {"error": "Collection not initialized"}
        
        count = self.collection.count()
        return {
            "collection_name": self.collection.name,
            "segment_count": count
        }


# Pre-built metadata schema
SEGMENT_METADATA_SCHEMA = {
    "video_id": str,           # Video identifier
    "video_title": str,        # Full video title
    "chapter": str,           # Chapter/section title
    "start_sec": int,          # Start time in seconds
    "end_sec": int,           # End time in seconds
    "transcript": str,         # Transcript text
    "ocr_text": str,          # OCR from frames
    "visual_type": str,       # Type: slide, code, demo, speaker, diagram
    "concepts": str,          # Comma-separated concepts
    "tags": str,              # Comma-separated tags
    "has_ocr": bool,          # Whether OCR was extracted
    "summary": str            # Multimodal summary text
}

if __name__ == "__main__":
    # Test ChromaDB store
    print("=== Testing ChromaDB Vector Store ===")
    
    store = ChromaVectorStore()
    store.create_collection("test_trading")
    
    print(f"Collection: {store.collection.name}")
    print(f"Stats: {store.get_stats()}")
    
    # Add a test segment
    test_metadata = {
        "video_id": "test001",
        "chapter": "Introduction",
        "start_sec": 0,
        "end_sec": 60,
        "visual_type": "slide",
        "tags": "intro,overview"
    }
    
    print(f"\nSchema: {SEGMENT_METADATA_SCHEMA}")
    print("✓ ChromaDB store ready!")
