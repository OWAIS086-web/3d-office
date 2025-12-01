#!/usr/bin/env python3
"""
Migration script to add is_online field to User model
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models.user import User

def migrate_is_online():
    """Add is_online field to existing users"""
    app = create_app()
    with app.app_context():
        try:
            # Check if column exists, if not add it
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            # Add missing column
            if 'is_online' not in columns:
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE users ADD COLUMN is_online BOOLEAN DEFAULT FALSE'))
                    conn.commit()
                print("Added is_online column")
            
            # Update existing users to have default status
            users = User.query.all()
            for user in users:
                if not hasattr(user, 'is_online') or user.is_online is None:
                    user.is_online = False
            
            db.session.commit()
            print(f"Migration completed successfully! Updated {len(users)} users.")
            
        except Exception as e:
            print(f"Migration failed: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    migrate_is_online()