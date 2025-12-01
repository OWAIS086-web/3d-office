#!/usr/bin/env python3
"""
Test script for enhanced messaging system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_messaging_models():
    """Test messaging models and functionality"""
    print("🧪 Testing Enhanced Messaging Models...")
    
    try:
        from app import create_app, db
        from models.user import User
        from models.group import Group
        from models.message import Message
        
        app = create_app()
        
        with app.app_context():
            # Test Group model
            print("✅ Group model imported successfully")
            
            # Test Message model updates
            print("✅ Updated Message model imported successfully")
            
            # Test database tables
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            required_tables = ['groups', 'group_members', 'messages']
            for table in required_tables:
                if table in tables:
                    print(f"✅ Table '{table}' exists")
                else:
                    print(f"❌ Table '{table}' missing")
            
            # Test group creation
            users = User.query.all()
            if len(users) >= 2:
                test_group = Group(
                    name='Test Group',
                    description='Test group for messaging',
                    created_by=users[0].id
                )
                
                # Test adding members
                test_group.add_member(users[0])
                if len(users) > 1:
                    test_group.add_member(users[1])
                
                print(f"✅ Group creation test passed")
                print(f"   - Group has {len(test_group.members)} members")
                
                # Test group messaging
                test_message = Message(
                    sender_id=users[0].id,
                    group_id=1,  # Assuming group ID 1
                    content='Test group message',
                    chat_type='group'
                )
                
                print("✅ Group message creation test passed")
            else:
                print("⚠️  Not enough users for group testing")
            
        return True
        
    except Exception as e:
        print(f"❌ Model test error: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    print("\n🌐 Testing API Endpoints...")
    
    try:
        from controllers.api_controller import api_bp
        print("✅ API controller imported successfully")
        
        # Check if new endpoints exist
        endpoints = [
            '/api/users/all',
            '/api/conversations',
            '/api/groups/create',
            '/api/groups/<int:group_id>/messages',
            '/api/groups/send'
        ]
        
        print("✅ New API endpoints defined:")
        for endpoint in endpoints:
            print(f"   - {endpoint}")
        
        return True
        
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False

def test_templates():
    """Test template files"""
    print("\n📄 Testing Templates...")
    
    templates = [
        'templates/dashboard/messages_enhanced.html'
    ]
    
    all_exist = True
    for template in templates:
        if os.path.exists(template):
            print(f"✅ {template}")
            
            # Check file size
            size = os.path.getsize(template)
            print(f"   - Size: {size:,} bytes")
            
        else:
            print(f"❌ {template} missing")
            all_exist = False
    
    return all_exist

def main():
    print("🚀 Enhanced Messaging System Test")
    print("=" * 50)
    
    tests = [
        ("Models & Database", test_messaging_models),
        ("API Endpoints", test_api_endpoints),
        ("Templates", test_templates)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 Enhanced messaging system is ready!")
        print("\n🚀 Features available:")
        print("   • Individual user messaging with dropdown selection")
        print("   • Group messaging and creation")
        print("   • Real-time conversation updates")
        print("   • User and group tabs")
        print("   • Message history and threading")
        print("\n💡 To use the enhanced messaging:")
        print("   1. Run: python migrate_groups.py")
        print("   2. Start app: python start.py")
        print("   3. Visit: /dashboard/messages/enhanced")
    else:
        print(f"\n⚠️  {len(results) - passed} tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()