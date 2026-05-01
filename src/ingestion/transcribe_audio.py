#!/usr/bin/env python3
"""Audio transcription module using faster-whisper."""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

from src.config.settings import settings
from src.storage.sqlite_store import SQLiteStore
from src.storage.file_store import FileStore


class AudioTranscriber:
    """Transcribe audio to text using Whisper."""
    
    def __init__(self, model_name: str = None, device: str = None,
                 sqlite_store: SQLiteStore = None, file_store: FileStore = None):
        self.model_name = model_name or settings.whisper_model
        self.device = device or settings.device
        
        if WHISPER_AVAILABLE:
            self.model = WhisperModel(self.model_name, device=self.device)
        else:
            self.model = None
            print("Warning: faster-whisper not installed. Install with: pip install faster-whisper")
        
        self.sqlite = sqlite_store or SQLiteStore()
        self.files = file_store or FileStore()
    
    def transcribe(self, video_id: str, audio_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
        """Transcribe video audio.
        
        Args:
            video_id: ID of the video
            audio_path: Optional path to audio file (extracted if not provided)
        
        Returns:
            Transcription with segments
        """
        if not WHISPER_AVAILABLE:
            print("faster-whisper not available. Cannot transcribe.")
            return None
        
        if audio_path is None:
            audio_path = self.files.get_audio_path(video_id)
        
        if not audio_path.exists():
            print(f"Audio file not found: {audio_path}")
            return None
        
        try:
            # Transcribe with Whisper
            segments, info = self.model.transcribe(
                str(audio_path),
                word_timestamps=True,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # Build segments list
            transcription_segments = []
            for segment in segments:
                transcription_segments.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "words": [
                        {"word": w.word, "start": w.start, "end": w.end}
                        for w in segment.words
                    ] if segment.words else []
                })
            
            # Build result
            result = {
                "video_id": video_id,
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": info.duration,
                "segments": transcription_segments,
                "extracted_at": __import__('datetime').datetime.utcnow().isoformat()
            }
            
            # Save to file
            transcript_path = self.files.get_transcript_path(video_id)
            with open(transcript_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            # Store segment metadata in SQLite
            for seg in transcription_segments:
                segment_id = f"{video_id}_seg_{int(seg['start'])}_{int(seg['end'])}"
                self.sqlite.create_segment(
                    segment_id=segment_id,
                    video_id=video_id,
                    start_time=seg['start'],
                    end_time=seg['end'],
                    transcript=seg['text'],
                    keyframes_json=json.dumps([])
                )
            
            # Update processing job
            job_id = f"{video_id}_transcribe"
            self.sqlite.create_processing_job(
                job_id=job_id,
                video_id=video_id,
                job_type="transcription",
                status="completed",
                error_message=None
            )
            
            return result
            
        except Exception as e:
            print(f"Error transcribing {video_id}: {e}")
            self.sqlite.create_processing_job(
                job_id=f"{video_id}_transcribe",
                video_id=video_id,
                job_type="transcription",
                status="failed",
                error_message=str(e)
            )
            return None
    
    def transcribe_audio_file(self, audio_path: str) -> Dict[str, Any]:
        """Transcribe a standalone audio file.
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Transcription with segments
        """
        if not WHISPER_AVAILABLE:
            return {"error": "faster-whisper not installed"}
        
        audio_path = Path(audio_path)
        segments, info = self.model.transcribe(
            str(audio_path),
            word_timestamps=True,
            vad_filter=True
        )
        
        transcription_segments = []
        for segment in segments:
            transcription_segments.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            })
        
        return {
            "audio_file": str(audio_path),
            "language": info.language,
            "duration": info.duration,
            "segments": transcription_segments
        }


def transcribe_audio(video_id: str) -> Optional[Dict[str, Any]]:
    """Convenience function to transcribe a video."""
    transcriber = AudioTranscriber()
    return transcriber.transcribe(video_id)
