#!/usr/bin/env python3
"""Audio extraction module using ffmpeg."""

import os
from pathlib import Path
from typing import Optional
import subprocess

from src.config.settings import settings
from src.storage.file_store import FileStore
from src.storage.sqlite_store import SQLiteStore


class AudioExtractor:
    """Extract audio from videos."""
    
    def __init__(self, file_store: FileStore = None, sqlite_store: SQLiteStore = None):
        self.files = file_store or FileStore()
        self.sqlite = sqlite_store or SQLiteStore()
    
    def extract_audio(self, video_id: str, output_format: str = "wav") -> Optional[Path]:
        """Extract audio from a video.
        
        Args:
            video_id: ID of the registered video
            output_format: Output format (wav, mp3, etc.)
        
        Returns:
            Path to extracted audio file
        """
        video_path = self.files.get_video_path(video_id)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        audio_path = self.files.get_audio_path(video_id)
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build ffmpeg command
        cmd = [
            "ffmpeg", "-y",  # Overwrite if exists
            "-i", str(video_path),
            "-vn",  # Disable video
            "-acodec", "pcm_s16le",  # WAV PCM
            "-ar", "16000",  # 16kHz sample rate
            "-ac", "1",  # Mono
            str(audio_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                print(f"FFmpeg error: {result.stderr}")
                return None
            
            # Update processing job status
            job_id = f"{video_id}_audio_extract"
            self.sqlite.create_processing_job(
                job_id=job_id,
                video_id=video_id,
                job_type="audio_extraction",
                status="completed"
            )
            
            return audio_path
            
        except subprocess.TimeoutExpired:
            print(f"Audio extraction timed out for {video_id}")
            self._update_job_status(video_id, "audio_extraction", "failed", "Timeout")
            return None
        except Exception as e:
            print(f"Error extracting audio for {video_id}: {e}")
            self._update_job_status(video_id, "audio_extraction", "failed", str(e))
            return None
    
    def _update_job_status(self, video_id: str, job_type: str, status: str, error: Optional[str] = None):
        """Update processing job status."""
        self.sqlite.create_processing_job(
            job_id=f"{video_id}_{job_type}",
            video_id=video_id,
            job_type=job_type,
            status=status,
            error_message=error
        )


def extract_audio(video_id: str, output_format: str = "wav") -> Optional[Path]:
    """Convenience function to extract audio."""
    extractor = AudioExtractor()
    return extractor.extract_audio(video_id, output_format)
