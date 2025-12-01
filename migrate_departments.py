#!/usr/bin/env python3
"""
Add departments to existing users
"""

import sqlite3
import os
import random
from datetime import datetime

def migrate_departments():
    """Add departments to existing users"""
    
    db_path = 'remote_work_monitor.db'
    
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Adding departments to users...")
        
        # Check if department column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'department' not in columns:
            print("📋 Adding department column...")
            cursor.execute("ALTER TABLE users ADD COLUMN department VARCHAR(50) DEFAULT 'GENERAL'")
        
        # Get all users without departments
        cursor.execute("SELECT id, username, is_admin FROM users WHERE department IS NULL OR department = ''")
        users = cursor.fetchall()
        
        if not users:
            print("✅ All users already have departments assigned!")
            conn.close()
            return True
        
        # Department options
        departments = ['ENGINEERING', 'MARKETING', 'SALES', 'HR', 'GENERAL']
        
        # Assign departments
        for user_id, username, is_admin in users:
            if is_admin:
                # Admins get GENERAL department
                dept = 'GENERAL'
            else:
                # Regular users get random departments for demo
                dept = random.choice(departments)
            
            cursor.execute("UPDATE users SET department = ? WHERE id = ?", (dept, user_id))
            print(f"   👤 {username} → {dept}")
        
        # Commit changes
        conn.commit()
        
        print(f"✅ Updated {len(users)} users with departments!")
        
        # Show department distribution
        cursor.execute("SELECT department, COUNT(*) FROM users GROUP BY department")
        distribution = cursor.fetchall()
        
        print("\n📊 Department Distribution:")
        for dept, count in distribution:
            print(f"   {dept}: {count} users")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error migrating departments: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print("🚀 Department Migration")
    print("=" * 50)
    
    success = migrate_departments()
    
    if success:
        print("\n✅ Department migration completed successfully!")
        print("🏢 Users now have department assignments for office layout.")
    else:
        print("\n❌ Department migration failed!")
        print("🔍 Please check the error messages above.")