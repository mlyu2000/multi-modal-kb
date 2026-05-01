#!/usr/bin/env python3
"""File system store for trading KB artifacts."""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from config.settings import VIDEOS_DIR, EXTRACTED_DIR, PROCESSED_DIR


class FileStore:
    """File system store for video artifacts and intermediate results."""
    
    def __init__(self):
        # Ensure directories exist
        VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
        EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    def get_video_path(self, video_id: str) -> Path:
        """Get the path to a video file."""
        return VIDEOS_DIR / f"{video_id}.mp4"
    
    def get_audio_path(self, video_id: str) -> Path:
        """Get the path to extracted audio."""
        return EXTRACTED_DIR / video_id / "audio.wav"
    
    def get_frames_dir(self, video_id: str) -> Path:
        """Get the directory for extracted frames."""
        return EXTRACTED_DIR / video_id / "frames"
    
    def get_frame_path(self, video_id: str, frame_id: str) -> Path:
        """Get the path to a specific frame."""
        return self.get_frames_dir(video_id) / f"{frame_id}.jpg"
    
    def get_ocr_path(self, video_id: str) -> Path:
        """Get the path to OCR results."""
        return EXTRACTED_DIR / video_id / "ocr.json"
    
    def get_transcript_path(self, video_id: str) -> Path:
        """Get the path to transcription results."""
        return EXTRACTED_DIR / video_id / "transcript.json"
    
    def get_visual_descriptions_path(self, video_id: str) -> Path:
        """Get the path to visual descriptions."""
        return EXTRACTED_DIR / video_id / "visual_descriptions.json"
    
    def get_segments_path(self, video_id: str) -> Path:
        """Get the path to segment results."""
        return PROCESSED_DIR / video_id / "segments.json"
    
    def get_knowledge_path(self, video_id: str) -> Path:
        """Get the path to extracted knowledge."""
        return PROCESSED_DIR / video_id / "knowledge.json"
    
    def save_frames(self, video_id: str, frames: List[Dict[str, Any]]) -> bool:
        """Save frame metadata."""
        frames_dir = self.get_frames_dir(video_id)
        frames_dir.mkdir(parents=True, exist_ok=True)
        
        metadata_file = frames_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(frames, f, indent=2)
        return True
    
    def save_ocr(self, video_id: str, ocr_results: Dict[str, Any]) -> bool:
        """Save OCR results."""
        with open(self.get_ocr_path(video_id), 'w') as f:
            json.dump(ocr_results, f, indent=2)
        return True
    
    def save_transcript(self, video_id: str, transcript: Dict[str, Any]) -> bool:
        """Save transcription results."""
        with open(self.get_transcript_path(video_id), 'w') as f:
            json.dump(transcript, f, indent=2)
        return True
    
    def save_visual_descriptions(self, video_id: str, descriptions: List[Dict[str, Any]]) -> bool:
        """Save visual descriptions."""
        with open(self.get_visual_descriptions_path(video_id), 'w') as f:
            json.dump(descriptions, f, indent=2)
        return True
    
    def save_segments(self, video_id: str, segments: List[Dict[str, Any]]) -> bool:
        """Save segment results."""
        segments_dir = PROCESSED_DIR / video_id
        segments_dir.mkdir(parents=True, exist_ok=True)
        
        with open(self.get_segments_path(video_id), 'w') as f:
            json.dump(segments, f, indent=2)
        return True
    
    def save_knowledge(self, video_id: str, knowledge: Dict[str, Any]) -> bool:
        """Save extracted knowledge."""
        knowledge_dir = PROCESSED_DIR / video_id
        knowledge_dir.mkdir(parents=True, exist_ok=True)
        
        with open(self.get_knowledge_path(video_id), 'w') as f:
            json.dump(knowledge, f, indent=2)
        return True
    
    def load_frames(self, video_id: str) -> Optional[List[Dict[str, Any]]]:
        """Load frame metadata."""
        frames_metadata = self.get_frames_dir(video_id) / "metadata.json"
        if frames_metadata.exists():
            with open(frames_metadata, 'r') as f:
                return json.load(f)
        return None
    
    def load_ocr(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Load OCR results."""
        if self.get_ocr_path(video_id).exists():
            with open(self.get_ocr_path(video_id), 'r') as f:
                return json.load(f)
        return None
    
    def load_transcript(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Load transcription results."""
        if self.get_transcript_path(video_id).exists():
            with open(self.get_transcript_path(video_id), 'r') as f:
                return json.load(f)
        return None
    
    def load_visual_descriptions(self, video_id: str) -> Optional[List[Dict[str, Any]]]:
        """Load visual descriptions."""
        if self.get_visual_descriptions_path(video_id).exists():
            with open(self.get_visual_descriptions_path(video_id), 'r') as f:
                return json.load(f)
        return None
    
    def load_segments(self, video_id: str) -> Optional[List[Dict[str, Any]]]:
        """Load segment results."""
        if self.get_segments_path(video_id).exists():
            with open(self.get_segments_path(video_id), 'r') as f:
                return json.load(f)
        return None
    
    def load_knowledge(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Load extracted knowledge."""
        if self.get_knowledge_path(video_id).exists():
            with open(self.get_knowledge_path(video_id), 'r') as f:
                return json.load(f)
        return None
    
    def list_videos(self) -> List[str]:
        """List all video IDs in the system."""
        videos = []
        for f in VIDEOS_DIR.glob("*.mp4"):
            videos.append(f.stem)
        return sorted(videos)
    
    def list_extracted(self) -> List[str]:
        """List all extracted video IDs."""
        extracted = []
        if EXTRACTED_DIR.exists():
            for d in EXTRACTED_DIR.iterdir():
                if d.is_dir():
                    extracted.append(d.name)
        return sorted(extracted)
    
    def clear_video_data(self, video_id: str, keep_source: bool = False) -> bool:
        """Clear all processed data for a video."""
        extracted_path = EXTRACTED_DIR / video_id
        processed_path = PROCESSED_DIR / video_id
        
        # Remove extracted data
        if extracted_path.exists():
            import shutil
            shutil.rmtree(extracted_path)
        
        # Remove processed data
        if processed_path.exists():
            import shutil
            shutil.rmtree(processed_path)
        
        if keep_source and self.get_video_path(video_id).exists():
            # Re-create extracted directories
            self.get_frames_dir(video_id).mkdir(parents=True, exist_ok=True)
        
        return True
