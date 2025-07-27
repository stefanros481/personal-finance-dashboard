#!/usr/bin/env python3
"""Initialize the database with sample data."""
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models import *  # noqa
from app.services.user import create_user
from app.schemas.user import UserCreate


def init_db():
    """Initialize database with sample data."""
    db = SessionLocal()
    
    try:
        # Create a test user
        test_user = UserCreate(
            email="test@example.com",
            password="testpass"
        )
        
        # Check if user already exists
        from app.services.user import get_user_by_email
        existing_user = get_user_by_email(db, test_user.email)
        
        if not existing_user:
            user = create_user(db, test_user)
            print(f"Created test user: {user.email}")
        else:
            print(f"Test user already exists: {existing_user.email}")
            
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_db()