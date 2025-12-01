from datetime import datetime

# Import db from app module
try:
    from app import db
except ImportError:
    # For initialization scripts
    db = None

class Log(db.Model):
    __tablename__ = 'logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # login, logout, face_verification, inactivity_alert
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    details = db.Column(db.JSON)  # Additional details as JSON
    
    def __repr__(self):
        return f'<Log {self.action} for User {self.user_id} at {self.timestamp}>'
