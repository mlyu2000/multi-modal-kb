#!/usr/bin/env python3
"""Initialize databases for Trading KB."""

import sys
import os

# Add src directory to path correctly
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
src_dir = os.path.join(project_root, 'src')

if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from storage.sqlite_store import SQLiteStore
from storage.chroma_store import ChromaStore
from storage.neo4j_store import Neo4jStore


def main():
    print("Initializing Trading KB database...")
    print("-" * 40)
    
    # Initialize SQLite
    print("1. Initializing SQLite metadata store...")
    try:
        sqlite = SQLiteStore()
        print("   SQLite database created")
        sqlite.close()
    except Exception as e:
        print(f"   SQLite failed: {e}")
        return 1
    
    # Initialize ChromaDB
    print("2. Initializing ChromaDB vector store...")
    try:
        chroma = ChromaStore()
        print("   ChromaDB collections created")
        print("   Collections: segments, concepts, rules, strategies, visual_examples")
    except Exception as e:
        print(f"   ChromaDB failed: {e}")
        print("   Install: pip install chromadb")
        return 1
    
    # Initialize Neo4j
    print("3. Initializing Neo4j graph store...")
    try:
        neo4j = Neo4jStore()
        print("   Neo4j connection established")
        print("   Node types: Video, Segment, Frame, Strategy, Concept, etc.")
        print("   Relationship types: HAS_RULE, USES, SUPPORTS, etc.")
        neo4j.close()
    except Exception as e:
        print(f"   Neo4j failed: {e}")
        print("   Make sure Neo4j is running and configure .env")
    
    print("-" * 40)
    print("Initialization complete!")
    print("")
    print("Next steps:")
    print("  1. Add video files to data/videos/")
    print("  2. Run: python scripts/ingest_video.py --file <video_path>")
    print("  3. Run: python scripts/build_kb.py --video-id <video_id>")


if __name__ == "__main__":
    main()
