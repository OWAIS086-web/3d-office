#!/usr/bin/env python3
"""
Database initialization script for Remote Work Monitor
Run this script to create the database and initial admin user
"""

import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models.user import User
from models.face_encoding import FaceEncoding
from utils.face_recognition import face_recognition
import numpy as np

def create_admin_user():
    """Create an admin user for initial setup"""
    print("Creating admin user...")
    
    # Check if admin user already exists
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print("Admin user already exists!")
        return admin
    
    # Create admin user
    admin = User(
        username='admin',
        email='admin@example.com',
        is_admin=True,
        is_active=True
    )
    admin.set_password('admin123')  # Change this in production!
    
    db.session.add(admin)
    db.session.commit()
    
    print("Admin user created successfully!")
    print("Username: admin")
    print("Password: admin123")
    print("Email: admin@example.com")
    print("\nIMPORTANT: Change the admin password after first login!")
    
    return admin

def create_sample_users():
    """Create sample users for testing"""
    print("Creating sample users...")
    
    sample_users = [
        {
            'username': 'john_doe',
            'email': 'john@example.com',
            'password': 'password123'
        },
        {
            'username': 'jane_smith',
            'email': 'jane@example.com',
            'password': 'password123'
        },
        {
            'username': 'bob_wilson',
            'email': 'bob@example.com',
            'password': 'password123'
        }
    ]
    
    for user_data in sample_users:
        # Check if user already exists
        existing_user = User.query.filter_by(username=user_data['username']).first()
        if existing_user:
            print(f"User {user_data['username']} already exists, skipping...")
            continue
        
        user = User(
            username=user_data['username'],
            email=user_data['email'],
            is_admin=False,
            is_active=True
        )
        user.set_password(user_data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        print(f"Created user: {user_data['username']}")
    
    print("Sample users created successfully!")

def create_sample_face_encodings():
    """Create sample face encodings for testing using DeepFace"""
    print("Creating sample face encodings...")
    
    # Generate random face encodings for testing
    # In a real application, these would be actual face encodings from photos
    users = User.query.filter_by(is_admin=False).all()
    
    for user in users:
        # Check if user already has face encodings
        if user.face_encodings:
            print(f"User {user.username} already has face encodings, skipping...")
            continue
        
        # Generate a random face encoding (4096 features for VGG-Face)
        # In production, this would be from actual DeepFace recognition
        random_encoding = np.random.rand(4096).tolist()
        
        face_encoding = FaceEncoding(
            user_id=user.id,
            encoding=random_encoding,
            model_name='VGG-Face'
        )
        
        db.session.add(face_encoding)
        db.session.commit()
        
        print(f"Created face encoding for user: {user.username}")
    
    print("Sample face encodings created successfully!")

def main():
    """Main initialization function"""
    print("Initializing Remote Work Monitor Database...")
    print("=" * 50)
    
    # Create Flask app
    app, socketio = create_app()
    
    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")
        
        # Create admin user
        admin = create_admin_user()
        
        # Create sample users
        create_sample_users()
        
        # Create sample face encodings
        create_sample_face_encodings()
        
        print("\n" + "=" * 50)
        print("Database initialization completed successfully!")
        print("\nNext steps:")
        print("1. Start the application: python app.py")
        print("2. Open your browser and go to: http://localhost:5000")
        print("3. Login with admin credentials")
        print("4. Change the admin password")
        print("5. Register new users with face photos")
        print("\nFor production deployment:")
        print("- Change the SECRET_KEY in config.py")
        print("- Use a proper database (MySQL/PostgreSQL)")
        print("- Set up proper environment variables")
        print("- Configure HTTPS")

if __name__ == '__main__':
    main()
