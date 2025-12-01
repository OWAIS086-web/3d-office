#!/usr/bin/env python3
"""
Migration script to add break management fields to User model
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models.user import User

def migrate_break_fields():
    """Add break management fields to existing users"""
    app = create_app()
    with app.app_context():
        try:
            # Check if columns exist, if not add them
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            # Add missing columns
            if 'break_duration' not in columns:
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE users ADD COLUMN break_duration INTEGER'))
                    conn.commit()
                print("Added break_duration column")
            
            if 'break_reason' not in columns:
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE users ADD COLUMN break_reason VARCHAR(200)'))
                    conn.commit()
                print("Added break_reason column")
            
            if 'status' not in columns:
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT "offline"'))
                    conn.commit()
                print("Added status column")
            
            # Update existing users to have default status
            users = User.query.all()
            for user in users:
                if not hasattr(user, 'status') or user.status is None:
                    user.status = 'offline'
            
            db.session.commit()
            print(f"Migration completed successfully! Updated {len(users)} users.")
            
        except Exception as e:
            print(f"Migration failed: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    migrate_break_fields()