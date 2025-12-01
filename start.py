#!/usr/bin/env python3
"""
Smart startup script with multiple modes
"""

import sys
import os

def show_menu():
    """Show startup options"""
    print("🚀 Remote Work Monitor - Startup Options")
    print("=" * 50)
    print("1. 🏃 Quick Start (No Face Recognition)")
    print("2. 🔒 Full Mode (With Face Recognition)")
    print("3. 🧪 Test System")
    print("4. 📊 System Status")
    print("5. ❌ Exit")
    print("=" * 50)

def quick_start():
    """Start in development mode without face recognition"""
    print("🏃 Starting Quick Mode...")
    print("⚡ Face recognition disabled for fast startup")
    
    try:
        from app_dev import create_dev_app
        app = create_dev_app()
        
        print("✅ Server ready at http://localhost:5000")
        print("👤 Login with: admin/admin123 or testuser/test123")
        
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

def full_mode():
    """Start with full face recognition"""
    print("🔒 Starting Full Mode...")
    print("🤖 Face recognition enabled (models will load on first use)")
    
    try:
        from app import create_app
        app = create_app()
        
        print("✅ Server ready at http://localhost:5000")
        print("📷 Face capture required for login/registration")
        
        app.run(debug=False, host='0.0.0.0', port=5000)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_system():
    """Run system tests"""
    print("🧪 Running System Tests...")
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, 'test_complete_system.py'], 
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
    except Exception as e:
        print(f"❌ Test error: {e}")

def system_status():
    """Show system status"""
    print("📊 System Status Check")
    print("-" * 30)
    
    # Check Python version
    print(f"🐍 Python: {sys.version.split()[0]}")
    
    # Check dependencies
    dependencies = [
        ('Flask', 'flask'),
        ('SQLAlchemy', 'sqlalchemy'),
        ('OpenCV', 'cv2'),
        ('Pillow', 'PIL'),
        ('DeepFace', 'deepface')
    ]
    
    for name, module in dependencies:
        try:
            __import__(module)
            print(f"✅ {name}: Available")
        except ImportError:
            print(f"❌ {name}: Missing")
    
    # Check database
    try:
        if os.path.exists('instance/app.db'):
            print("✅ Database: Found")
        else:
            print("⚠️  Database: Not found (will be created)")
    except Exception:
        print("❌ Database: Error checking")
    
    print("-" * 30)

def main():
    """Main menu loop"""
    while True:
        show_menu()
        
        try:
            choice = input("Choose an option (1-5): ").strip()
            
            if choice == '1':
                quick_start()
                break
            elif choice == '2':
                full_mode()
                break
            elif choice == '3':
                test_system()
                input("\nPress Enter to continue...")
            elif choice == '4':
                system_status()
                input("\nPress Enter to continue...")
            elif choice == '5':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please try again.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()