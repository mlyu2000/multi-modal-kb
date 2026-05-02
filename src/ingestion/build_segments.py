#!/usr/bin/env python3
"""Build multimodal segments from extracted data."""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

from src.config.settings import settings
from src.storage.sqlite_store import SQLiteStore
from src.storage.file_store import FileStore


from src.embeddings.litellm_embed import LiteLMEmbeddingService
from src.storage.chroma_store import ChromaStore



class SegmentBuilder:
    """Build multimodal segments from extracted video data."""
    
    def __init__(self, min_seconds: int = None, max_seconds: int = None,
                 sqlite_store: SQLiteStore = None, file_store: FileStore = None,
                 embedding_service: LiteLMEmbeddingService = None, chroma_store: ChromaVectorStore = None):
        self.min_seconds = min_seconds or settings.segment_min_seconds
        self.max_seconds = max_seconds or settings.segment_max_seconds
        self.sqlite = sqlite_store or SQLiteStore()
        self.files = file_store or FileStore()
        self.embedding_service = embedding_service or LiteLMEmbeddingService()
        self.chroma_store = chroma_store or ChromaStore()
    

    def _build_multimodal_text(self, video_id: str, segment_id: str,
                                transcript: str, ocr_text: str, visual_summary: str,
                                start_time: float, end_time: float) -> str:
        """Build multimodal text blob for embedding.
        
        Creates a condensed, information-rich text that combines
        transcript, OCR, and visual context for better retrieval.
        """
        return f"""Video: {video_id}
Segment: {segment_id}
Time: {self._format_time(start_time)}-{self._format_time(end_time)}

Transcript:
{transcript}

OCR:
{ocr_text}

Visual Summary:
{visual_summary}

Merged Summary:
This segment from {video_id} covers content between {self._format_time(start_time)} and {self._format_time(end_time)}, featuring {visual_summary[:100] if visual_summary else 'visual content'} with transcript explaining: {transcript[:150] if transcript else 'content'}."""

    def _format_time(self, seconds: float) -> str:
        """Format seconds as MM:SS."""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"


    def build_segments(self, video_id: str) -> Optional[List[Dict[str, Any]]]:
        """Build multimodal segments for a video.
        
        Args:
            video_id: ID of the video
        
        Returns:
            List of segment objects
        """
        # Load extracted data
        transcript = self.files.load_transcript(video_id)
        ocr = self.files.load_ocr(video_id)
        visual = self.files.load_visual_descriptions(video_id)
        frames = self.files.load_frames(video_id)
        
        if not transcript or not transcript.get("segments"):
            print(f"No transcript found for {video_id}")
            return None
        
        # Build segments based on transcript with multimodal context
        segments = []
        segment_count = 0
        
        transcript_segments = transcript["segments"]
        
        # Group transcript segments into multimodal chunks
        current_chunk = []
        chunk_start = None
        chunk_end = None
        
        for seg in transcript_segments:
            seg_start = seg["start"]
            seg_end = seg["end"]
            
            if chunk_start is None:
                chunk_start = seg_start
                chunk_end = seg_end
            
            # Add to current chunk
            current_chunk.append(seg)
            chunk_end = seg_end
            
            # Check if chunk is large enough
            chunk_duration = chunk_end - chunk_start
            
            if chunk_duration >= self.min_seconds:
                # Build segment object
                segment_id = f"{video_id}_seg_{segment_count:03d}"
                
                # Get frames in this time range
                segment_frames = []
                if frames:
                    for frame in frames:
                        if chunk_start <= frame["timestamp"] <= chunk_end:
                            segment_frames.append(frame["file_path"])
                
                # Get OCR in this time range
                segment_ocr = ""
                if ocr:
                    for frame in ocr.get("frames", []):
                        if chunk_start <= frame["timestamp"] <= chunk_end:
                            segment_ocr += f"{frame.get('ocr_text', '')} "
                
                # Get visual descriptions in this time range
                visual_summary = ""
                if visual:
                    for desc in visual:
                        ts = desc.get("timestamp", 0)
                        if chunk_start <= ts <= chunk_end:
                            visual_summary += f"{desc.get('visual_description', {}).get('chart_description', '')} "
                
                # Build final transcript
                full_transcript = " ".join([s["text"] for s in current_chunk])
                
                segment = {
                    "segment_id": segment_id,
                    "video_id": video_id,
                    "start_time": chunk_start,
                    "end_time": chunk_end,
                    "transcript": full_transcript,
                    "ocr_text": segment_ocr.strip(),
                    "visual_summary": visual_summary.strip(),
                    "keyframes": segment_frames,
                    "transcript_segments": current_chunk
                }
                
                # Store in SQLite
                self.sqlite.create_segment(
                    segment_id=segment_id,
                    video_id=video_id,
                    start_time=chunk_start,
                    end_time=chunk_end,
                    transcript=full_transcript,
                    ocr_text=segment_ocr.strip(),
                    visual_summary=visual_summary.strip(),
                    keyframes_json=json.dumps(segment_frames)
                )
                
                # Build multimodal text for embedding
                multimodal_text = self._build_multimodal_text(
                    video_id=video_id,
                    segment_id=segment_id,
                    transcript=full_transcript,
                    ocr_text=segment_ocr.strip(),
                    visual_summary=visual_summary.strip(),
                    start_time=chunk_start,
                    end_time=chunk_end
                )
                
                # Generate embedding
                embedding = self.embedding_service.embed(multimodal_text, input_type="passage")
                
                # Store in ChromaDB
                # Store in ChromaDB (metadata only, embedding stored via add_embeddings method)
                # Store in ChromaDB with embedding
                self.chroma_store.add_segment_with_embedding(
                    segment_id=segment_id,
                    text=multimodal_text,
                    embedding=embedding,
                    metadata={
                        "video_id": video_id,
                        "chapter": "Segment",
                        "start_sec": chunk_start,
                        "end_sec": chunk_end,
                        "visual_type": "slide",  # Default - fix this
                        "transcript": full_transcript,
                        "ocr_text": segment_ocr.strip(),
                        "has_ocr": bool(segment_ocr.strip())
                    }
                )
                
                segments.append(segment)
                segment_count += 1
                
                # Reset for next segment
                current_chunk = []
                chunk_start = None
        
        # Handle remaining content
        if current_chunk and chunk_start is not None:
            segment_id = f"{video_id}_seg_{segment_count:03d}"
            chunk_end = max(s["end"] for s in current_chunk)
            full_transcript = " ".join([s["text"] for s in current_chunk])
            
            segment = {
                "segment_id": segment_id,
                "video_id": video_id,
                "start_time": chunk_start,
                "end_time": chunk_end,
                "transcript": full_transcript,
                "ocr_text": "",
                "visual_summary": "",
                "keyframes": [],
                "transcript_segments": current_chunk
            }
            
            # Save to SQLite
            self.sqlite.create_segment(
                segment_id=segment_id,
                video_id=video_id,
                start_time=chunk_start,
                end_time=chunk_end,
                transcript=full_transcript,
                ocr_text="",
                visual_summary="",
                keyframes_json=json.dumps([])
            )
            
            segments.append(segment)
        
        # Save segments
        self.files.save_segments(video_id, segments)
        
        return segments
    
    def create_fine_grained_segments(self, video_id: str, segment_length: int = 30) -> List[Dict[str, Any]]:
        """Create fine-grained segments of fixed length.
        
        Args:
            video_id: ID of the video
            segment_length: Length of each segment in seconds
        
        Returns:
            List of fine-grained segments
        """
        transcript = self.files.load_transcript(video_id)
        
        if not transcript or not transcript.get("segments"):
            return []
        
        segments = []
        transcript_segments = transcript["segments"]
        
        current_segment = []
        current_start = None
        
        for seg in transcript_segments:
            if current_start is None:
                current_start = seg["start"]
            
            current_segment.append(seg)
            
            # Check if we should finalize this segment
            current_end = seg["end"]
            duration = current_end - current_start
            
            if duration >= segment_length:
                segment_id = f"{video_id}_seg_{len(segments):03d}"
                
                segment = {
                    "segment_id": segment_id,
                    "video_id": video_id,
                    "start_time": current_start,
                    "end_time": current_end,
                    "transcript": " ".join([s["text"] for s in current_segment]),
                    "transcript_segments": current_segment.copy()
                }
                
                segments.append(segment)
                current_segment = []
                current_start = None
        
        # Handle remaining
        if current_segment:
            segment_id = f"{video_id}_seg_{len(segments):03d}"
            current_end = max(s["end"] for s in current_segment)
            
            segments.append({
                "segment_id": segment_id,
                "video_id": video_id,
                "start_time": current_start,
                "end_time": current_end,
                "transcript": " ".join([s["text"] for s in current_segment]),
                "transcript_segments": current_segment
            })
        
        return segments


def build_segments(video_id: str) -> Optional[List[Dict[str, Any]]]:
    """Convenience function to build segments."""
    builder = SegmentBuilder()
    return builder.build_segments(video_id)
