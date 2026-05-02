#!/usr/bin/env python3
"""Visual description module using Gemma vision model."""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

from src.config.settings import settings
from src.storage.sqlite_store import SQLiteStore
from src.storage.file_store import FileStore

# Import model clients
from models.gemma_client import GemmaVisionClient


class FrameDescriber:
    """Describe visual content in frames."""
    
    def __init__(self, api_base: str = None, api_key: str = None, model: str = None,
                 sqlite_store: SQLiteStore = None, file_store: FileStore = None):
        self.api_base = api_base or settings.gemma_api_base
        self.api_key = api_key or settings.gemma_api_key
        self.model = model or settings.gemma_model
        
        self.vision_client = GemmaVisionClient(
            api_base=self.api_base,
            api_key=self.api_key,
            model=self.model
        )
        
        self.sqlite = sqlite_store or SQLiteStore()
        self.files = file_store or FileStore()
    
    def describe_frames(self, video_id: str, prompt_file: str = None) -> Optional[List[Dict[str, Any]]]:
        """Describe visual content in frames.
        
        Args:
            video_id: ID of the video
            prompt_file: Optional path to custom prompt file
        
        Returns:
            List of visual descriptions
        """
        frames_dir = self.files.get_frames_dir(video_id)
        if not frames_dir.exists():
            print(f"Frames not found for {video_id}")
            return None
        
        # Load frames metadata
        frames_metadata = frames_dir / "metadata.json"
        if not frames_metadata.exists():
            print(f"Frames metadata not found for {video_id}")
            return None
        
        with open(frames_metadata, 'r') as f:
            frames = json.load(f)
        
        descriptions = []
        
        for frame_info in frames:
            frame_path = Path(frame_info["file_path"])
            
            if not frame_path.exists():
                continue
            
            # Get nearby transcript and OCR for context
            segment_id = frame_info.get("segment_id")
            transcript = ""
            ocr_text = ""
            
            if segment_id:
                segment = self.sqlite.get_segment(segment_id)
                if segment:
                    transcript = segment.get("transcript", "")
            
            frame = self.sqlite.get_frame(frame_info["frame_id"])
            if frame:
                ocr_text = frame.get("ocr_text", "")
            
            # Build prompt
            prompt = self._build_prompt(transcript, ocr_text, frame_info["timestamp"])
            
            try:
                # Get visual description
                description = self.vision_client.describe_image(
                    str(frame_path),
                    prompt,
                    system_prompt="You are analyzing a trading education video frame."
                )
                
                # Store in SQLite
                self.sqlite.create_frame(
                    frame_id=frame_info["frame_id"],
                    video_id=video_id,
                    timestamp=frame_info["timestamp"],
                    file_path=frame_info["file_path"],
                    visual_description=json.dumps(description)
                )
                
                descriptions.append({
                    "frame_id": frame_info["frame_id"],
                    "timestamp": frame_info["timestamp"],
                    "file_path": frame_info["file_path"],
                    "visual_description": description
                })
                
            except Exception as e:
                print(f"Error describing {frame_path}: {e}")
                descriptions.append({
                    "frame_id": frame_info["frame_id"],
                    "timestamp": frame_info["timestamp"],
                    "file_path": frame_info["file_path"],
                    "error": str(e)
                })
        
        # Save descriptions
        descriptions_path = self.files.get_visual_descriptions_path(video_id)
        with open(descriptions_path, 'w') as f:
            json.dump(descriptions, f, indent=2)
        
        return descriptions
    
    def _build_prompt(self, transcript: str, ocr_text: str, timestamp: float) -> str:
        """Build a prompt for visual description."""
        prompt = f"""You are analyzing a trading education video frame.
Describe only what you see in this frame.

Timestamp: {timestamp:.1f} seconds

If available, nearby transcript:
{transcript}

OCR text from this frame:
{ocr_text}

Please describe:
1. What type of chart is visible (candlestick, line, bar, etc.)?
2. What indicators are shown (RSI, MACD, moving averages, etc.)?
3. Are there any annotations, lines, or markers on the chart?
4. What trading setup or concept is being explained?
5. Any visible support/resistance levels, trendlines, or patterns?

Return your analysis as structured JSON with:
- visual_type: The type of visual content (chart, diagram, text, etc.)
- chart_description: Detailed description of what is visible
- visible_indicators: List of any visible indicators
- chart_pattern: Any recognizable patterns (head and shoulders, double top, etc.)
- visible_levels: Any visible levels (support, resistance, etc.)
- trading_interpretation: What the instructor appears to be explaining
- uncertainty: How certain you are about each observation (high/medium/low)
"""
        return prompt


def describe_frames(video_id: str) -> Optional[List[Dict[str, Any]]]:
    """Convenience function to describe frames."""
    describer = FrameDescriber()
    return describer.describe_frames(video_id)
