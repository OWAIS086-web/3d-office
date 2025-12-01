#!/usr/bin/env python3
"""
Test script to check group functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_groups():
    """Test group creation and retrieval"""
    try:
        from app import create_app, db
        from models.user import User
        from models.group import Group
        from models.message import Message
        
        app = create_app()
        
        with app.app_context():
            print("🧪 Testing Group Functionality")
            print("=" * 40)
            
            # Check if tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            print("📋 Available tables:")
            for table in tables:
                print(f"   - {table}")
            
            # Check groups
            groups = Group.query.all()
            print(f"\n📊 Found {len(groups)} groups:")
            for group in groups:
                print(f"   - {group.name} (ID: {group.id})")
                try:
                    member_count = len(group.members)
                    print(f"     Members: {member_count}")
                except Exception as e:
                    print(f"     Error getting members: {e}")
            
            # Check users
            users = User.query.all()
            print(f"\n👥 Found {len(users)} users:")
            for user in users:
                print(f"   - {user.username} (ID: {user.id})")
            
            # Test conversation loading
            if users:
                test_user = users[0]
                print(f"\n🔍 Testing conversations for user: {test_user.username}")
                
                try:
                    conversations = Message.get_user_conversations(test_user.id)
                    print(f"   Found {len(conversations)} conversations:")
                    for conv in conversations:
                        print(f"   - {conv['type']}: {conv['name']}")
                except Exception as e:
                    print(f"   Error loading conversations: {e}")
            
            return True
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    test_groups()