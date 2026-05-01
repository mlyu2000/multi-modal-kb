#!/usr/bin/env python3
"""Main entry point for Trading KB."""

import os
import sys
import argparse

from src.config.settings import settings
from src.storage.sqlite_store import SQLiteStore
from src.storage.chroma_store import ChromaStore
from src.storage.neo4j_store import Neo4jStore
from src.storage.file_store import FileStore


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Trading KB - Graph-first multimodal knowledge base")
    parser.add_argument("command", nargs="?", default="help",
                       help="Command to run (init, ingest, build, query)")
    parser.add_argument("--file", "-f", help="Path to video file for ingestion")
    parser.add_argument("--title", "-t", help="Title for the video")
    parser.add_argument("--video-id", "-v", help="Video ID to process")
    parser.add_argument("--query", "-q", help="Query for the agent")
    
    args = parser.parse_args()
    
    if args.command == "help" or args.command not in ["init", "ingest", "build", "query"]:
        print_help()
        return 0
    
    if args.command == "init":
        return cmd_init()
    elif args.command == "ingest":
        return cmd_ingest(args.file, args.title)
    elif args.command == "build":
        return cmd_build(args.video_id)
    elif args.command == "query":
        return cmd_query(args.query)
    
    return 0


def print_help():
    """Print help message."""
    print("""Trading KB - Graph-first multimodal trading video knowledge base

Usage:
    python src/main.py <command> [options]

Commands:
    init              Initialize databases (SQLite, Neo4j, Chroma)
    ingest            Ingest a video into the knowledge base
    build             Build knowledge graph from ingested video
    query             Query the GraphRAG agent

Options:
    -f, --file        Path to video file (for ingest)
    -t, --title       Title for the video (for ingest)
    -v, --video-id    Video ID to process (for build/query)
    -q, --query       Query for the agent (for query)

Examples:
    python src/main.py init
    python src/main.py ingest -f data/videos/rsi_strategy.mp4 -t "RSI Strategy Video"
    python src/main.py build -v rsi_strategy
    python src/main.py query -q "Create a bot using RSI divergence"
""")


