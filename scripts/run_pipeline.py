#!/usr/bin/env python3
"""Run complete Trading KB pipeline: ingestion -> build -> optional query."""

import sys
import os
import argparse
from pathlib import Path

# Insert src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.logging import get_logger, log_info, log_warning, log_error
from ingestion.ingest_video import ingest_video
from scripts.build_kb import main as build_kb_main
from rag.vector_retriever import VectorRetriever


def run_pipeline(video_id: str = None, video_url: str = None, 
                 category: str = "general", school: str = "default",
                 run_build: bool = True, run_query: str = None):
    """
    Run the complete Trading KB pipeline.
    
    Args:
        video_id: Optional existing video ID to use
        video_url: Optional video URL to download and process
        run_build: Whether to run knowledge graph building
        run_query: Optional query to run after pipeline completes
    """
    logger = get_logger()
    
    print("\n" + "="*60)
    print("TRADING KB PIPELINE")
    print("="*60)
    
    try:
        # Step 1: Ingest video (or use existing)
        if video_url:
            log_info(f"Downloading video from: {video_url}")
            # Extract video ID from URL
            video_id = video_url.split("/")[-2] if "/" in video_url else "video"
        elif video_id:
            log_info(f"Using existing video: {video_id}")
        else:
            log_warning("No video specified. Skipping ingestion step.")
            return 0
        
        log_info(f"Step 1: Ingesting video ({video_id})...")
        result = ingest_video(video_url or "", video_id=video_id, 
                            category=category, school_of_thought=school)
        
        if not result:
            log_error("Video ingestion failed")
            return 1
        
        log_info(f"✓ Ingestion complete: {len(result)} segments extracted")
        
        # Step 2: Build knowledge graph (optional)
        if run_build:
            log_info("\nStep 2: Building knowledge graph...")
            
            # Re-run build_kb with the video
            build_args = type("Args", (), {"video_id": video_id, "segment_limit": 5})()
            
            try:
                build_kb_main_wrapper(build_args)
                log_info("✓ Knowledge graph build complete")
            except Exception as e:
                log_error(f"Build failed: {e}")
                return 1
        
        # Step 3: Optional query
        if run_query:
            log_info(f"\nStep 3: Running query: "{run_query}"")
            
            try:
                retriever = VectorRetriever()
                results = retriever.search_segments(run_query, n_results=5)
                
                log_info(f"Found {len(results)} relevant segments:")
                for i, result in enumerate(results, 1):
                    print(f"  {i}. {result.get('text', '')[:100]}...")
                
                log_info("✓ Query complete")
            except Exception as e:
                log_error(f"Query failed: {e}")
                return 1
        
        print("\n" + "="*60)
        print("PIPELINE COMPLETE")
        print("="*60 + "\n")
        
        return 0
        
    except Exception as e:
        log_error(f"Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def build_kb_main_wrapper(args):
    """Wrapper to call build_kb.main() with args object."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    
    # Inline copy of build_kb main logic
    from storage.sqlite_store import SQLiteStore
    from storage.file_store import FileStore
    from extraction.knowledge_extractor import KnowledgeExtractor
    from graph.graph_loader import GraphLoader
    
    sqlite = SQLiteStore()
    files = FileStore()
    
    if args.video_id:
        video_ids = [args.video_id]
    else:
        video_ids = files.list_videos()
    
    if not video_ids:
        print("No videos found. Run ingest_video.py first.")
        return 1
    
    for video_id in video_ids:
        segments = files.load_segments(video_id)
        if not segments:
            continue
        
        extractor = KnowledgeExtractor()
        
        for segment in segments[:args.segment_limit]:
            extractor.extract_knowledge(segment, video_id)
        
        graph_loader = GraphLoader()
        graph_loader.load_video(video_id, segments)


def main():
    parser = argparse.ArgumentParser(description="Run Trading KB pipeline")
    parser.add_argument("--video-id", "-v", help="Video ID to process")
    parser.add_argument("--video-url", "-u", help="Video URL to download")
    parser.add_argument("--category", "-c", default="general", help="Video category")
    parser.add_argument("--school", "-s", default="default", help="School of thought")
    parser.add_argument("--skip-build", action="store_true", help="Skip knowledge graph build")
    parser.add_argument("--query", "-q", help="Run query after pipeline")
    parser.add_argument("--verbose", "-V", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    return run_pipeline(
        video_id=args.video_id,
        video_url=args.video_url,
        category=args.category,
        school=args.school,
        run_build=not args.skip_build,
        run_query=args.query
    )


if __name__ == "__main__":
    sys.exit(main())
