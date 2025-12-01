from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

# Import db from app module
try:
    from app import db
except ImportError:
    db = None

# Import FaceEncoding for the method
try:
    from models.face_encoding import FaceEncoding
except ImportError:
    FaceEncoding = None

# Import Log for the method
try:
    from models.log import Log
except ImportError:
    Log = None


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow,nullable=False)
    last_login = db.Column(db.DateTime)
    last_activity = db.Column(db.DateTime)
    current_status = db.Column(db.String(20), default='offline')  # offline, working, break, absent
    break_start_time = db.Column(db.DateTime)
    break_duration = db.Column(db.Integer)  # Break duration in minutes
    break_reason = db.Column(db.String(200))  # Reason for break
    status = db.Column(db.String(20), default='offline')  # Current status
    is_online = db.Column(db.Boolean, default=False)  # Online status
    department = db.Column(db.String(50), default='GENERAL')  # User's department
    
    # Relationships
    face_encodings = db.relationship('FaceEncoding', backref='user', lazy=True, cascade='all, delete-orphan')
    logs = db.relationship('Log', backref='user', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        if password:
            self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        return False
    
    def get_face_encodings(self):
        """Get all face encodings for this user"""
        if hasattr(self, 'face_encodings') and self.face_encodings:
            return [encoding.encoding for encoding in self.face_encodings if encoding.is_active]
        return []
    
    def add_face_encoding(self, encoding, model_name='VGG-Face'):
        """Add a new face encoding using DeepFace"""
        if db is not None and FaceEncoding is not None:  # Check if db and FaceEncoding are available
            face_encoding = FaceEncoding(
                user_id=self.id, 
                encoding=encoding.tolist() if hasattr(encoding, 'tolist') else encoding,
                model_name=model_name
            )
            db.session.add(face_encoding)
            db.session.commit()
    
    def update_activity(self):
        """Update last activity timestamp"""
        if db is not None:
            self.last_activity = datetime.utcnow()
            db.session.commit()
    
    def get_online_duration_today(self):
        """Calculate total online duration for today"""
        if db is None:
            return 0.0
            
        try:
            from models.log import Log
            today = datetime.utcnow().date()
            today_logs = Log.query.filter(
                Log.user_id == self.id,
                db.func.date(Log.timestamp) == today,
                Log.action.in_(['login', 'logout'])
            ).order_by(Log.timestamp).all()
            
            total_hours = 0
            login_time = None
            
            for log in today_logs:
                if log.action == 'login':
                    login_time = log.timestamp
                elif log.action == 'logout' and login_time:
                    total_hours += (log.timestamp - login_time).total_seconds() / 3600
                    login_time = None
            
            # If user is still logged in
            if login_time:
                total_hours += (datetime.utcnow() - login_time).total_seconds() / 3600
            
            return round(total_hours, 2)
        except ImportError:
            return 0.0

    @property
    def is_online(self):
        """Check if user is online (active in last 5 minutes)"""
        if self.last_activity:
            return datetime.utcnow() - self.last_activity < timedelta(minutes=5)
        return False
    
    @is_online.setter
    def is_online(self, value):
        """Set online status by updating last_activity"""
        if value:
            self.last_activity = datetime.utcnow()
        # Note: We don't set it to None when False to preserve last activity time
        return False
    
    def set_status(self, status):
        """Set user status (online, break, offline)"""
        if db is not None:
            self.current_status = status
            if status == 'break':
                self.break_start_time = datetime.utcnow()
            elif status == 'online':
                self.break_start_time = None
            db.session.commit()
    
    def get_current_status(self):
        """Get current user status with intelligent detection"""
        if not self.is_online:
            return 'offline'
        
        # If manually set to break
        if self.current_status == 'break':
            return 'break'
        
        # Auto-detect break (inactive for 15+ minutes but still online)
        if self.last_activity and datetime.utcnow() - self.last_activity > timedelta(minutes=15):
            return 'break'
        
        # Default to online if online and active
        return 'online'
    
    def __repr__(self):
        return f'<User {self.username}>'
