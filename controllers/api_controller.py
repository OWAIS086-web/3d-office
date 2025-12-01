from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models.user import User
from models.message import Message
from models.face_encoding import FaceEncoding
from app import db
from datetime import datetime
import base64

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/users', methods=['GET'])
@login_required
def get_users():
    """Get list of users for messaging"""
    try:
        user_type = request.args.get('type', 'users')
        
        if user_type == 'admin':
            # Get admin users
            users = User.query.filter_by(is_admin=True).filter(User.id != current_user.id).all()
        else:
            # Get regular users
            users = User.query.filter_by(is_admin=False).filter(User.id != current_user.id).all()
        
        user_list = []
        for user in users:
            # Get face image if available
            face_encoding = FaceEncoding.query.filter_by(user_id=user.id).first()
            face_image = None
            if face_encoding and face_encoding.encoding:
                # Use the stored face image
                face_image = face_encoding.encoding
            
            # Get unread message count
            unread_count = Message.get_unread_count(user.id)
            
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'status': user.current_status or 'offline',
                'last_activity': user.last_activity.isoformat() if user.last_activity else None,
                'is_admin': user.is_admin,
                'face_image': face_image,
                'unread_count': unread_count
            }
            user_list.append(user_data)
        
        return jsonify({
            'success': True,
            'users': user_list
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@api_bp.route('/messages/<int:user_id>', methods=['GET'])
@login_required
def get_messages(user_id):
    """Get messages between current user and specified user"""
    try:
        # Check if target user exists
        target_user = User.query.get(user_id)
        if not target_user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Get messages between users
        messages_query = Message.get_conversation(current_user.id, user_id)
        messages = []
        
        for msg in reversed(messages_query):
            msg_dict = msg.to_dict()
            # Determine if message was sent by current user
            msg_dict['is_sent'] = (msg.sender_id == current_user.id)
            messages.append(msg_dict)
        
        # Mark messages as read
        Message.mark_conversation_read(current_user.id, user_id)
        
        return jsonify({
            'success': True,
            'messages': messages
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@api_bp.route('/messages/send', methods=['POST'])
@login_required
def send_message():
    """Send a message to another user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        recipient_id = data.get('recipient_id')
        content = data.get('content')
        
        if not recipient_id or not content:
            return jsonify({
                'success': False,
                'message': 'Recipient ID and content are required'
            }), 400
        
        # Check if recipient exists
        recipient = User.query.get(recipient_id)
        if not recipient:
            return jsonify({
                'success': False,
                'message': 'Recipient not found'
            }), 404
        
        # Create message
        message = Message(
            sender_id=current_user.id,
            recipient_id=recipient_id,
            content=content.strip(),
            message_type='text',
            chat_type='direct'
        )
        
        db.session.add(message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Message sent successfully',
            'message_data': {
                'id': message.id,
                'sender_id': message.sender_id,
                'sender_name': current_user.username,
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
                'is_sent': True
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@api_bp.route('/user/status', methods=['POST'])
@login_required
def update_user_status():
    """Update user status (online, break, offline)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        new_status = data.get('status')
        
        if new_status not in ['online', 'break', 'offline']:
            return jsonify({
                'success': False,
                'message': 'Invalid status'
            }), 400
        
        # Update user status
        current_user.current_status = new_status
        current_user.status = new_status
        current_user.last_activity = datetime.utcnow()
        
        if new_status == 'online':
            current_user.is_online = True
        elif new_status == 'offline':
            current_user.is_online = False
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Status updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@api_bp.route('/dashboard/stats', methods=['GET'])
@login_required
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        # Get user counts by status
        online_users = User.query.filter_by(current_status='online').count()
        break_users = User.query.filter_by(current_status='break').count()
        offline_users = User.query.filter_by(current_status='offline').count()
        total_users = User.query.count()
        
        # Get recent activity (placeholder)
        recent_logins = 0
        
        stats = {
            'online_users': online_users,
            'break_users': break_users,
            'offline_users': offline_users,
            'total_users': total_users,
            'recent_logins': recent_logins
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@api_bp.route('/user/face-image', methods=['GET'])
@login_required
def get_user_face_image():
    """Get current user's face image"""
    try:
        # Get user's face encoding
        face_encoding = FaceEncoding.query.filter_by(user_id=current_user.id).first()
        
        if face_encoding and face_encoding.encoding:
            return jsonify({
                'success': True,
                'face_image': face_encoding.encoding
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No face image found'
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@api_bp.route('/users/all', methods=['GET'])
@login_required
def get_all_users():
    """Get all users for dropdowns and selections"""
    try:
        users = User.query.filter(User.id != current_user.id).all()
        
        user_list = []
        for user in users:
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'status': user.current_status or 'offline',
                'is_admin': user.is_admin,
                'department': user.department or 'GENERAL',
                'last_activity': user.last_activity.isoformat() if user.last_activity else None,
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
            user_list.append(user_data)
        
        return jsonify({
            'success': True,
            'users': user_list
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@api_bp.route('/notifications/unread', methods=['GET'])
@login_required
def get_unread_notifications():
    """Get unread message count for current user"""
    try:
        # Get unread direct messages
        unread_direct = Message.query.filter_by(
            recipient_id=current_user.id,
            is_read=False,
            chat_type='direct'
        ).count()
        
        # Get unread group messages
        from models.group import Group
        user_groups = Group.get_user_groups(current_user.id)
        unread_group = 0
        
        for group in user_groups:
            group_unread = Message.query.filter(
                Message.group_id == group.id,
                Message.sender_id != current_user.id,
                Message.is_read == False,
                Message.chat_type == 'group'
            ).count()
            unread_group += group_unread
        
        return jsonify({
            'success': True,
            'unread_direct': unread_direct,
            'unread_group': unread_group,
            'total_unread': unread_direct + unread_group
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@api_bp.route('/conversations', methods=['GET'])
@login_required
def get_conversations():
    """Get all conversations for current user"""
    try:
        conversation_type = request.args.get('type', 'users')
        
        all_conversations = Message.get_user_conversations(current_user.id)
        
        # Filter by type
        conversations = []
        if conversation_type == 'users':
            conversations = [c for c in all_conversations if c.get('type') == 'direct']
        elif conversation_type == 'groups':
            conversations = [c for c in all_conversations if c.get('type') == 'group']
        else:
            conversations = all_conversations
        
        return jsonify({
            'success': True,
            'conversations': conversations
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@api_bp.route('/groups/create', methods=['POST'])
@login_required
def create_group():
    """Create a new group"""
    try:
        from models.group import Group
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        member_ids = data.get('member_ids', [])
        
        if not name:
            return jsonify({
                'success': False,
                'message': 'Group name is required'
            }), 400
        
        if not member_ids:
            return jsonify({
                'success': False,
                'message': 'At least one member is required'
            }), 400
        
        # Create group
        group = Group(
            name=name,
            description=description,
            created_by=current_user.id
        )
        
        db.session.add(group)
        db.session.flush()  # Get group ID
        
        # Add members
        members = User.query.filter(User.id.in_(member_ids)).all()
        
        for member in members:
            group.add_member(member)
        
        # Add creator as member
        group.add_member(current_user)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Group created successfully',
            'group': group.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@api_bp.route('/groups/<int:group_id>/messages', methods=['GET'])
@login_required
def get_group_messages(group_id):
    """Get messages for a group"""
    try:
        from models.group import Group
        
        # Check if user is member of group
        group = Group.query.get(group_id)
        if not group:
            return jsonify({
                'success': False,
                'message': 'Group not found'
            }), 404
        
        if not group.is_member(current_user):
            return jsonify({
                'success': False,
                'message': 'You are not a member of this group'
            }), 403
        
        # Get group messages
        messages_query = Message.get_group_messages(group_id)
        messages = [msg.to_dict() for msg in reversed(messages_query)]
        
        return jsonify({
            'success': True,
            'messages': messages
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@api_bp.route('/messages/<int:message_id>/delete', methods=['DELETE'])
@login_required
def delete_message(message_id):
    """Delete a specific message"""
    try:
        message = Message.query.get(message_id)
        
        if not message:
            return jsonify({
                'success': False,
                'message': 'Message not found'
            }), 404
        
        # Check if user can delete this message (sender or admin)
        if message.sender_id != current_user.id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'message': 'You can only delete your own messages'
            }), 403
        
        db.session.delete(message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Message deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to delete message: {str(e)}'
        }), 500

@api_bp.route('/conversations/<int:user_id>/delete', methods=['DELETE'])
@login_required
def delete_conversation(user_id):
    """Delete entire conversation with a user"""
    try:
        # Delete all messages between current user and target user
        messages = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.recipient_id == user_id)) |
            ((Message.sender_id == user_id) & (Message.recipient_id == current_user.id))
        ).all()
        
        for message in messages:
            db.session.delete(message)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Conversation deleted successfully ({len(messages)} messages removed)'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to delete conversation: {str(e)}'
        }), 500

@api_bp.route('/groups/<int:group_id>/delete', methods=['DELETE'])
@login_required
def delete_group(group_id):
    """Delete a group (only creator or admin can delete)"""
    try:
        from models.group import Group
        
        group = Group.query.get(group_id)
        
        if not group:
            return jsonify({
                'success': False,
                'message': 'Group not found'
            }), 404
        
        # Check if user can delete this group (creator or admin)
        if group.created_by != current_user.id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'message': 'Only group creator or admin can delete the group'
            }), 403
        
        # Delete all group messages first
        group_messages = Message.query.filter_by(group_id=group_id).all()
        for message in group_messages:
            db.session.delete(message)
        
        # Delete the group
        db.session.delete(group)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Group "{group.name}" deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to delete group: {str(e)}'
        }), 500

@api_bp.route('/groups/send', methods=['POST'])
@login_required
def send_group_message():
    """Send a message to a group"""
    try:
        from models.group import Group
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        group_id = data.get('group_id')
        content = data.get('content')
        
        if not group_id or not content:
            return jsonify({
                'success': False,
                'message': 'Group ID and content are required'
            }), 400
        
        # Check if group exists and user is member
        group = Group.query.get(group_id)
        
        if not group:
            return jsonify({
                'success': False,
                'message': 'Group not found'
            }), 404
        
        if not group.is_member(current_user):
            return jsonify({
                'success': False,
                'message': 'You are not a member of this group'
            }), 403
        
        # Send message
        message = Message.send_group_message(current_user.id, group_id, content.strip())
        
        return jsonify({
            'success': True,
            'message': 'Message sent successfully',
            'message_data': {
                'id': message.id,
                'sender_id': message.sender_id,
                'sender_name': current_user.username,
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
                'is_sent': True
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to send message: {str(e)}'
        }), 500