#!/usr/bin/env python3
"""SQLite schema migration for category/school/tags support."""

import sqlite3
import os


def migrate_to_category_support():
    """Add category, school_of_thought, and tags columns to videos table."""
    db_path = os.path.join(os.path.dirname(__file__), "../../db/metadata.sqlite")
    db_path = os.path.abspath(db_path)
    
    print(f"Checking database: {db_path}")
    
    if not os.path.exists(db_path):
        print("Database not found - creating fresh schema")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(videos)")
    columns = [col[1] for col in cursor.fetchall()]
    
    additions = []
    if "category" not in columns:
        additions.append(("category", "TEXT DEFAULT 'general'"))
    if "school_of_thought" not in columns:
        additions.append(("school_of_thought", "TEXT DEFAULT 'default'"))
    if "tags" not in columns:
        additions.append(("tags", "TEXT DEFAULT '[]'"))
    
    if additions:
        print(f"Adding columns: {', '.join([a[0] for a in additions])}")
        for col_name, col_def in additions:
            cursor.execute(f"ALTER TABLE videos ADD COLUMN {col_name} {col_def}")
        conn.commit()
        print("✓ Migration complete")
    else:
        print("✓ Schema already up-to-date")
    
    conn.close()


if __name__ == "__main__":
    migrate_to_category_support()
