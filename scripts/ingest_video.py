#!/usr/bin/env python3

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

"""Ingest a video into the Trading KB."""

import sys
import os
import argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from storage.sqlite_store import SQLiteStore
from storage.file_store import FileStore
from ingestion.register_video import VideoRegistrar
from ingestion.extract_audio import AudioExtractor
from ingestion.transcribe_audio import AudioTranscriber
from ingestion.extract_frames import FrameExtractor
from ingestion.run_ocr import FrameOCR
from ingestion.describe_frames import FrameDescriber
from ingestion.build_segments import SegmentBuilder


def main():
    parser = argparse.ArgumentParser(description="Ingest a video into Trading KB")
    parser.add_argument("--file", "-f", required=True, help="Path to video file")
    parser.add_argument("--title", "-t", help="Title for the video (defaults to filename)")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug output")
    
    args = parser.parse_args()
    
    print(f"Ingesting video: {args.file}")
    
    # Initialize stores
    sqlite = SQLiteStore()
    files = FileStore()
    
    try:
        # Register video
        registrar = VideoRegistrar(sqlite_store=sqlite, file_store=files)
        video_id = registrar.register_video(args.file, args.title)
        print(f"✓ Registered video ID: {video_id}")
        
        # Extract audio
        audio_extractor = AudioExtractor(file_store=files, sqlite_store=sqlite)
        audio_path = audio_extractor.extract_audio(video_id)
        if audio_path:
            print(f"✓ Audio extracted to: {audio_path}")
        else:
            print("✗ Audio extraction failed")
            return 1
        
        # Transcribe
        transcriber = AudioTranscriber(sqlite_store=sqlite, file_store=files)
        transcript = transcriber.transcribe(video_id)
        if transcript:
            print(f"✓ Transcription complete ({len(transcript.get('segments', []))} segments)")
        else:
            print("✗ Transcription failed")
            return 1
        
        # Extract frames
        frame_extractor = FrameExtractor(sqlite_store=sqlite, file_store=files)
        frames = frame_extractor.extract_frames(video_id)
        if frames:
            print(f"✓ Extracted {len(frames)} frames")
        else:
            print("✗ Frame extraction failed")
            return 1
        
        # Run OCR
        ocr = FrameOCR(sqlite_store=sqlite, file_store=files)
        ocr_results = ocr.run_ocr(video_id)
        if ocr_results:
            print(f"✓ OCR complete ({len(ocr_results.get('frames', []))} frames)")
        else:
            print("✗ OCR failed")
        
        # Describe frames
        describer = FrameDescriber(sqlite_store=sqlite, file_store=files)
        descriptions = describer.describe_frames(video_id)
        if descriptions:
            print(f"✓ Frame descriptions complete ({len(descriptions)} frames)")
        else:
            print("✗ Frame description failed")
        
        # Build segments
        builder = SegmentBuilder(sqlite_store=sqlite, file_store=files)
        segments = builder.build_segments(video_id)
        if segments:
            print(f"✓ Built {len(segments)} multimodal segments")
        else:
            print("✗ Segment building failed")
        
        print(f"
✓ Ingestion complete! Video ID: {video_id}")
        print("
Next: Run build_kb.py to extract knowledge and load graph")
        
        return 0
        
    finally:
        sqlite.close()


if __name__ == "__main__":
    sys.exit(main())
