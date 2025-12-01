#!/usr/bin/env python3
"""
Migration script to add missing columns to messages table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db

def migrate_messages_table():
    """Add missing columns to messages table"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🚀 Updating Messages Table Structure")
            print("=" * 50)
            
            # Check current table structure
            inspector = db.inspect(db.engine)
            columns = inspector.get_columns('messages')
            existing_columns = [col['name'] for col in columns]
            
            print("📋 Current messages table columns:")
            for col in existing_columns:
                print(f"   - {col}")
            
            # Add missing columns
            missing_columns = []
            
            if 'group_id' not in existing_columns:
                missing_columns.append('group_id')
                
            if 'chat_type' not in existing_columns:
                missing_columns.append('chat_type')
            
            if missing_columns:
                print(f"\n🔧 Adding missing columns: {missing_columns}")
                
                # Add group_id column
                if 'group_id' in missing_columns:
                    with db.engine.connect() as conn:
                        conn.execute(db.text('ALTER TABLE messages ADD COLUMN group_id INTEGER'))
                        conn.commit()
                    print("✅ Added group_id column")
                
                # Add chat_type column
                if 'chat_type' in missing_columns:
                    with db.engine.connect() as conn:
                        conn.execute(db.text("ALTER TABLE messages ADD COLUMN chat_type VARCHAR(20) DEFAULT 'direct'"))
                        conn.commit()
                    print("✅ Added chat_type column")
                
                # Update existing messages to have chat_type = 'direct'
                with db.engine.connect() as conn:
                    conn.execute(db.text("UPDATE messages SET chat_type = 'direct' WHERE chat_type IS NULL"))
                    conn.commit()
                print("✅ Updated existing messages with chat_type = 'direct'")
                
                print("\n🎉 Messages table updated successfully!")
                
            else:
                print("\n✅ Messages table already has all required columns!")
            
            # Verify the update
            print("\n📋 Updated messages table structure:")
            columns = inspector.get_columns('messages')
            for col in columns:
                print(f"   - {col['name']}: {col['type']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating messages table: {e}")
            return False

if __name__ == "__main__":
    success = migrate_messages_table()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("\n🎯 Now you can:")
        print("   • Create and view groups")
        print("   • Send group messages")
        print("   • Switch between direct and group chats")
        print("\n🌐 Test the messaging at:")
        print("   http://localhost:5000/dashboard/messages/whatsapp")
    else:
        print("\n❌ Migration failed!")
        print("Please check the error messages above.")