from app import db
from datetime import datetime

class Message(db.Model):
    """Message model for user-to-user and group messaging"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Null for group messages
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=True)  # For group messages
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    message_type = db.Column(db.String(20), default='text', nullable=False)  # text, image, file
    chat_type = db.Column(db.String(20), default='direct', nullable=False)  # direct, group
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')
    group = db.relationship('Group', backref='messages')
    
    def __repr__(self):
        if self.chat_type == 'group':
            return f'<Message {self.id}: {self.sender.username} -> Group {self.group_id}>'
        else:
            recipient_name = self.recipient.username if self.recipient else 'Unknown'
            return f'<Message {self.id}: {self.sender.username} -> {recipient_name}>'
    
    def to_dict(self):
        """Convert message to dictionary"""
        data = {
            'id': self.id,
            'sender_id': self.sender_id,
            'sender_name': self.sender.username,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'is_read': self.is_read,
            'message_type': self.message_type,
            'chat_type': self.chat_type
        }
        
        if self.chat_type == 'direct':
            data['recipient_id'] = self.recipient_id
            data['recipient_name'] = self.recipient.username if self.recipient else None
        elif self.chat_type == 'group':
            data['group_id'] = self.group_id
            data['group_name'] = self.group.name if self.group else None
        
        return data
    
    @staticmethod
    def get_conversation(user1_id, user2_id, limit=50):
        """Get conversation between two users"""
        return Message.query.filter(
            ((Message.sender_id == user1_id) & (Message.recipient_id == user2_id)) |
            ((Message.sender_id == user2_id) & (Message.recipient_id == user1_id))
        ).filter(Message.chat_type == 'direct').order_by(Message.timestamp.asc()).limit(limit).all()
    
    @staticmethod
    def get_unread_count(user_id):
        """Get count of unread messages for a user"""
        return Message.query.filter_by(recipient_id=user_id, is_read=False).count()
    
    @staticmethod
    def mark_conversation_read(user1_id, user2_id):
        """Mark all messages in a conversation as read"""
        Message.query.filter(
            (Message.sender_id == user2_id) & 
            (Message.recipient_id == user1_id) & 
            (Message.is_read == False)
        ).update({'is_read': True})
        db.session.commit()
    
    @staticmethod
    def get_group_messages(group_id, limit=50):
        """Get messages for a group"""
        return Message.query.filter_by(
            group_id=group_id, 
            chat_type='group'
        ).order_by(Message.timestamp.desc()).limit(limit).all()
    
    @staticmethod
    def send_group_message(sender_id, group_id, content):
        """Send a message to a group"""
        message = Message(
            sender_id=sender_id,
            group_id=group_id,
            content=content,
            chat_type='group',
            message_type='text'
        )
        db.session.add(message)
        db.session.commit()
        return message
    
    @staticmethod
    def get_user_conversations(user_id):
        """Get all conversations (direct and group) for a user"""
        conversations = []
        
        try:
            from models.user import User
            
            # Get direct conversations - find all users who have exchanged messages with current user
            direct_messages = db.session.query(Message).filter(
                ((Message.sender_id == user_id) | (Message.recipient_id == user_id)) &
                (Message.chat_type == 'direct')
            ).order_by(Message.timestamp.desc()).all()
            
            # Process direct conversations
            processed_users = set()
            for msg in direct_messages:
                other_user_id = msg.recipient_id if msg.sender_id == user_id else msg.sender_id
                if other_user_id and other_user_id not in processed_users:
                    processed_users.add(other_user_id)
                    other_user = User.query.get(other_user_id)
                    if other_user:
                        # Get unread count
                        unread_count = Message.query.filter(
                            (Message.sender_id == other_user_id) & 
                            (Message.recipient_id == user_id) & 
                            (Message.is_read == False) &
                            (Message.chat_type == 'direct')
                        ).count()
                        
                        conversations.append({
                            'type': 'direct',
                            'id': other_user_id,
                            'name': other_user.username,
                            'last_message': msg.content,
                            'timestamp': msg.timestamp,
                            'unread_count': unread_count
                        })
        except Exception as e:
            print(f"Error loading direct conversations: {e}")
        
        # Process group conversations
        try:
            from models.group import Group, group_members
            
            # Get groups where user is a member using the association table
            user_groups = db.session.query(Group).join(group_members).filter(
                group_members.c.user_id == user_id
            ).all()
            
            for group in user_groups:
                try:
                    last_message = Message.query.filter_by(
                        group_id=group.id, 
                        chat_type='group'
                    ).order_by(Message.timestamp.desc()).first()
                    
                    # Get member count safely
                    member_count = db.session.query(group_members).filter(
                        group_members.c.group_id == group.id
                    ).count()
                    
                    conversations.append({
                        'type': 'group',
                        'id': group.id,
                        'name': group.name,
                        'last_message': last_message.content if last_message else 'No messages yet',
                        'timestamp': last_message.timestamp if last_message else group.created_at,
                        'member_count': member_count,
                        'unread_count': 0  # TODO: Implement group unread count
                    })
                except Exception as group_error:
                    print(f"Error processing group {group.id}: {group_error}")
                    continue
                    
        except Exception as e:
            print(f"Error loading group conversations: {e}")
        
        # Sort by timestamp
        try:
            conversations.sort(key=lambda x: x['timestamp'], reverse=True)
        except Exception as e:
            print(f"Error sorting conversations: {e}")
        
        return conversations