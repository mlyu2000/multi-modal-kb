#!/usr/bin/env python3
"""SQLite database store for trading KB metadata."""

import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

from config.settings import SQLITE_PATH


class SQLiteStore:
    """SQLite store for video metadata and processing state."""
    
    def __init__(self, path: str = None):
        self.path = Path(path or SQLITE_PATH)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self._init_tables()
    
    def _init_tables(self):
        """Initialize database schema."""
        cursor = self.conn.cursor()
        
        # Videos table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id TEXT PRIMARY KEY,
            title TEXT,
            file_path TEXT NOT NULL,
            duration_seconds REAL,
            status TEXT DEFAULT 'registered',
            created_at TEXT,
            updated_at TEXT
        )
        """)
        
        # Segments table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS segments (
            id TEXT PRIMARY KEY,
            video_id TEXT NOT NULL,
            start_time REAL NOT NULL,
            end_time REAL NOT NULL,
            transcript TEXT,
            ocr_text TEXT,
            visual_summary TEXT,
            summary TEXT,
            keyframes_json TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY(video_id) REFERENCES videos(id)
        )
        """)
        
        # Frames table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS frames (
            id TEXT PRIMARY KEY,
            video_id TEXT NOT NULL,
            segment_id TEXT,
            timestamp REAL NOT NULL,
            file_path TEXT,
            ocr_text TEXT,
            visual_description TEXT,
            created_at TEXT,
            FOREIGN KEY(video_id) REFERENCES videos(id),
            FOREIGN KEY(segment_id) REFERENCES segments(id)
        )
        """)
        
        # Processing jobs table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS processing_jobs (
            id TEXT PRIMARY KEY,
            video_id TEXT NOT NULL,
            job_type TEXT NOT NULL,
            status TEXT NOT NULL,
            error_message TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY(video_id) REFERENCES videos(id)
        )
        """)
        
        # Entities table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
            confidence REAL,
            canonical_name TEXT,
            source_segment_id TEXT,
            created_at TEXT
        )
        """)
        
        # Relationships table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS relationships (
            id TEXT PRIMARY KEY,
            subject TEXT NOT NULL,
            subject_type TEXT NOT NULL,
            predicate TEXT NOT NULL,
            object TEXT NOT NULL,
            object_type TEXT NOT NULL,
            confidence REAL,
            evidence TEXT,
            source_segment_id TEXT,
            created_at TEXT
        )
        """)
        
        self.conn.commit()
    
    def register_video(self, video_id: str, title: Optional[str], file_path: str, duration_seconds: float) -> bool:
        """Register a new video."""
        now = datetime.utcnow().isoformat()
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO videos (id, title, file_path, duration_seconds, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'registered', ?, ?)
            ON CONFLICT(id) DO UPDATE SET file_path=excluded.file_path, duration_seconds=excluded.duration_seconds, updated_at=excluded.updated_at
        """, (video_id, title, file_path, duration_seconds, now, now))
        self.conn.commit()
        return True
    
    def get_video(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get video by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def update_video_status(self, video_id: str, status: str) -> bool:
        """Update video processing status."""
        now = datetime.utcnow().isoformat()
        cursor = self.conn.cursor()
        cursor.execute("UPDATE videos SET status = ?, updated_at = ? WHERE id = ?", (status, now, video_id))
        self.conn.commit()
        return True
    
    def create_segment(self, segment_id: str, video_id: str, start_time: float, end_time: float,
                      transcript: Optional[str] = None, ocr_text: Optional[str] = None,
                      visual_summary: Optional[str] = None, summary: Optional[str] = None,
                      keyframes_json: Optional[str] = None) -> bool:
        """Create a new segment."""
        now = datetime.utcnow().isoformat()
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO segments (id, video_id, start_time, end_time, transcript, ocr_text, visual_summary, summary, keyframes_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET transcript=excluded.transcript, ocr_text=excluded.ocr_text, visual_summary=excluded.visual_summary, summary=excluded.summary, updated_at=excluded.updated_at
        """, (segment_id, video_id, start_time, end_time, transcript, ocr_text, visual_summary, summary, keyframes_json, now))
        self.conn.commit()
        return True
    
    
    def update_segment(self, segment_id: str, **kwargs) -> bool:
        """Update segment fields."""
        set_clause = ", ".join([f"{k}=?" for k in kwargs.keys() if k != "segment_id"])
        values = list(kwargs.values()) + [segment_id]
        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE segments SET {set_clause} WHERE id = ?", values)
        self.conn.commit()
        return cursor.rowcount > 0
