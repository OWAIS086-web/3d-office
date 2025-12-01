import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration - Using SQLite for simplicity
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///remote_work_monitor.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Face recognition settings
    FACE_ENCODING_MODEL = 'hog'  # or 'cnn' for better accuracy but slower
    FACE_VERIFICATION_INTERVAL = 300  # 5 minutes in seconds
    FACE_TOLERANCE = 0.6  # Lower is more strict
    
    # File upload settings
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Monitoring settings
    INACTIVITY_THRESHOLD = 300  # 5 minutes of inactivity
    WORK_HOURS_START = 9  # 9 AM
    WORK_HOURS_END = 17  # 5 PM
    
    # Performance scoring weights
    TASK_COMPLETION_WEIGHT = 0.4
    ACTIVITY_WEIGHT = 0.3
    PUNCTUALITY_WEIGHT = 0.3
