
"""
Database migration script to add new fields to existing tables
"""
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import engine, SessionLocal
from app.models.base import Base
from sqlalchemy import text

def column_exists(db, table_name, column_name):
    """Check if a column exists in a table using SQLite PRAGMA"""
    result = db.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    columns = [col[1] for col in result]
    return column_name in columns


def migrate_database():
    """
    Perform database migration
    """
    print("=" * 60)
    print("Starting database migration")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Check if last_message_preview column exists
        if not column_exists(db, 'sessions', 'last_message_preview'):
            print("\nAdding 'last_message_preview' column to sessions table...")
            add_preview_query = """
            ALTER TABLE sessions 
            ADD COLUMN last_message_preview TEXT
            """
            db.execute(text(add_preview_query))
            print("[OK] 'last_message_preview' column added")
            
            print("\nAdding 'message_count' column to sessions table...")
            add_count_query = """
            ALTER TABLE sessions 
            ADD COLUMN message_count INTEGER DEFAULT 0
            """
            db.execute(text(add_count_query))
            print("[OK] 'message_count' column added")
        
        # Check if react_steps column exists in messages table
        if not column_exists(db, 'messages', 'react_steps'):
            print("\nAdding 'react_steps' column to messages table...")
            add_react_steps_query = """
            ALTER TABLE messages 
            ADD COLUMN react_steps TEXT
            """
            db.execute(text(add_react_steps_query))
            print("[OK] 'react_steps' column added")
        
        db.commit()
        
        # Update existing sessions with message counts and previews
        print("\nUpdating existing sessions with message counts and previews...")
        update_query = """
        UPDATE sessions
        SET 
            message_count = (SELECT COUNT(*) FROM messages WHERE messages.session_id = sessions.id),
            last_message_preview = (
                SELECT content 
                FROM messages 
                WHERE messages.session_id = sessions.id 
                ORDER BY messages.created_at DESC 
                LIMIT 1
            )
        """
        db.execute(text(update_query))
        db.commit()
        print("[OK] Existing sessions updated")
        
        print("\n" + "=" * 60)
        print("Database migration completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate_database()
