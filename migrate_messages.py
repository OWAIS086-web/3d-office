#!/usr/bin/env python3
"""
Migration script to add messages table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models.message import Message

def migrate_messages():
    """Add messages table to database"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create messages table
            db.create_all()
            print("✅ Messages table created successfully!")
            
            # Verify table exists
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'messages' in tables:
                print("✅ Messages table verified in database")
                
                # Show table structure
                columns = inspector.get_columns('messages')
                print("\n📋 Messages table structure:")
                for col in columns:
                    print(f"   - {col['name']}: {col['type']}")
            else:
                print("❌ Messages table not found in database")
                
        except Exception as e:
            print(f"❌ Error creating messages table: {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("🚀 Adding Messages Table to Database")
    print("=" * 40)
    
    success = migrate_messages()
    
    if success:
        print("\n✅ Messages migration completed successfully!")
        print("\n🎉 Features now available:")
        print("   • User-to-user messaging")
        print("   • Real-time message updates")
        print("   • Message read status")
        print("   • Conversation history")
    else:
        print("\n❌ Messages migration failed!")
        print("Please check the error messages above.")