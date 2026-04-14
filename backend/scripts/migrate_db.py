
"""
Database migration script to add new fields to existing tables
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import engine, SessionLocal
from app.models.base import Base
from sqlalchemy import text

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
        check_column_query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'sessions' 
        AND column_name = 'last_message_preview'
        """
        result = db.execute(text(check_column_query)).fetchone()
        
        if not result:
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
        else:
            print("\n[OK] Columns already exist, skipping migration")
        
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
