from datetime import datetime

# Import db from app module
try:
    from app import db
except ImportError:
    # For initialization scripts
    db = None

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Assigned to
    assigned_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Admin who assigned
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='todo')  # todo, in_progress, completed, overdue
    priority = db.Column(db.String(10), default='medium')  # low, medium, high, urgent
    due_date = db.Column(db.DateTime)
    due_time = db.Column(db.Time, nullable=True)  # Specific time for the task
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    column_position = db.Column(db.Integer, default=0)  # For Trello-like drag and drop ordering
    
    def is_overdue(self):
        """Check if task is overdue"""
        if self.due_date and self.status != 'completed':
            return datetime.utcnow() > self.due_date
        return False
    
    def update_status(self, new_status):
        """Update task status and timestamps"""
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        if new_status == 'completed':
            self.completed_at = datetime.utcnow()
        
        db.session.commit()
    
    def get_days_until_due(self):
        """Get days until due date"""
        if self.due_date:
            delta = self.due_date - datetime.utcnow()
            return delta.days
        return None
    
    def __repr__(self):
        return f'<Task {self.title} - {self.status}>'
