#!/usr/bin/env python3
"""
Fix Messages Schema - Make recipient_id nullable for group messages
"""

import sqlite3
import os
from datetime import datetime

def fix_messages_schema():
    """Fix the messages table to allow NULL recipient_id for group messages"""
    
    db_path = 'instance/app.db'
    
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Fixing messages table schema...")
        
        # Check current schema
        cursor.execute("PRAGMA table_info(messages)")
        columns = cursor.fetchall()
        print("📋 Current messages table schema:")
        for col in columns:
            print(f"   {col[1]} {col[2]} {'NOT NULL' if col[3] else 'NULL'}")
        
        # Create new table with correct schema
        cursor.execute("""
            CREATE TABLE messages_new (
                id INTEGER PRIMARY KEY,
                sender_id INTEGER NOT NULL,
                recipient_id INTEGER NULL,
                group_id INTEGER NULL,
                content TEXT NOT NULL,
                timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN NOT NULL DEFAULT 0,
                message_type VARCHAR(20) NOT NULL DEFAULT 'text',
                chat_type VARCHAR(20) NOT NULL DEFAULT 'direct',
                FOREIGN KEY (sender_id) REFERENCES users (id),
                FOREIGN KEY (recipient_id) REFERENCES users (id),
                FOREIGN KEY (group_id) REFERENCES groups (id)
            )
        """)
        
        # Copy existing data
        cursor.execute("""
            INSERT INTO messages_new 
            SELECT id, sender_id, recipient_id, group_id, content, timestamp, is_read, message_type, chat_type
            FROM messages
        """)
        
        # Drop old table and rename new one
        cursor.execute("DROP TABLE messages")
        cursor.execute("ALTER TABLE messages_new RENAME TO messages")
        
        # Commit changes
        conn.commit()
        
        print("✅ Messages table schema fixed successfully!")
        print("📝 recipient_id is now nullable for group messages")
        
        # Verify the fix
        cursor.execute("PRAGMA table_info(messages)")
        columns = cursor.fetchall()
        print("📋 Updated messages table schema:")
        for col in columns:
            print(f"   {col[1]} {col[2]} {'NOT NULL' if col[3] else 'NULL'}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error fixing schema: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print("🚀 Messages Schema Fix")
    print("=" * 50)
    
    success = fix_messages_schema()
    
    if success:
        print("\n✅ Schema fix completed successfully!")
        print("🔄 Please restart the application to use the updated schema.")
    else:
        print("\n❌ Schema fix failed!")
        print("🔍 Please check the error messages above.")