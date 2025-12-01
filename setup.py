#!/usr/bin/env python3
"""
Setup script for Remote Work Monitor
This script helps set up the application for first-time use
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    print("\n📦 Checking dependencies...")
    
    required_packages = [
        'flask', 'flask-sqlalchemy', 'flask-migrate', 'flask-socketio',
        'flask-login', 'flask-wtf', 'opencv-python', 'deepface',
        'pillow', 'numpy', 'python-socketio', 'eventlet', 'python-dotenv',
        'bcrypt', 'email-validator', 'tensorflow'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    return True

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        'static/uploads',
        'static/uploads/faces',
        'logs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {directory}")

def create_env_file():
    """Create .env file from template"""
    print("\n⚙️  Setting up environment configuration...")
    
    if os.path.exists('.env'):
        print("✅ .env file already exists")
        return
    
    if os.path.exists('env_example.txt'):
        shutil.copy('env_example.txt', '.env')
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file with your database credentials")
    else:
        print("❌ env_example.txt not found")

def run_database_init():
    """Initialize the database"""
    print("\n🗄️  Initializing database...")
    
    try:
        result = subprocess.run([sys.executable, 'init_db.py'], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Database initialized successfully")
            return True
        else:
            print(f"❌ Database initialization failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Database initialization timed out")
        return False
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Remote Work Monitor Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        print("\n💡 Install missing dependencies with:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Create environment file
    create_env_file()
    
    # Ask about database initialization
    print("\n" + "=" * 50)
    print("📋 Setup Summary:")
    print("✅ Python version check passed")
    print("✅ Dependencies check passed")
    print("✅ Directories created")
    print("✅ Environment file created")
    
    print("\n🔧 Next Steps:")
    print("1. Edit .env file with your database credentials")
    print("2. Run: python init_db.py (to initialize database)")
    print("3. Run: python run.py (to start the application)")
    print("4. Open http://localhost:5000 in your browser")
    print("5. Login with admin/admin123 (change password immediately)")
    
    print("\n📚 For detailed instructions, see README.md")
    print("=" * 50)

if __name__ == '__main__':
    main()
