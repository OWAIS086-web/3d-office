from datetime import datetime

# Import db from app module
try:
    from app import db
except ImportError:
    # For initialization scripts
    db = None

class FaceEncoding(db.Model):
    __tablename__ = 'face_encodings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    encoding = db.Column(db.JSON, nullable=False)  # Store face encoding as JSON (DeepFace embedding)
    model_name = db.Column(db.String(50), default='VGG-Face')  # DeepFace model used
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<FaceEncoding {self.id} for User {self.user_id} using {self.model_name}>'
