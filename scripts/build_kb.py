#!/usr/bin/env python3
"""Build knowledge graph from ingested videos."""

import sys
import os
import argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from storage.sqlite_store import SQLiteStore
from storage.file_store import FileStore
from storage.chroma_store import ChromaStore
from storage.neo4j_store import Neo4jStore
from storage.file_store import FileStore
from extraction.knowledge_extractor import KnowledgeExtractor
from graph.graph_loader import GraphLoader


def main():
    parser = argparse.ArgumentParser(description="Build knowledge graph from ingested videos")
    parser.add_argument("--video-id", "-v", help="Video ID to build (all if not specified)")
    parser.add_argument("--segment-limit", "-l", type=int, default=5, help="Max segments to process per video")
    
    args = parser.parse_args()
    
    print("Building Trading KB knowledge graph...")
    print("-" * 40)
    
    # Initialize stores
    sqlite = SQLiteStore()
    files = FileStore()
    chroma = ChromaStore()
    
    neo4j = None
    try:
        neo4j = Neo4jStore()
        
        # Get video IDs
        if args.video_id:
            video_ids = [args.video_id]
        else:
            video_ids = files.list_videos()
        
        if not video_ids:
            print("No videos found. Run ingest_video.py first.")
            return 1
        
        print(f"Processing {len(video_ids)} video(s)...")
        
        for video_id in video_ids:
            print(f"
--- Processing {video_id} ---")
            
            # Load segments
            segments = files.load_segments(video_id)
            if not segments:
                print(f"  No segments found for {video_id}")
                continue
            
            print(f"  Loaded {len(segments)} segments")
            
            # Extract knowledge
            extractor = KnowledgeExtractor(sqlite_store=sqlite, file_store=files)
            all_knowledge = []
            
            for segment in segments[:args.segment_limit]:
                knowledge = extractor.extract_knowledge(segment, video_id)
                if knowledge and "error" not in knowledge:
                    all_knowledge.append(knowledge)
            
            print(f"  Extracted knowledge from {len(all_knowledge)} segments")
            
            # Load into Neo4j
            graph_loader = GraphLoader(neo4j_store=neo4j)
            graph_loader.load_video(video_id, segments)
            print(f"  ✓ Loaded video to Neo4j")
            
            for knowledge in all_knowledge:
                graph_loader.load_knowledge(video_id, knowledge)
            print(f"  ✓ Loaded knowledge to Neo4j")
            
            # Load into ChromaDB
            for segment in segments:
                chroma.add_segment(
                    segment_id=segment["segment_id"],
                    text=segment.get("transcript", ""),
                    metadata={
                        "video_id": video_id,
                        "start_time": segment.get("start_time", 0),
                        "end_time": segment.get("end_time", 0)
                    }
                )
            print(f"  ✓ ChromaDB vectors created")
            
            print(f"  ✓ {video_id} complete")
        
        print("
" + "-" * 40)
        print("KB build complete!")
        print(f"
Total videos processed: {len(video_ids)}")
        print("
Next: Query the graph with query_agent.py")
        
        return 0
        
    finally:
        sqlite.close()
        neo4j.close()


if __name__ == "__main__":
    sys.exit(main())
