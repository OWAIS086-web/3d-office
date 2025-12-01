"""
Development configuration with face recognition disabled for faster startup
"""

import os
from config import Config

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
    # Disable face recognition for faster development
    FACE_RECOGNITION_ENABLED = False
    
    # Use in-memory SQLite for faster testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Reduce session timeout for development
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # Enable detailed error messages
    PROPAGATE_EXCEPTIONS = True
    
    # Disable CSRF for API testing (enable in production)
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Production configuration with full security"""
    DEBUG = False
    TESTING = False
    
    # Enable face recognition in production
    FACE_RECOGNITION_ENABLED = True
    
    # Use persistent database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    
    # Enable all security features
    WTF_CSRF_ENABLED = True