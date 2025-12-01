#!/usr/bin/env python3
"""
Test script to verify the application setup with SQLite and DeepFace
"""

import sys
import os
import numpy as np

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import flask
        print("✅ Flask imported successfully")
    except ImportError as e:
        print(f"❌ Flask import failed: {e}")
        return False
    
    try:
        import deepface
        print("✅ DeepFace imported successfully")
    except ImportError as e:
        print(f"❌ DeepFace import failed: {e}")
        return False
    
    try:
        import cv2
        print("✅ OpenCV imported successfully")
    except ImportError as e:
        print(f"❌ OpenCV import failed: {e}")
        return False
    
    try:
        import numpy
        print("✅ NumPy imported successfully")
    except ImportError as e:
        print(f"❌ NumPy import failed: {e}")
        return False
    
    try:
        import PIL
        print("✅ Pillow imported successfully")
    except ImportError as e:
        print(f"❌ Pillow import failed: {e}")
        return False
    
    return True

def test_deepface():
    """Test DeepFace functionality"""
    print("\nTesting DeepFace functionality...")
    
    try:
        from deepface import DeepFace
        print("✅ DeepFace module imported successfully")
        
        # Test if we can get available models
        models = DeepFace.build_model("VGG-Face")
        print("✅ DeepFace VGG-Face model loaded successfully")
        
        return True
    except Exception as e:
        print(f"❌ DeepFace test failed: {e}")
        return False

def test_database():
    """Test database connection"""
    print("\nTesting database connection...")
    
    try:
        from app import create_app, db
        app, socketio = create_app()
        
        with app.app_context():
            # Test database connection
            with db.engine.connect() as connection:
                connection.execute(db.text("SELECT 1"))
            print("✅ Database connection successful")
            
            # Test if tables can be created
            db.create_all()
            print("✅ Database tables created successfully")
            
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_face_recognition_utils():
    """Test our face recognition utility"""
    print("\nTesting face recognition utility...")
    
    try:
        from utils.face_recognition import face_recognition
        print("✅ Face recognition utility imported successfully")
        
        # Test with a random image array
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # Test face detection
        faces = face_recognition.detect_faces(test_image)
        print(f"✅ Face detection test completed (found {len(faces)} faces)")
        
        # Test encoding extraction (this might fail with random data, but should not crash)
        try:
            encoding = face_recognition.extract_face_encoding(test_image)
            if encoding is not None:
                print("✅ Face encoding extraction test completed")
            else:
                print("⚠️  Face encoding extraction returned None (expected with random data)")
        except Exception as e:
            print(f"⚠️  Face encoding extraction failed (expected with random data): {e}")
        
        return True
    except Exception as e:
        print(f"❌ Face recognition utility test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Remote Work Monitor Setup")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Test imports
    if not test_imports():
        all_tests_passed = False
    
    # Test DeepFace
    if not test_deepface():
        all_tests_passed = False
    
    # Test database
    if not test_database():
        all_tests_passed = False
    
    # Test face recognition utility
    if not test_face_recognition_utils():
        all_tests_passed = False
    
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("🎉 All tests passed! The application is ready to run.")
        print("\nNext steps:")
        print("1. Run: python init_db.py")
        print("2. Run: python run.py")
        print("3. Open http://localhost:5000")
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        print("\nCommon solutions:")
        print("- Install missing dependencies: pip install -r requirements.txt")
        print("- Check Python version (3.8+ required)")
        print("- Ensure all files are in the correct directory")
    
    return all_tests_passed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
