from app import db
from datetime import datetime

# Association table for group members
group_members = db.Table('group_members',
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)

class Group(db.Model):
    """Group model for group messaging"""
    __tablename__ = 'groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    group_type = db.Column(db.String(20), default='general', nullable=False)  # general, department, project
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_groups')
    members = db.relationship('User', secondary=group_members, backref='groups')
    
    def __repr__(self):
        return f'<Group {self.name}>'
    
    def to_dict(self):
        """Convert group to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_by': self.created_by,
            'creator_name': self.creator.username,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active,
            'group_type': self.group_type,
            'member_count': len(self.members),
            'members': [{'id': member.id, 'username': member.username} for member in self.members]
        }
    
    def add_member(self, user):
        """Add a user to the group"""
        if user not in self.members:
            self.members.append(user)
            return True
        return False
    
    def remove_member(self, user):
        """Remove a user from the group"""
        if user in self.members:
            self.members.remove(user)
            return True
        return False
    
    def is_member(self, user):
        """Check if user is a member of the group"""
        return user in self.members
    
    @staticmethod
    def get_user_groups(user_id):
        """Get all groups a user belongs to"""
        from models.user import User
        user = User.query.get(user_id)
        if user:
            return user.groups
        return []