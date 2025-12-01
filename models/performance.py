from datetime import datetime, date

# Import db from app module
try:
    from app import db
except ImportError:
    # For initialization scripts
    db = None

class Performance(db.Model):
    __tablename__ = 'performance'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, default=date.today)
    task_completion_score = db.Column(db.Float, default=0.0)  # 0-100
    activity_score = db.Column(db.Float, default=0.0)  # 0-100
    punctuality_score = db.Column(db.Float, default=0.0)  # 0-100
    overall_score = db.Column(db.Float, default=0.0)  # 0-100
    total_work_hours = db.Column(db.Float, default=0.0)
    tasks_completed = db.Column(db.Integer, default=0)
    tasks_overdue = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def calculate_overall_score(self):
        """Calculate overall performance score"""
        from config import Config
        
        self.overall_score = (
            self.task_completion_score * Config.TASK_COMPLETION_WEIGHT +
            self.activity_score * Config.ACTIVITY_WEIGHT +
            self.punctuality_score * Config.PUNCTUALITY_WEIGHT
        )
        return self.overall_score
    
    def update_scores(self, task_score=None, activity_score=None, punctuality_score=None):
        """Update individual scores and recalculate overall"""
        if task_score is not None:
            self.task_completion_score = task_score
        if activity_score is not None:
            self.activity_score = activity_score
        if punctuality_score is not None:
            self.punctuality_score = punctuality_score
        
        self.calculate_overall_score()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def get_performance_grade(self):
        """Get performance grade based on overall score"""
        if self.overall_score >= 90:
            return 'A'
        elif self.overall_score >= 80:
            return 'B'
        elif self.overall_score >= 70:
            return 'C'
        elif self.overall_score >= 60:
            return 'D'
        else:
            return 'F'
    
    @staticmethod
    def get_user_performance_for_period(user_id, start_date, end_date):
        """Get performance data for a user over a date range"""
        return Performance.query.filter(
            Performance.user_id == user_id,
            Performance.date >= start_date,
            Performance.date <= end_date
        ).order_by(Performance.date.desc()).all()
    
    def __repr__(self):
        return f'<Performance User {self.user_id} - {self.date} - Score: {self.overall_score}>'
