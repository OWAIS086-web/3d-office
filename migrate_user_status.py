#!/usr/bin/env python3
"""
Migration script to add status tracking fields to User model
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models.user import User

def migrate_user_status():
    """Add status tracking fields to existing users"""
    app, _ = create_app()
    
    with app.app_context():
        try:
            # Check if columns exist, if not add them
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            if 'current_status' not in columns:
                print("Adding current_status column...")
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE users ADD COLUMN current_status VARCHAR(20) DEFAULT "offline"'))
                    conn.commit()
            
            if 'break_start_time' not in columns:
                print("Adding break_start_time column...")
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE users ADD COLUMN break_start_time DATETIME'))
                    conn.commit()
            
            # Update existing users to have default status
            users = User.query.all()
            for user in users:
                if not hasattr(user, 'current_status') or user.current_status is None:
                    user.current_status = 'offline'
            
            db.session.commit()
            print(f"Successfully migrated {len(users)} users")
            
        except Exception as e:
            print(f"Migration failed: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    migrate_user_status()