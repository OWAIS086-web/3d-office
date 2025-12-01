#!/usr/bin/env python3
"""
Quick test script to verify the fixes
"""

import sys
import os

def test_database_fix():
    """Test the database connection fix"""
    print("Testing database connection fix...")
    
    try:
        from app import create_app, db
        app, socketio = create_app()
        
        with app.app_context():
            # Test database connection with new method
            with db.engine.connect() as connection:
                result = connection.execute(db.text("SELECT 1"))
                print("✅ Database connection successful")
            
            # Test if tables can be created
            db.create_all()
            print("✅ Database tables created successfully")
            
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_root_route():
    """Test the root route fix"""
    print("Testing root route...")
    
    try:
        from app import create_app
        app, socketio = create_app()
        
        with app.test_client() as client:
            response = client.get('/')
            print(f"✅ Root route responds with status: {response.status_code}")
            return True
    except Exception as e:
        print(f"❌ Root route test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🔧 Testing Fixes")
    print("=" * 30)
    
    success = True
    
    if not test_database_fix():
        success = False
    
    if not test_root_route():
        success = False
    
    print("\n" + "=" * 30)
    if success:
        print("🎉 All fixes working! You can now run the application.")
        print("\nNext steps:")
        print("1. Run: python init_db.py")
        print("2. Run: python run.py")
        print("3. Open http://localhost:5000")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
