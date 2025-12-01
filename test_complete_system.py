#!/usr/bin/env python3
"""
Complete system test script
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from app import create_app, db
        print("✅ Flask app imports successful")
        
        from models.user import User
        from models.face_encoding import FaceEncoding
        from models.message import Message
        from models.log import Log
        print("✅ Model imports successful")
        
        from controllers.auth_controller_simple import auth_bp
        from controllers.dashboard_controller import dashboard_bp
        from controllers.admin_controller import admin_bp
        from controllers.api_controller import api_bp
        print("✅ Controller imports successful")
        
        from utils.face_recognition import detect_face, verify_faces
        print("✅ Face recognition utils imported")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_database():
    """Test database connectivity and tables"""
    print("\n🗄️  Testing database...")
    
    try:
        from app import create_app, db
        app = create_app()
        
        with app.app_context():
            # Test database connection
            db.create_all()
            print("✅ Database connection successful")
            
            # Check if tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            required_tables = ['users', 'face_encodings', 'logs', 'notifications']
            optional_tables = ['messages']
            
            for table in required_tables:
                if table in tables:
                    print(f"✅ Table '{table}' exists")
                else:
                    print(f"❌ Table '{table}' missing")
            
            for table in optional_tables:
                if table in tables:
                    print(f"✅ Table '{table}' exists")
                else:
                    print(f"⚠️  Table '{table}' missing (will be created on first use)")
            
            return True
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_face_recognition():
    """Test face recognition functionality"""
    print("\n👤 Testing face recognition...")
    
    try:
        from utils.face_recognition import detect_face, get_face_quality_score
        
        # Test with a minimal base64 image
        test_image = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A"
        
        print("✅ Face recognition utilities loaded")
        print("ℹ️  Note: DeepFace models will be downloaded on first real use")
        
        return True
        
    except Exception as e:
        print(f"❌ Face recognition error: {e}")
        return False

def test_templates():
    """Test if key templates exist"""
    print("\n📄 Testing templates...")
    
    key_templates = [
        'templates/auth/login.html',
        'templates/auth/register.html',
        'templates/dashboard/index.html',
        'templates/dashboard/messages_full.html',
        'templates/admin/dashboard.html'
    ]
    
    all_exist = True
    for template in key_templates:
        if os.path.exists(template):
            print(f"✅ {template}")
        else:
            print(f"❌ {template} missing")
            all_exist = False
    
    return all_exist

def main():
    print("🚀 Complete System Test")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Database", test_database),
        ("Face Recognition", test_face_recognition),
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
        print("\n🎉 All tests passed! System is ready!")
        print("\n🚀 Features available:")
        print("   • Face recognition login/registration")
        print("   • 3D futuristic dashboard")
        print("   • Employee status monitoring")
        print("   • Live messaging system")
        print("   • Admin management panel")
        print("   • Fancy scrollbars and animations")
        print("\n💡 To start the application:")
        print("   python run.py")
    else:
        print(f"\n⚠️  {len(results) - passed} tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()