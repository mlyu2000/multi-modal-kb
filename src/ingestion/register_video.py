#!/usr/bin/env python3
"""Video registration module."""

import os
from pathlib import Path
from typing import Optional
import subprocess

from src.config.settings import settings
from src.storage.sqlite_store import SQLiteStore
from src.storage.file_store import FileStore


class VideoRegistrar:
    """Register and register videos for processing."""
    
    def __init__(self, sqlite_store: SQLiteStore = None, file_store: FileStore = None):
        self.sqlite = sqlite_store or SQLiteStore()
        self.files = file_store or FileStore()
    
    def register_video(self, video_path: str, title: Optional[str] = None, 
                      video_id: Optional[str] = None) -> str:
        """Register a video for processing.
        
        Args:
            video_path: Path to the video file
            title: Optional title for the video
            video_id: Optional custom ID (generated from filename if not provided)
        
        Returns:
            The video ID
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        # Generate video ID from filename if not provided
        if video_id is None:
            video_id = video_path.stem
        
        # Get video duration using ffprobe
        duration = self._get_video_duration(video_path)
        
        # Register in SQLite
        self.sqlite.register_video(
            video_id=video_id,
            title=title or video_path.stem,
            file_path=str(video_path),
            duration_seconds=duration
        )
        
        # Create extracted directory
        extracted_path = self.files.EXTRACTED_DIR / video_id
        extracted_path.mkdir(parents=True, exist_ok=True)
        
        return video_id
    
    def _get_video_duration(self, video_path: Path) -> float:
        """Get video duration in seconds using ffprobe."""
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return float(result.stdout.strip())
        except Exception as e:
            print(f"Warning: Could not get duration for {video_path}: {e}")
            return 0.0
    
    def is_registered(self, video_id: str) -> bool:
        """Check if a video is registered."""
        return self.sqlite.get_video(video_id) is not None
    
    def get_registration(self, video_id: str) -> Optional[dict]:
        """Get registration info for a video."""
        return self.sqlite.get_video(video_id)


def register_video(video_path: str, title: Optional[str] = None,
                  video_id: Optional[str] = None) -> str:
    """Convenience function to register a video."""
    registrar = VideoRegistrar()
    return registrar.register_video(video_path, title, video_id)
