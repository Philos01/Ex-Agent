"""
Script to check and update user roles in the database
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import SessionLocal
from app.models.user import User

def list_users():
    """List all users in the database"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"\nFound {len(users)} users:")
        print("-" * 80)
        for user in users:
            print(f"ID: {user.id}")
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Role: {user.role}")
            print(f"Active: {user.is_active}")
            print("-" * 80)
        return users
    finally:
        db.close()

def update_user_role(username: str, new_role: str = "admin"):
    """Update a user's role"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            print(f"User '{username}' not found!")
            return False
        
        old_role = user.role
        user.role = new_role
        db.commit()
        print(f"Successfully updated user '{username}' role from '{old_role}' to '{new_role}'")
        return True
    except Exception as e:
        print(f"Error updating user role: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage user roles")
    parser.add_argument("action", choices=["list", "update"], help="Action to perform")
    parser.add_argument("--username", help="Username to update (for 'update' action)")
    parser.add_argument("--role", default="admin", help="New role (for 'update' action, default: admin)")
    
    args = parser.parse_args()
    
    if args.action == "list":
        list_users()
    elif args.action == "update":
        if not args.username:
            print("Error: --username is required for 'update' action")
            sys.exit(1)
        update_user_role(args.username, args.role)
