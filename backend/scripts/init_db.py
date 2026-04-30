
"""
Database initialization script
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import engine, Base
from app.models import (
    User,
    Session,
    Message,
    Document,
    Permission,
    RolePermission,
    AuditLog
)

def create_tables():
    """
    Create all database tables
    """
    print("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] All tables created successfully!")
        print(f"\nCreated tables:")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")
    except Exception as e:
        print(f"[ERROR] Error creating tables: {e}")
        raise

def drop_tables():
    """
    Drop all database tables (use with caution!)
    """
    print("WARNING: This will drop all tables!")
    confirm = input("Are you sure? Type 'YES' to confirm: ")
    if confirm != "YES":
        print("Operation cancelled.")
        return
    
    print("Dropping all tables...")
    try:
        Base.metadata.drop_all(bind=engine)
        print("[OK] All tables dropped successfully!")
    except Exception as e:
        print(f"[ERROR] Error dropping tables: {e}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database management")
    parser.add_argument("command", choices=["create", "drop"], help="Command to execute")
    
    args = parser.parse_args()
    
    if args.command == "create":
        create_tables()
    elif args.command == "drop":
        drop_tables()
