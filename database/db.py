"""
Database Connection and Configuration
Handles database connections and basic operations
"""

import sqlite3
import logging
from contextlib import contextmanager
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class ModerationDatabase:
    def __init__(self, db_path: str = "moderation.db"):
        """
        Initialize database connection
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        try:
            with self.get_connection() as conn:
                # Create moderation_results table
                conn.execute("""
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
                conn.execute("""
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
                
                # Create content_categories table for analytics
                conn.execute("""
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
                
                # Create indexes for better performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON moderation_results(user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_content_type ON moderation_results(content_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON moderation_results(created_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_is_appropriate ON moderation_results(is_appropriate)")
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get database connection with automatic closing"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()
    
    def save_moderation_result(self, result: Dict[str, Any]) -> int:
        """
        Save moderation result to database
        
        Args:
            result: Moderation result dictionary
            
        Returns:
            ID of the inserted record
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO moderation_results (
                        user_id, content_id, content_type, is_appropriate,
                        confidence_score, flagged_categories, original_content_hash,
                        processed_content_info, service_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.get("user_id"),
                    result.get("content_id"),
                    result["content_type"],
                    result["is_appropriate"],
                    result["confidence_score"],
                    json.dumps(result.get("flagged_categories", [])),
                    result.get("content_hash"),
                    json.dumps(result.get("content_info", {})),
                    result.get("service_version", "1.0.0")
                ))
                
                record_id = cursor.lastrowid
                conn.commit()
                
                # Update user stats
                self._update_user_stats(
                    conn,
                    result.get("user_id"),
                    result["is_appropriate"]
                )
                
                # Update category stats
                for category in result.get("flagged_categories", []):
                    self._update_category_stats(
                        conn,
                        category,
                        result["content_type"]
                    )
                
                logger.info(f"Saved moderation result with ID: {record_id}")
                return record_id
                
        except Exception as e:
            logger.error(f"Error saving moderation result: {str(e)}")
            raise
    
    def _update_user_stats(self, conn, user_id: str, is_appropriate: bool):
        """Update user statistics"""
        if not user_id:
            return
        
        try:
            # Insert or update user stats
            conn.execute("""
                INSERT INTO user_stats (user_id, total_submissions, appropriate_submissions, flagged_submissions, last_submission_at)
                VALUES (?, 1, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    total_submissions = total_submissions + 1,
                    appropriate_submissions = appropriate_submissions + ?,
                    flagged_submissions = flagged_submissions + ?,
                    last_submission_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                user_id,
                1 if is_appropriate else 0,
                0 if is_appropriate else 1,
                1 if is_appropriate else 0,
                0 if is_appropriate else 1
            ))
            
        except Exception as e:
            logger.error(f"Error updating user stats: {str(e)}")
    
    def _update_category_stats(self, conn, category: str, content_type: str):
        """Update category statistics"""
        try:
            conn.execute("""
                INSERT INTO content_categories (category_name, content_type, detection_count)
                VALUES (?, ?, 1)
                ON CONFLICT(category_name, content_type) DO UPDATE SET
                    detection_count = detection_count + 1,
                    updated_at = CURRENT_TIMESTAMP
            """, (category, content_type))
            
        except Exception as e:
            logger.error(f"Error updating category stats: {str(e)}")
    
    def get_user_stats(self, user_id: str) -> Optional[Dict]:
        """Get statistics for a specific user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM user_stats WHERE user_id = ?
                """, (user_id,))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            return None
    
    def get_moderation_history(self, user_id: str = None, limit: int = 100) -> List[Dict]:
        """Get moderation history"""
        try:
            with self.get_connection() as conn:
                if user_id:
                    cursor = conn.execute("""
                        SELECT * FROM moderation_results 
                        WHERE user_id = ? 
                        ORDER BY created_at DESC 
                        LIMIT ?
                    """, (user_id, limit))
                else:
                    cursor = conn.execute("""
                        SELECT * FROM moderation_results 
                        ORDER BY created_at DESC 
                        LIMIT ?
                    """, (limit,))
                
                results = []
                for row in cursor.fetchall():
                    result = dict(row)
                    # Parse JSON fields
                    result["flagged_categories"] = json.loads(result["flagged_categories"] or "[]")
                    result["processed_content_info"] = json.loads(result["processed_content_info"] or "{}")
                    results.append(result)
                
                return results
                
        except Exception as e:
            logger.error(f"Error getting moderation history: {str(e)}")
            return []
    
    def get_analytics_summary(self) -> Dict:
        """Get analytics summary"""
        try:
            with self.get_connection() as conn:
                # Overall stats
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_moderations,
                        SUM(CASE WHEN is_appropriate = 1 THEN 1 ELSE 0 END) as appropriate_count,
                        SUM(CASE WHEN is_appropriate = 0 THEN 1 ELSE 0 END) as flagged_count,
                        AVG(confidence_score) as avg_confidence,
                        COUNT(DISTINCT user_id) as unique_users
                    FROM moderation_results
                """)
                overall_stats = dict(cursor.fetchone())
                
                # Category breakdown
                cursor = conn.execute("""
                    SELECT category_name, content_type, detection_count
                    FROM content_categories
                    ORDER BY detection_count DESC
                """)
                category_stats = [dict(row) for row in cursor.fetchall()]
                
                # Recent activity (last 24 hours)
                cursor = conn.execute("""
                    SELECT COUNT(*) as recent_moderations
                    FROM moderation_results
                    WHERE created_at >= datetime('now', '-1 day')
                """)
                recent_stats = dict(cursor.fetchone())
                
                return {
                    "overall": overall_stats,
                    "categories": category_stats,
                    "recent": recent_stats,
                    "generated_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting analytics summary: {str(e)}")
            return {}

# Global database instance
db = ModerationDatabase()

def init_db(db_path: str = "moderation.db") -> bool:
    """
    Initialize database with tables and schema
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        bool: True if initialization successful, False otherwise
    """
    try:
        global db
        db = ModerationDatabase(db_path)
        logger.info(f"Database initialized successfully at {db_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        return False

def get_db() -> ModerationDatabase:
    """Get the global database instance"""
    return db
