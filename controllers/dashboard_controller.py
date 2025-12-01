from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models.notification import Notification
from models.log import Log
from models.user import User
from app import db
from datetime import datetime, date, timedelta
import json

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard for users"""
    # Get recent notifications
    notifications = Notification.query.filter(
        (Notification.user_id == current_user.id) | (Notification.user_id.is_(None))
    ).order_by(Notification.created_at.desc()).limit(10).all()
    
    # Get online duration for today
    online_duration = current_user.get_online_duration_today()
    
    # Get recent activity logs
    recent_logs = Log.query.filter_by(user_id=current_user.id)\
        .order_by(Log.timestamp.desc()).limit(10).all()
    
    # Get user status
    user_status = current_user.get_current_status()
    
    return render_template('dashboard/index.html',
                         notifications=notifications,
                         online_duration=online_duration,
                         recent_logs=recent_logs,
                         user_status=user_status)

@dashboard_bp.route('/notifications')
@login_required
def notifications():
    """Notifications page"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    notifications = Notification.query.filter(
        (Notification.user_id == current_user.id) | (Notification.user_id.is_(None))
    ).order_by(Notification.created_at.desc())\
    .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('dashboard/notifications.html', notifications=notifications)

@dashboard_bp.route('/mark_notification_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    try:
        notification = Notification.query.get_or_404(notification_id)
        
        if notification.user_id == current_user.id or notification.user_id is None:
            notification.mark_as_read()
            return jsonify({'success': True})
        
        return jsonify({'success': False, 'message': 'Unauthorized'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@dashboard_bp.route('/get_activity_data')
@login_required
def get_activity_data():
    """Get activity data for charts"""
    days = request.args.get('days', 7, type=int)
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    # Get daily work hours
    logs = Log.query.filter(
        Log.user_id == current_user.id,
        Log.action.in_(['login', 'logout']),
        Log.timestamp >= start_date
    ).order_by(Log.timestamp).all()
    
    # Calculate daily work hours
    daily_hours = {}
    login_time = None
    
    for log in logs:
        log_date = log.timestamp.date()
        if log_date not in daily_hours:
            daily_hours[log_date] = 0
        
        if log.action == 'login':
            login_time = log.timestamp
        elif log.action == 'logout' and login_time:
            hours = (log.timestamp - login_time).total_seconds() / 3600
            daily_hours[log_date] += hours
            login_time = None
    
    # If still logged in today
    if login_time and login_time.date() == date.today():
        hours = (datetime.utcnow() - login_time).total_seconds() / 3600
        daily_hours[date.today()] = daily_hours.get(date.today(), 0) + hours
    
    # Format data for chart
    chart_data = []
    for i in range(days):
        chart_date = end_date - timedelta(days=i)
        chart_data.append({
            'date': chart_date.strftime('%Y-%m-%d'),
            'hours': round(daily_hours.get(chart_date, 0), 2)
        })
    
    chart_data.reverse()
    
    return jsonify(chart_data)

@dashboard_bp.route('/settings')
@login_required
def settings():
    """User settings page"""
    return render_template('dashboard/settings.html')

@dashboard_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    # Get activity data for the last 30 days
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    # Get recent activity logs
    recent_logs = Log.query.filter(
        Log.user_id == current_user.id,
        Log.timestamp >= start_date
    ).order_by(Log.timestamp.desc()).limit(50).all()
    
    return render_template('dashboard/profile.html', recent_logs=recent_logs)

@dashboard_bp.route('/notifications')
@login_required
def user_notifications():
    """User notifications page"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    notifications = Notification.query.filter(
        (Notification.user_id == current_user.id) | (Notification.user_id.is_(None))
    ).order_by(Notification.created_at.desc())\
    .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('dashboard/notifications.html', 
                         notifications=notifications,
                         pagination=notifications)

@dashboard_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile"""
    email = request.form.get('email')
    
    if email:
        current_user.email = email
        db.session.commit()
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
    else:
        return jsonify({'success': False, 'message': 'Email is required'})

@dashboard_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not all([current_password, new_password, confirm_password]):
        return jsonify({'success': False, 'message': 'All fields are required'})
    
    if new_password != confirm_password:
        return jsonify({'success': False, 'message': 'Passwords do not match'})
    
    if not current_user.check_password(current_password):
        return jsonify({'success': False, 'message': 'Current password is incorrect'})
    
    current_user.set_password(new_password)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Password changed successfully'})

@dashboard_bp.route('/update_face', methods=['POST'])
@login_required
def update_face():
    """Update user face recognition"""
    try:
        face_image = request.files.get('new_face_image')
        if not face_image:
            return jsonify({'success': False, 'message': 'No image provided'})
        
        from utils.face_recognition import face_recognition
        from models.face_encoding import FaceEncoding
        import numpy as np
        from PIL import Image
        
        # Process image
        image = Image.open(face_image)
        image_array = np.array(image)
        
        # Detect faces
        face_locations = face_recognition.detect_faces(image_array)
        if not face_locations:
            return jsonify({'success': False, 'message': 'No face detected in the image'})
        
        # Extract face encoding
        face_encoding = face_recognition.extract_face_encoding(image_array)
        if face_encoding is None:
            return jsonify({'success': False, 'message': 'Could not extract face features'})
        
        # Remove old face encodings
        FaceEncoding.query.filter_by(user_id=current_user.id).delete()
        
        # Add new face encoding
        face_encoding_obj = FaceEncoding(
            user_id=current_user.id,
            encoding=face_encoding.tolist() if hasattr(face_encoding, 'tolist') else face_encoding,
            model_name='VGG-Face'
        )
        db.session.add(face_encoding_obj)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Face recognition updated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@dashboard_bp.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    """Delete user account"""
    if request.method == 'POST':
        # This would typically require password confirmation
        # For now, just show a message
        return jsonify({'success': False, 'message': 'Account deletion requires admin approval'})
    
    return jsonify({'success': False, 'message': 'Invalid request'})

@dashboard_bp.route('/send_admin_message', methods=['POST'])
@login_required
def send_admin_message():
    """Send a message to all admin users"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'})
        
        subject = data.get('subject')
        content = data.get('content')
        
        if not subject or not content:
            return jsonify({'success': False, 'message': 'Subject and content are required'})
        
        # Find all admin users
        admin_users = User.query.filter_by(is_admin=True).all()
        
        if not admin_users:
            return jsonify({'success': False, 'message': 'No admin users found'})
        
        # Create notifications for each admin
        for admin in admin_users:
            notification = Notification(
                user_id=admin.id,
                title=f"Message from {current_user.username}",
                message=f"Subject: {subject}<br>Message: {content}",
                type='message',
                icon='envelope'
            )
            db.session.add(notification)
        
        # Log the message
        log = Log(
            user_id=current_user.id,
            action='send_admin_message',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            details={'subject': subject, 'content': content}
        )
        db.session.add(log)
        db.session.commit()
        
        # Note: Real-time notifications would be sent via WebSocket here
        print(f"Message sent to {len(admin_users)} admin(s) from {current_user.username}")
        
        return jsonify({'success': True, 'message': 'Message sent to admin(s)'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@dashboard_bp.route('/api/check-messages')
@login_required
def check_messages():
    """Check for new messages for the current user"""
    try:
        unread_notifications = Notification.query.filter_by(
            user_id=current_user.id,
            is_read=False
        ).count()
        
        return jsonify({
            'success': True,
            'unread_count': unread_notifications
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@dashboard_bp.route('/delete_notification/<int:notification_id>', methods=['DELETE'])
@login_required
def delete_notification(notification_id):
    """Delete a notification"""
    try:
        notification = Notification.query.get_or_404(notification_id)
        
        # Check if user owns this notification or it's a broadcast notification
        if notification.user_id == current_user.id or notification.user_id is None:
            db.session.delete(notification)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Notification deleted successfully'})
        
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@dashboard_bp.route('/api/notifications-count')
@login_required
def get_notifications_count():
    """Get total notification count for real-time updates"""
    try:
        total_count = Notification.query.filter(
            (Notification.user_id == current_user.id) | (Notification.user_id.is_(None))
        ).count()
        
        unread_count = Notification.query.filter(
            (Notification.user_id == current_user.id) | (Notification.user_id.is_(None)),
            Notification.is_read == False
        ).count()
        
        return jsonify({
            'success': True,
            'count': total_count,
            'unread_count': unread_count
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@dashboard_bp.route('/api/users-list')
@login_required
def get_users_list():
    """Get list of users for messaging"""
    try:
        users = User.query.filter(User.id != current_user.id).all()
        users_data = []
        
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin
            })
        
        return jsonify({
            'success': True,
            'users': users_data
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@dashboard_bp.route('/send_user_message', methods=['POST'])
@login_required
def send_user_message():
    """Send message to another user"""
    try:
        data = request.get_json()
        target_user_id = data.get('target_user_id')
        message = data.get('message')
        
        if not target_user_id or not message:
            return jsonify({'success': False, 'message': 'Target user and message are required'})
        
        target_user = User.query.get(target_user_id)
        if not target_user:
            return jsonify({'success': False, 'message': 'Target user not found'})
        
        # Create notification for the target user
        notification = Notification(
            user_id=target_user_id,
            title=f'Message from {current_user.username}',
            message=message,
            type='message',
            icon='envelope'
        )
        db.session.add(notification)
        
        # Log the message
        log = Log(
            user_id=current_user.id,
            action='send_user_message',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            details={'target_user_id': target_user_id, 'message': message}
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Message sent to {target_user.username}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@dashboard_bp.route('/api/user-messages')
@login_required
def get_user_messages():
    """Get messages for the current user"""
    try:
        # Get notifications that are messages for this user
        messages = Notification.query.filter(
            Notification.user_id == current_user.id,
            Notification.type == 'message'
        ).order_by(Notification.created_at.desc()).limit(20).all()
        
        messages_data = []
        for msg in messages:
            # Try to extract sender info from the title
            sender_username = None
            if 'Message from ' in msg.title:
                sender_username = msg.title.replace('Message from ', '')
            
            messages_data.append({
                'id': msg.id,
                'title': msg.title,
                'message': msg.message,
                'sender_username': sender_username,
                'created_at': msg.created_at.isoformat(),
                'is_read': msg.is_read
            })
        
        return jsonify({
            'success': True,
            'messages': messages_data
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@dashboard_bp.route('/messages')
@login_required
def messages():
    """Messages page"""
    return render_template('dashboard/messages.html')

@dashboard_bp.route('/api/chats')
@login_required
def get_chats():
    """Get chat list for current user"""
    try:
        chat_type = request.args.get('type', 'private')
        
        if chat_type == 'private':
            # Get private chats (recent message exchanges)
            chats = []
            
            # Get users who have sent messages to current user
            sent_to_me = db.session.query(Notification.user_id, User.username, User.email)\
                .join(User, User.id == Notification.user_id)\
                .filter(Notification.type == 'message')\
                .filter(Notification.title.like(f'Message from %'))\
                .distinct().all()
            
            # Get users current user has sent messages to
            sent_by_me = db.session.query(Log.details, User.username, User.email)\
                .join(User, User.id == Log.user_id)\
                .filter(Log.action == 'send_user_message')\
                .filter(Log.user_id == current_user.id)\
                .distinct().all()
            
            # Combine and create chat list
            user_chats = {}
            
            for user_id, username, email in sent_to_me:
                if user_id != current_user.id:
                    user_chats[user_id] = {
                        'id': f'private_{user_id}',
                        'name': username,
                        'type': 'private',
                        'lastMessage': 'Recent message...',
                        'lastMessageTime': '',
                        'unreadCount': 0
                    }
            
            for log_details, username, email in sent_by_me:
                try:
                    details = json.loads(log_details) if isinstance(log_details, str) else log_details
                    target_user_id = details.get('target_user_id')
                    if target_user_id and target_user_id != current_user.id:
                        user_chats[target_user_id] = {
                            'id': f'private_{target_user_id}',
                            'name': User.query.get(target_user_id).username,
                            'type': 'private',
                            'lastMessage': 'Recent message...',
                            'lastMessageTime': '',
                            'unreadCount': 0
                        }
                except:
                    pass
            
            chats = list(user_chats.values())
            
        else:  # group chats
            # For now, create department-based groups
            departments = ['ENGINEERING', 'MARKETING', 'SALES', 'HR', 'FINANCE']
            chats = []
            
            for dept in departments:
                chats.append({
                    'id': f'group_{dept.lower()}',
                    'name': f'{dept} Team',
                    'type': 'group',
                    'lastMessage': 'Group conversation...',
                    'lastMessageTime': '',
                    'unreadCount': 0
                })
            
            # Add general chat
            chats.insert(0, {
                'id': 'group_general',
                'name': 'General Chat',
                'type': 'group',
                'lastMessage': 'Welcome to general chat!',
                'lastMessageTime': '',
                'unreadCount': 0
            })
        
        return jsonify({
            'success': True,
            'chats': chats
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@dashboard_bp.route('/api/messages/<chat_id>')
@login_required
def get_chat_messages(chat_id):
    """Get messages for a specific chat"""
    try:
        messages = []
        chat_info = {}
        
        if chat_id.startswith('private_'):
            # Private chat
            user_id = int(chat_id.replace('private_', ''))
            other_user = User.query.get(user_id)
            
            if not other_user:
                return jsonify({'success': False, 'message': 'User not found'})
            
            chat_info = {
                'name': other_user.username,
                'subtitle': f'Private chat with {other_user.username}'
            }
            
            # Get messages between current user and other user
            # Messages sent to current user from other user
            received_messages = Notification.query.filter(
                Notification.user_id == current_user.id,
                Notification.type == 'message',
                Notification.title == f'Message from {other_user.username}'
            ).all()
            
            for msg in received_messages:
                messages.append({
                    'id': msg.id,
                    'sender_id': user_id,
                    'sender_name': other_user.username,
                    'content': msg.message,
                    'created_at': msg.created_at.isoformat()
                })
            
            # Messages sent by current user to other user (from logs)
            sent_logs = Log.query.filter(
                Log.user_id == current_user.id,
                Log.action == 'send_user_message'
            ).all()
            
            for log in sent_logs:
                try:
                    details = json.loads(log.details) if isinstance(log.details, str) else log.details
                    if details.get('target_user_id') == user_id:
                        messages.append({
                            'id': f'sent_{log.id}',
                            'sender_id': current_user.id,
                            'sender_name': current_user.username,
                            'content': details.get('message', ''),
                            'created_at': log.timestamp.isoformat()
                        })
                except:
                    pass
            
        elif chat_id.startswith('group_'):
            # Group chat
            group_name = chat_id.replace('group_', '').replace('_', ' ').title()
            
            chat_info = {
                'name': group_name,
                'subtitle': f'Group chat - {group_name}'
            }
            
            # For demo purposes, create some sample group messages
            messages = [
                {
                    'id': 'group_1',
                    'sender_id': 999,
                    'sender_name': 'System',
                    'content': f'Welcome to {group_name} chat!',
                    'created_at': datetime.utcnow().isoformat()
                }
            ]
        
        # Sort messages by timestamp
        messages.sort(key=lambda x: x['created_at'])
        
        return jsonify({
            'success': True,
            'messages': messages,
            'chatInfo': chat_info
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@dashboard_bp.route('/api/send-message', methods=['POST'])
@login_required
def send_chat_message():
    """Send a message in a chat"""
    try:
        data = request.get_json()
        chat_id = data.get('chat_id')
        content = data.get('content')
        
        if not chat_id or not content:
            return jsonify({'success': False, 'message': 'Chat ID and content are required'})
        
        if chat_id.startswith('private_'):
            # Private message
            user_id = int(chat_id.replace('private_', ''))
            target_user = User.query.get(user_id)
            
            if not target_user:
                return jsonify({'success': False, 'message': 'User not found'})
            
            # Create notification for target user
            notification = Notification(
                user_id=user_id,
                title=f'Message from {current_user.username}',
                message=content,
                type='message',
                icon='envelope'
            )
            db.session.add(notification)
            
            # Log the message
            log = Log(
                user_id=current_user.id,
                action='send_user_message',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                details={'target_user_id': user_id, 'message': content}
            )
            db.session.add(log)
            
        elif chat_id.startswith('group_'):
            # Group message - broadcast to all users in group
            group_type = chat_id.replace('group_', '')
            
            if group_type == 'general':
                # Send to all users
                target_users = User.query.filter(User.id != current_user.id).all()
            else:
                # Send to users in specific department
                department = group_type.upper()
                target_users = User.query.filter(
                    User.department == department,
                    User.id != current_user.id
                ).all()
            
            # Create notifications for all target users
            for user in target_users:
                notification = Notification(
                    user_id=user.id,
                    title=f'Group Message - {group_type.title()}',
                    message=f'{current_user.username}: {content}',
                    type='message',
                    icon='users'
                )
                db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Message sent successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@dashboard_bp.route('/api/create-chat', methods=['POST'])
@login_required
def create_chat():
    """Create a new chat"""
    try:
        data = request.get_json()
        chat_type = data.get('type')
        
        if chat_type == 'private':
            user_id = data.get('user_id')
            if not user_id:
                return jsonify({'success': False, 'message': 'User ID is required'})
            
            # Check if user exists
            target_user = User.query.get(user_id)
            if not target_user:
                return jsonify({'success': False, 'message': 'User not found'})
            
            return jsonify({
                'success': True,
                'message': f'Private chat with {target_user.username} is ready',
                'chat_id': f'private_{user_id}'
            })
            
        elif chat_type == 'group':
            name = data.get('name')
            department = data.get('department')
            
            if not name:
                return jsonify({'success': False, 'message': 'Group name is required'})
            
            # For now, just return success (in a real app, you'd create a group record)
            return jsonify({
                'success': True,
                'message': f'Group "{name}" created successfully',
                'chat_id': f'group_{name.lower().replace(" ", "_")}'
            })
        
        return jsonify({'success': False, 'message': 'Invalid chat type'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@dashboard_bp.route('/api/start-break', methods=['POST'])
@login_required
def start_break():
    """Start a break for the current user"""
    try:
        data = request.get_json()
        duration = data.get('duration', 15)  # Default 15 minutes
        reason = data.get('reason', '')
        
        # Update user status to break
        current_user.status = 'break'
        current_user.break_start_time = datetime.utcnow()
        current_user.break_duration = duration
        current_user.break_reason = reason
        
        # Log the break start
        log = Log(
            user_id=current_user.id,
            action='start_break',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            details={
                'duration': duration,
                'reason': reason,
                'start_time': current_user.break_start_time.isoformat()
            }
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Break started for {duration} minutes',
            'break_start_time': current_user.break_start_time.isoformat()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@dashboard_bp.route('/api/end-break', methods=['POST'])
@login_required
def end_break():
    """End the current break"""
    try:
        if not hasattr(current_user, 'break_start_time') or not current_user.break_start_time:
            return jsonify({'success': False, 'message': 'No active break found'})
        
        # Calculate break duration
        break_end_time = datetime.utcnow()
        actual_duration = (break_end_time - current_user.break_start_time).total_seconds() / 60
        
        # Update user status back to online
        current_user.status = 'online'
        current_user.last_activity = break_end_time
        
        # Log the break end
        log = Log(
            user_id=current_user.id,
            action='end_break',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            details={
                'start_time': current_user.break_start_time.isoformat(),
                'end_time': break_end_time.isoformat(),
                'planned_duration': getattr(current_user, 'break_duration', 0),
                'actual_duration': round(actual_duration, 2),
                'reason': getattr(current_user, 'break_reason', '')
            }
        )
        db.session.add(log)
        
        # Clear break data
        current_user.break_start_time = None
        current_user.break_duration = None
        current_user.break_reason = None
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Break ended successfully',
            'actual_duration': round(actual_duration, 2)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@dashboard_bp.route('/api/break-status')
@login_required
def get_break_status():
    """Get current break status"""
    try:
        is_on_break = (
            hasattr(current_user, 'break_start_time') and 
            current_user.break_start_time is not None and
            current_user.status == 'break'
        )
        
        result = {
            'success': True,
            'isOnBreak': is_on_break
        }
        
        if is_on_break:
            result.update({
                'breakStartTime': current_user.break_start_time.isoformat(),
                'plannedDuration': getattr(current_user, 'break_duration', 0),
                'reason': getattr(current_user, 'break_reason', '')
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
@dashboard_bp.route('/send_user_message_by_username', methods=['POST'])
@login_required
def send_user_message_by_username():
    """Send message to user by username"""
    try:
        data = request.get_json()
        username = data.get('username')
        subject = data.get('subject', 'Message')
        message = data.get('message')
        
        if not username or not message:
            return jsonify({'success': False, 'message': 'Username and message are required'})
        
        target_user = User.query.filter_by(username=username).first()
        if not target_user:
            return jsonify({'success': False, 'message': 'User not found'})
        
        # Create notification for target user
        notification = Notification(
            user_id=target_user.id,
            title=f'{subject} - From {current_user.username}',
            message=message,
            type='message',
            icon='envelope'
        )
        db.session.add(notification)
        
        # Log the message
        log = Log(
            user_id=current_user.id,
            action='send_user_message_by_username',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            details={'target_username': username, 'subject': subject, 'message': message}
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Message sent to {username}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@dashboard_bp.route('/messages/enhanced')
@login_required
def messages_enhanced():
    """Enhanced messages page with group messaging"""
    return render_template('dashboard/messages_enhanced.html')

@dashboard_bp.route('/messages/whatsapp')
@login_required
def messages_whatsapp():
    """WhatsApp-style messaging interface"""
    return render_template('dashboard/messages_whatsapp.html')
    
@dashboard_bp.route('/test-input')
def test_input():
    """Test input area functionality"""
    return render_template('test_input.html')