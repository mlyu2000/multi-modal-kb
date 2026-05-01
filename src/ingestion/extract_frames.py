#!/usr/bin/env python3
"""Frame extraction module."""

import os
from pathlib import Path
from typing import Dict, Any, List
import json
import math

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

try:
    from pymovements import SceneDetect
    PYSCEME_AVAILABLE = True
except ImportError:
    PYSCEME_AVAILABLE = False

from src.config.settings import settings
from src.storage.sqlite_store import SQLiteStore
from src.storage.file_store import FileStore


class FrameExtractor:
    """Extract frames from videos."""
    
    def __init__(self, interval_seconds: int = None,
                 sqlite_store: SQLiteStore = None, file_store: FileStore = None):
        self.interval = interval_seconds or settings.frame_interval_seconds
        self.sqlite = sqlite_store or SQLiteStore()
        self.files = file_store or FileStore()
    
    def extract_frames(self, video_id: str) -> Optional[List[Dict[str, Any]]]:
        """Extract frames from a video.
        
        Args:
            video_id: ID of the video
        
        Returns:
            List of frame metadata
        """
        if not OPENCV_AVAILABLE:
            print("OpenCV not installed. Install with: pip install opencv-python")
            return None
        
        video_path = self.files.get_video_path(video_id)
        if not video_path.exists():
            print(f"Video not found: {video_path}")
            return None
        
        # Create frames directory
        frames_dir = self.files.get_frames_dir(video_id)
        frames_dir.mkdir(parents=True, exist_ok=True)
        
        # Open video
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            print(f"Could not open video: {video_path}")
            return None
        
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps
            
            frames = []
            frame_num = 0
            saved_frame = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Calculate timestamp
                timestamp = frame_num / fps
                
                # Save frame at intervals
                if frame_num % int(fps * self.interval) == 0:
                    frame_id = f"{video_id}_frame_{saved_frame:06d}"
                    frame_path = frames_dir / f"{frame_id}.jpg"
                    
                    cv2.imwrite(str(frame_path), frame)
                    
                    frames.append({
                        "frame_id": frame_id,
                        "video_id": video_id,
                        "timestamp": timestamp,
                        "file_path": str(frame_path)
                    })
                    
                    # Store in SQLite
                    self.sqlite.create_frame(
                        frame_id=frame_id,
                        video_id=video_id,
                        timestamp=timestamp,
                        file_path=str(frame_path)
                    )
                    
                    saved_frame += 1
                
                frame_num += 1
            
            cap.release()
            
            # Also save frames metadata
            frames_file = frames_dir / "metadata.json"
            with open(frames_file, 'w') as f:
                json.dump(frames, f, indent=2)
            
            return frames
            
        finally:
            cap.release()
    
    def extract_frames_by_scenes(self, video_id: str) -> Optional[List[Dict[str, Any]]]:
        """Extract frames at scene boundaries.
        
        Args:
            video_id: ID of the video
        
        Returns:
            List of frame metadata
        """
        if not PYSCEME_AVAILABLE:
            print("pymovements not installed. Using time intervals instead.")
            return self.extract_frames(video_id)
        
        # This would use scene detection to extract frames at scene boundaries
        # For now, fall back to time-based extraction
        return self.extract_frames(video_id)


def extract_frames(video_id: str) -> Optional[List[Dict[str, Any]]]:
    """Convenience function to extract frames."""
    extractor = FrameExtractor()
    return extractor.extract_frames(video_id)