def cmd_init():
    """Initialize databases."""
    print("Initializing databases...")
    
    # Check Neo4j connection
    try:
        neo4j = Neo4jStore()
        print("✓ Neo4j connection established")
        neo4j.close()
    except Exception as e:
        print(f"✗ Neo4j connection failed: {e}")
        print("  Make sure Neo4j is running and configured correctly in .env")
    
    # Initialize SQLite
    try:
        sqlite = SQLiteStore()
        print("✓ SQLite database created/updated")
        sqlite.close()
    except Exception as e:
        print(f"✗ SQLite initialization failed: {e}")
    
    # Initialize ChromaDB
    try:
        chroma = ChromaStore()
        print("✓ ChromaDB collections created")
    except Exception as e:
        print(f"✗ ChromaDB initialization failed: {e}")
        print("  Install chromadb: pip install chromadb")
    
    print("
Initialization complete!")
    return 0


def cmd_ingest(video_path: str, title: str = None):
    """Ingest a video."""
    if not video_path:
        print("Error: --file is required for ingest command")
        return 1
    
    from src.ingestion.register_video import VideoRegistrar
    from src.ingestion.extract_audio import AudioExtractor
    from src.ingestion.transcribe_audio import AudioTranscriber
    from src.ingestion.extract_frames import FrameExtractor
    from src.ingestion.run_ocr import FrameOCR
    from src.ingestion.describe_frames import FrameDescriber
    from src.ingestion.build_segments import SegmentBuilder
    
    print(f"Ingesting video: {video_path}")
    
    # Register video
    registrar = VideoRegistrar()
    video_id = registrar.register_video(video_path, title)
    print(f"✓ Registered video ID: {video_id}")
    
    # Extract audio
    extractor = AudioExtractor()
    audio_path = extractor.extract_audio(video_id)
    if audio_path:
        print(f"✓ Audio extracted to: {audio_path}")
    else:
        print("✗ Audio extraction failed")
        return 1
    
    # Transcribe
    transcriber = AudioTranscriber()
    transcript = transcriber.transcribe(video_id)
    if transcript:
        print(f"✓ Transcription complete ({len(transcript.get('segments', []))} segments)")
    else:
        print("✗ Transcription failed")
        return 1
    
    # Extract frames
    frame_extractor = FrameExtractor()
    frames = frame_extractor.extract_frames(video_id)
    if frames:
        print(f"✓ Extracted {len(frames)} frames")
    else:
        print("✗ Frame extraction failed")
        return 1
    
    # Run OCR
    ocr = FrameOCR()
    ocr_results = ocr.run_ocr(video_id)
    if ocr_results:
        print(f"✓ OCR complete ({len(ocr_results.get('frames', []))} frames processed)")
    else:
        print("✗ OCR failed")
    
    # Describe frames
    describer = FrameDescriber()
    descriptions = describer.describe_frames(video_id)
    if descriptions:
        print(f"✓ Frame descriptions complete ({len(descriptions)} frames)")
    else:
        print("✗ Frame description failed")
    
    # Build segments
    builder = SegmentBuilder()
    segments = builder.build_segments(video_id)
    if segments:
        print(f"✓ Built {len(segments)} multimodal segments")
    else:
        print("✗ Segment building failed")
    
    print(f"
Ingestion complete! Video ID: {video_id}")
    return 0


def cmd_build(video_id: str):
    """Build knowledge graph from video."""
    if not video_id:
        print("Error: --video-id is required for build command")
        return 1
    
    from src.ingestion.file_store import FileStore
    from src.extraction.knowledge_extractor import KnowledgeExtractor
    from src.extraction.entity_normalizer import EntityNormalizer
    from src.graph.graph_loader import GraphLoader
    from src.storage.chroma_store import ChromaStore
    
    print(f"Building knowledge graph for video: {video_id}")
    
    # Load extracted data
    files = FileStore()
    segments = files.load_segments(video_id)
    
    if not segments:
        print(f"Error: No segments found for {video_id}")
        print("Run ingestion first: python src/main.py ingest -f <video_path>")
        return 1
    
    print(f"✓ Loaded {len(segments)} segments")
    
    # Extract knowledge
    extractor = KnowledgeExtractor()
    all_knowledge = []
    
    for segment in segments[:5]:  # Process first 5 segments as sample
        knowledge = extractor.extract_knowledge(segment, video_id)
        if knowledge and "error" not in knowledge:
            all_knowledge.append(knowledge)
    
    print(f"✓ Extracted knowledge from {len(all_knowledge)} segments")
    
    # Load into Neo4j
    try:
        graph_loader = GraphLoader()
        graph_loader.load_video(video_id, segments)
        print("✓ Video loaded to Neo4j")
        
        for knowledge in all_knowledge:
            graph_loader.load_knowledge(video_id, knowledge)
        print("✓ Knowledge graph loaded to Neo4j")
    except Exception as e:
        print(f"✗ Neo4j loading failed: {e}")
    
    # Load into ChromaDB
    try:
        chroma = ChromaStore()
        
        # Add segments
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
        
        print("✓ ChromaDB vectors created")
    except Exception as e:
        print(f"✗ ChromaDB loading failed: {e}")
    
    print(f"
Knowledge graph build complete for {video_id}")
    return 0


def cmd_query(query: str):
    """Query the GraphRAG agent."""
    if not query:
        print("Error: --query is required for query command")
        return 1
    
    from src.rag.graphrag_agent import GraphRAGAgent
    
    print(f"Query: {query}")
    print("=" * 60)
    
    agent = GraphRAGAgent()
    result = agent.answer_query(query)
    
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
    
    # Completeness
    completeness = result.get('completeness_report', {})
    if completeness:
        print(f"
--- Completeness Report ---")
        print(f"Is complete: {completeness.get('is_complete', False)}")
        if completeness.get('missing'):
            print(f"Missing: {completeness.get('missing', [])}")
    
    # Bot spec
    bot_spec = result.get('bot_spec')
    if bot_spec:
        print(f"
--- Bot Specification ---")
        print(f"Status: {bot_spec.get('status', 'draft')}")
        print(f"Name: {bot_spec.get('name', 'Unknown')}")


if __name__ == "__main__":
    sys.exit(main())
