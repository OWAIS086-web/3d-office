#!/usr/bin/env python3
"""
Migration script to add groups and update messages table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models.group import Group
from models.message import Message

def migrate_groups():
    """Add groups table and update messages table"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create all tables (including groups and updated messages)
            db.create_all()
            print("✅ Groups and updated messages tables created successfully!")
            
            # Verify tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            required_tables = ['groups', 'group_members', 'messages']
            
            for table in required_tables:
                if table in tables:
                    print(f"✅ Table '{table}' verified in database")
                    
                    # Show table structure
                    columns = inspector.get_columns(table)
                    print(f"   📋 {table} columns:")
                    for col in columns:
                        print(f"      - {col['name']}: {col['type']}")
                    print()
                else:
                    print(f"❌ Table '{table}' not found in database")
            
            # Create some demo groups
            create_demo_groups()
            
        except Exception as e:
            print(f"❌ Error creating groups tables: {e}")
            return False
    
    return True

def create_demo_groups():
    """Create some demo groups for testing"""
    try:
        from models.user import User
        
        # Check if we have users
        users = User.query.all()
        if len(users) < 2:
            print("⚠️  Not enough users to create demo groups")
            return
        
        # Create demo groups
        demo_groups = [
            {
                'name': 'Development Team',
                'description': 'Main development team discussions',
                'members': users[:3] if len(users) >= 3 else users
            },
            {
                'name': 'General Discussion',
                'description': 'General company discussions',
                'members': users
            }
        ]
        
        for group_data in demo_groups:
            # Check if group already exists
            existing_group = Group.query.filter_by(name=group_data['name']).first()
            if existing_group:
                print(f"⚠️  Group '{group_data['name']}' already exists")
                continue
            
            # Create group
            group = Group(
                name=group_data['name'],
                description=group_data['description'],
                created_by=users[0].id  # First user creates the group
            )
            
            db.session.add(group)
            db.session.flush()  # Get group ID
            
            # Add members
            for member in group_data['members']:
                group.add_member(member)
            
            db.session.commit()
            print(f"✅ Created demo group: {group_data['name']} with {len(group_data['members'])} members")
        
    except Exception as e:
        print(f"⚠️  Error creating demo groups: {e}")

if __name__ == "__main__":
    print("🚀 Adding Groups and Enhanced Messaging")
    print("=" * 50)
    
    success = migrate_groups()
    
    if success:
        print("\n✅ Groups migration completed successfully!")
        print("\n🎉 Enhanced messaging features now available:")
        print("   • Individual user messaging")
        print("   • Group messaging and creation")
        print("   • User dropdown selection")
        print("   • Real-time conversation updates")
        print("   • Group member management")
        print("\n🌐 Access enhanced messaging at:")
        print("   http://localhost:5000/dashboard/messages/enhanced")
    else:
        print("\n❌ Groups migration failed!")
        print("Please check the error messages above.")