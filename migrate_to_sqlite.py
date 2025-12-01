#!/usr/bin/env python3
"""
Migration script to help transition from MySQL/PostgreSQL to SQLite
and from face_recognition to DeepFace
"""

import os
import sys
import shutil
from datetime import datetime

def backup_database():
    """Create a backup of the current database"""
    print("Creating database backup...")
    
    backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    # Backup SQLite database if it exists
    if os.path.exists('remote_work_monitor.db'):
        shutil.copy2('remote_work_monitor.db', f"{backup_dir}/remote_work_monitor.db")
        print(f"✅ SQLite database backed up to {backup_dir}/")
    
    # Backup any existing face encodings
    if os.path.exists('static/uploads/faces'):
        shutil.copytree('static/uploads/faces', f"{backup_dir}/faces", dirs_exist_ok=True)
        print(f"✅ Face images backed up to {backup_dir}/faces/")
    
    print(f"✅ Backup created in {backup_dir}/")
    return backup_dir

def update_requirements():
    """Update requirements.txt to remove old dependencies"""
    print("Updating requirements.txt...")
    
    # Read current requirements
    with open('requirements.txt', 'r') as f:
        lines = f.readlines()
    
    # Remove problematic dependencies
    new_lines = []
    removed_deps = []
    
    for line in lines:
        line = line.strip()
        if line in ['face-recognition', 'dlib', 'mysql-connector-python', 'psycopg2-binary']:
            removed_deps.append(line)
        else:
            new_lines.append(line)
    
    # Write updated requirements
    with open('requirements.txt', 'w') as f:
        for line in new_lines:
            f.write(line + '\n')
    
    print(f"✅ Removed dependencies: {', '.join(removed_deps)}")
    print("✅ Updated requirements.txt")

def create_env_file():
    """Create .env file with SQLite configuration"""
    print("Creating .env file...")
    
    if os.path.exists('.env'):
        print("⚠️  .env file already exists, creating backup...")
        shutil.copy2('.env', '.env.backup')
    
    with open('.env', 'w') as f:
        f.write("""# Remote Work Monitor Configuration
SECRET_KEY=dev-secret-key-change-in-production
FLASK_ENV=development
FLASK_DEBUG=True

# Database Configuration - Using SQLite
DATABASE_URL=sqlite:///remote_work_monitor.db

# Face Recognition Settings
FACE_ENCODING_MODEL=VGG-Face
FACE_VERIFICATION_INTERVAL=300
FACE_TOLERANCE=0.6

# File Upload Settings
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=16777216

# Monitoring Settings
INACTIVITY_THRESHOLD=300
WORK_HOURS_START=9
WORK_HOURS_END=17

# Performance Scoring Weights
TASK_COMPLETION_WEIGHT=0.4
ACTIVITY_WEIGHT=0.3
PUNCTUALITY_WEIGHT=0.3
""")
    
    print("✅ Created .env file with SQLite configuration")

def create_directories():
    """Create necessary directories"""
    print("Creating directories...")
    
    directories = [
        'static/uploads',
        'static/uploads/faces',
        'logs',
        'utils'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created: {directory}")

def main():
    """Main migration function"""
    print("🔄 Migrating to SQLite + DeepFace Setup")
    print("=" * 50)
    
    try:
        # Create backup
        backup_dir = backup_database()
        
        # Update requirements
        update_requirements()
        
        # Create .env file
        create_env_file()
        
        # Create directories
        create_directories()
        
        print("\n" + "=" * 50)
        print("🎉 Migration completed successfully!")
        print("\nNext steps:")
        print("1. Install updated dependencies:")
        print("   pip install -r requirements.txt")
        print("2. Initialize the database:")
        print("   python init_db.py")
        print("3. Test the setup:")
        print("   python test_setup.py")
        print("4. Run the application:")
        print("   python run.py")
        print(f"\n📁 Backup created in: {backup_dir}/")
        print("💡 You can restore from backup if needed")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("Please check the error and try again")
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
