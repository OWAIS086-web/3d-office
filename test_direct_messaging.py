#!/usr/bin/env python3
"""
Test script for direct messaging functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_direct_messaging():
    """Test direct messaging functionality"""
    try:
        from app import create_app, db
        from models.user import User
        from models.message import Message
        
        app = create_app()
        
        with app.app_context():
            print("🧪 Testing Direct Messaging")
            print("=" * 40)
            
            # Get users
            users = User.query.all()
            if len(users) < 2:
                print("❌ Need at least 2 users for testing")
                return False
            
            user1 = users[0]
            user2 = users[1]
            
            print(f"👤 User 1: {user1.username} (ID: {user1.id})")
            print(f"👤 User 2: {user2.username} (ID: {user2.id})")
            
            # Create a test message
            test_message = Message(
                sender_id=user1.id,
                recipient_id=user2.id,
                content="Test direct message",
                message_type='text',
                chat_type='direct'
            )
            
            db.session.add(test_message)
            db.session.commit()
            
            print(f"✅ Created test message from {user1.username} to {user2.username}")
            
            # Test conversation retrieval
            conversation = Message.get_conversation(user1.id, user2.id)
            print(f"📨 Found {len(conversation)} messages in conversation")
            
            for msg in conversation:
                sender_name = user1.username if msg.sender_id == user1.id else user2.username
                print(f"   - {sender_name}: {msg.content}")
            
            # Test user conversations
            user1_conversations = Message.get_user_conversations(user1.id)
            print(f"\n💬 {user1.username} has {len(user1_conversations)} conversations:")
            for conv in user1_conversations:
                print(f"   - {conv['type']}: {conv['name']} - {conv['last_message']}")
            
            return True
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    success = test_direct_messaging()
    
    if success:
        print("\n✅ Direct messaging test completed!")
        print("\n🎯 Direct messaging should work in:")
        print("   • User WhatsApp interface: /dashboard/messages/whatsapp")
        print("   • Admin WhatsApp interface: /admin/messages/whatsapp")
    else:
        print("\n❌ Direct messaging test failed!")
        print("Please check the error messages above.")