#!/usr/bin/env python3
"""OCR module for extracting text from frames."""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False

from src.config.settings import settings
from src.storage.sqlite_store import SQLiteStore
from src.storage.file_store import FileStore


class FrameOCR:
    """Extract text from frames using OCR."""
    
    def __init__(self, lang: str = "en",
                 sqlite_store: SQLiteStore = None, file_store: FileStore = None):
        self.lang = lang
        
        if PADDLEOCR_AVAILABLE:
            self.ocr = PaddleOCR(use_angle_cls=True, lang=lang)
        else:
            self.ocr = None
            print("Warning: PaddleOCR not installed. Install with: pip install paddlepaddle paddleocr")
        
        self.sqlite = sqlite_store or SQLiteStore()
        self.files = file_store or FileStore()
    
    def run_ocr(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Run OCR on all frames for a video.
        
        Args:
            video_id: ID of the video
        
        Returns:
            OCR results dictionary
        """
        if not PADDLEOCR_AVAILABLE:
            print("PaddleOCR not available. Cannot run OCR.")
            return None
        
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
        
        ocr_results = {
            "video_id": video_id,
            "frames": []
        }
        
        for frame_info in frames:
            frame_path = Path(frame_info["file_path"])
            
            if not frame_path.exists():
                continue
            
            try:
                # Run PaddleOCR
                result = self.ocr.ocr(str(frame_path), cls=True)
                
                # Extract text
                ocr_text = ""
                if result[0]:
                    for line in result[0]:
                        ocr_text += f"{line[1][0]} "
                
                ocr_text = ocr_text.strip()
                
                # Store in SQLite
                self.sqlite.create_frame(
                    frame_id=frame_info["frame_id"],
                    video_id=video_id,
                    timestamp=frame_info["timestamp"],
                    file_path=frame_info["file_path"],
                    ocr_text=ocr_text
                )
                
                ocr_results["frames"].append({
                    "frame_id": frame_info["frame_id"],
                    "timestamp": frame_info["timestamp"],
                    "file_path": frame_info["file_path"],
                    "ocr_text": ocr_text,
                    "ocr_raw": result[0] if result[0] else []
                })
                
            except Exception as e:
                print(f"Error running OCR on {frame_path}: {e}")
                ocr_results["frames"].append({
                    "frame_id": frame_info["frame_id"],
                    "timestamp": frame_info["timestamp"],
                    "file_path": frame_info["file_path"],
                    "ocr_text": "",
                    "error": str(e)
                })
        
        # Save OCR results
        ocr_path = self.files.get_ocr_path(video_id)
        with open(ocr_path, 'w') as f:
            json.dump(ocr_results, f, indent=2)
        
        return ocr_results


def run_ocr(video_id: str) -> Optional[Dict[str, Any]]:
    """Convenience function to run OCR."""
    ocr = FrameOCR()
    return ocr.run_ocr(video_id)
