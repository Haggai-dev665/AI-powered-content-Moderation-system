"""
Database Migration: Initial Schema
Creates the initial database schema for the moderation system
"""

import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def run_migration(db_path: str = "moderation.db"):
    """
    Run the initial database migration
    
    Args:
        db_path: Path to SQLite database file
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info("Running initial database migration...")
        
        # Create moderation_results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS moderation_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                content_id TEXT,
                content_type TEXT NOT NULL CHECK (content_type IN ('text', 'image')),
                is_appropriate BOOLEAN NOT NULL,
                confidence_score REAL NOT NULL,
                flagged_categories TEXT,  -- JSON array
                original_content_hash TEXT,
                processed_content_info TEXT,  -- JSON object
                service_version TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create user_stats table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id TEXT PRIMARY KEY,
                total_submissions INTEGER DEFAULT 0,
                appropriate_submissions INTEGER DEFAULT 0,
                flagged_submissions INTEGER DEFAULT 0,
                last_submission_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create content_categories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name TEXT NOT NULL,
                content_type TEXT NOT NULL CHECK (content_type IN ('text', 'image')),
                detection_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category_name, content_type)
            )
        """)
        
        # Create migration_history table to track migrations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS migration_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                migration_name TEXT NOT NULL UNIQUE,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON moderation_results(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_type ON moderation_results(content_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON moderation_results(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_is_appropriate ON moderation_results(is_appropriate)")
        
        # Record this migration
        cursor.execute("""
            INSERT OR IGNORE INTO migration_history (migration_name)
            VALUES (?)
        """, ("001_initial_schema",))
        
        conn.commit()
        conn.close()
        
        logger.info("Initial database migration completed successfully")
        
    except Exception as e:
        logger.error(f"Error running database migration: {str(e)}")
        raise

if __name__ == "__main__":
    run_migration()