def create_frame(self, frame_id: str, video_id: str, timestamp: float, file_path: str,
                    segment_id: Optional[str] = None, ocr_text: Optional[str] = None,
                    visual_description: Optional[str] = None) -> bool:
        """Create a new frame record."""
        now = datetime.utcnow().isoformat()
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO frames (id, video_id, segment_id, timestamp, file_path, ocr_text, visual_description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET ocr_text=excluded.ocr_text, visual_description=excluded.visual_description
        """, (frame_id, video_id, segment_id, timestamp, file_path, ocr_text, visual_description, now))
        self.conn.commit()
        return True
    
    def create_processing_job(self, job_id: str, video_id: str, job_type: str, status: str,
                             error_message: Optional[str] = None) -> bool:
        """Create a processing job record."""
        now = datetime.utcnow().isoformat()
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO processing_jobs (id, video_id, job_type, status, error_message, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET status=excluded.status, error_message=excluded.error_message, updated_at=excluded.updated_at
        """, (job_id, video_id, job_type, status, error_message, now, now))
        self.conn.commit()
        return True
    
    def update_processing_job(self, job_id: str, status: str, error_message: Optional[str] = None) -> bool:
        """Update processing job status."""
        now = datetime.utcnow().isoformat()
        cursor = self.conn.cursor()
        cursor.execute("UPDATE processing_jobs SET status = ?, error_message = ?, updated_at = ? WHERE id = ?",
                      (status, error_message, now, job_id))
        self.conn.commit()
        return True
    
    def create_entity(self, entity_id: str, name: str, entity_type: str, description: Optional[str] = None,
                     confidence: Optional[float] = None, canonical_name: Optional[str] = None,
                     source_segment_id: Optional[str] = None) -> bool:
        """Create or update an entity."""
        now = datetime.utcnow().isoformat()
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO entities (id, name, type, description, confidence, canonical_name, source_segment_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET description=excluded.description, confidence=excluded.confidence, canonical_name=excluded.canonical_name
        """, (entity_id, name, entity_type, description, confidence, canonical_name, source_segment_id, now))
        self.conn.commit()
        return True
    
    def create_relationship(self, rel_id: str, subject: str, subject_type: str, predicate: str,
                           object_: str, object_type: str, confidence: Optional[float] = None,
                           evidence: Optional[str] = None, source_segment_id: Optional[str] = None) -> bool:
        """Create or update a relationship."""
        now = datetime.utcnow().isoformat()
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO relationships (id, subject, subject_type, predicate, object, object_type, confidence, evidence, source_segment_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET confidence=excluded.confidence, evidence=excluded.evidence
        """, (rel_id, subject, subject_type, predicate, object_, object_type, confidence, evidence, source_segment_id, now))
        self.conn.commit()
        return True
    
    def get_segments_for_video(self, video_id: str) -> List[Dict[str, Any]]:
        """Get all segments for a video."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM segments WHERE video_id = ?", (video_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_frames_for_video(self, video_id: str) -> List[Dict[str, Any]]:
        """Get all frames for a video."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM frames WHERE video_id = ?", (video_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_entities_for_segment(self, segment_id: str) -> List[Dict[str, Any]]:
        """Get entities for a segment."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM entities WHERE source_segment_id = ?", (segment_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_processing_jobs(self, video_id: str = None, status: str = None) -> List[Dict[str, Any]]:
        """Get processing jobs with optional filters."""
        cursor = self.conn.cursor()
        query = "SELECT * FROM processing_jobs WHERE 1=1"
        params = []
        if video_id:
            query += " AND video_id = ?"
            params.append(video_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC"
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def close(self):
        """Close database connection."""
        self.conn.close()

    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get an entity by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM entities WHERE id = ?", (entity_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
