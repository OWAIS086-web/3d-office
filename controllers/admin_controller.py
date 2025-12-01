from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.user import User
from models.notification import Notification
from models.log import Log
from app import db
from datetime import datetime, timedelta
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/office-layout')
@login_required
@admin_required
def office_layout():
    """Display futuristic office layout with department-based seating"""
    return render_template('admin/office_layout.html')

@admin_bp.route('/send-notification', methods=['GET', 'POST'])
@login_required
@admin_required
def send_notification():
    """Send real-time notification to users"""
    users = User.query.filter_by(is_admin=False).all()
    
    if request.method == 'POST':
        user_ids = request.form.getlist('user_ids')
        title = request.form.get('title')
        message = request.form.get('message')
        notification_type = request.form.get('type', 'info')
        
        if not title or not message:
            flash('Title and message are required', 'error')
            return redirect(url_for('admin.send_notification'))
        
        # Send to all users if none selected
        if not user_ids:
            user_ids = [str(user.id) for user in users]
        
        # Create notifications for selected users
        for user_id in user_ids:
            notification = Notification(
                user_id=int(user_id),
                title=title,
                message=message,
                type=notification_type,
                icon='bell'
            )
            db.session.add(notification)
            
            # Note: Real-time notifications would be sent via WebSocket here
            print(f"Notification sent to user {user_id}: {title}")
        
        db.session.commit()
        flash(f'Notification sent to {len(user_ids)} users', 'success')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/send_notification.html', users=users)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """View all users and their status"""
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """3D Admin dashboard page with employee status visualization"""
    from datetime import datetime, timedelta
    
    # Get all users
    users = User.query.filter_by(is_admin=False).all()
    
    # Categorize users by status
    user_status_data = []
    departments = ['ENGINEERING', 'MARKETING', 'SALES', 'HR', 'FINANCE']
    
    for i, user in enumerate(users):
        # Determine user status based on online status and activity
        if user.is_online:
            # Check if user is on break (no activity in last 15 minutes but still online)
            if user.last_activity and datetime.utcnow() - user.last_activity > timedelta(minutes=15):
                status = 'break'
                status_color = 'blue'
            else:
                status = 'online'
                status_color = 'green'
        else:
            status = 'offline'
            status_color = 'red'
        
        # Use user's actual department or assign cyclically for demo
        department = user.department or departments[i % len(departments)]
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'status': status,
            'status_color': status_color,
            'department': department,
            'last_activity': user.last_activity.isoformat() if user.last_activity else None,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'position': {
                'x': (i % 4) * 250 + 100,  # Grid positioning
                'y': (i // 4) * 200 + 100,
                'z': 0
            }
        }
        user_status_data.append(user_data)
    
    # Get department statistics
    dept_stats = {}
    for dept in departments:
        dept_users = [u for u in user_status_data if u['department'] == dept]
        dept_stats[dept] = {
            'total': len(dept_users),
            'online': len([u for u in dept_users if u['status'] == 'online']),
            'break': len([u for u in dept_users if u['status'] == 'break']),
            'offline': len([u for u in dept_users if u['status'] == 'offline'])
        }
    
    # Overall statistics
    total_users = len(users)
    online_users = len([u for u in user_status_data if u['status'] == 'online'])
    break_users = len([u for u in user_status_data if u['status'] == 'break'])
    offline_users = len([u for u in user_status_data if u['status'] == 'offline'])
    
    return render_template('admin/dashboard.html', 
                          user_status_data=user_status_data,
                          dept_stats=dept_stats,
                          total_users=total_users,
                          online_users=online_users,
                          break_users=break_users,
                          offline_users=offline_users,
                          departments=departments)

@admin_bp.route('/notifications')
@login_required
@admin_required
def notifications():
    """View all notifications"""
    notifications = Notification.query.order_by(Notification.created_at.desc()).limit(50).all()
    return render_template('admin/notifications.html', notifications=notifications)

@admin_bp.route('/api/online-users')
@login_required
@admin_required
def get_online_users():
    """API endpoint to get online users"""
    online_users = User.query.filter_by(is_online=True).all()
    users_data = []
    
    for user in online_users:
        users_data.append({
            'id': user.id,
            'username': user.username,
            'last_active': user.last_active.isoformat() if user.last_active else None,
            'status': 'online'
        })
    
    return jsonify({'users': users_data})

@admin_bp.route('/api/user-status')
@login_required
@admin_required
def get_user_status():
    """API endpoint to get real-time user status for 3D dashboard"""
    from datetime import datetime, timedelta
    
    users = User.query.filter_by(is_admin=False).all()
    departments = ['ENGINEERING', 'MARKETING', 'SALES', 'HR', 'FINANCE']
    
    user_status_data = []
    
    for i, user in enumerate(users):
        # Determine user status based on online status and activity
        if user.is_online:
            # Check if user is on break (no activity in last 15 minutes but still online)
            if user.last_activity and datetime.utcnow() - user.last_activity > timedelta(minutes=15):
                status = 'break'
                status_color = 'blue'
            else:
                status = 'online'
                status_color = 'green'
        else:
            status = 'offline'
            status_color = 'red'
        
        # Assign department cyclically for demo
        department = departments[i % len(departments)]
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'status': status,
            'status_color': status_color,
            'department': department,
            'last_activity': user.last_activity.isoformat() if user.last_activity else None,
            'last_login': user.last_login.isoformat() if user.last_login else None
        }
        user_status_data.append(user_data)
    
    # Calculate statistics
    total_users = len(users)
    online_users = len([u for u in user_status_data if u['status'] == 'online'])
    break_users = len([u for u in user_status_data if u['status'] == 'break'])
    offline_users = len([u for u in user_status_data if u['status'] == 'offline'])
    
    # Department statistics
    dept_stats = {}
    for dept in departments:
        dept_users = [u for u in user_status_data if u['department'] == dept]
        dept_stats[dept] = {
            'total': len(dept_users),
            'online': len([u for u in dept_users if u['status'] == 'online']),
            'break': len([u for u in dept_users if u['status'] == 'break']),
            'offline': len([u for u in dept_users if u['status'] == 'offline'])
        }
    
    return jsonify({
        'users': user_status_data,
        'stats': {
            'total': total_users,
            'online': online_users,
            'break': break_users,
            'offline': offline_users
        },
        'departments': dept_stats,
        'timestamp': datetime.utcnow().isoformat()
    })

@admin_bp.route('/departments')
@login_required
@admin_required
def manage_departments():
    """Manage departments"""
    # For now, departments are hardcoded, but this could be made dynamic
    departments = ['ENGINEERING', 'MARKETING', 'SALES', 'HR', 'FINANCE']
    users = User.query.filter_by(is_admin=False).all()
    
    return render_template('admin/departments.html', 
                          departments=departments, 
                          users=users)

@admin_bp.route('/add-user', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    """Add new user"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        department = request.form.get('department')
        is_admin = request.form.get('is_admin') == 'on'
        face_data = request.form.get('face_data')
        
        if not all([username, email, password]):
            flash('All fields are required', 'error')
            return redirect(url_for('admin.add_user'))
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('admin.add_user'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('admin.add_user'))
        
        try:
            # Create new user
            user = User(username=username, email=email, is_admin=is_admin)
            user.set_password(password)
            # Store department in a simple way (you might want to create a Department model)
            user.department = department
            db.session.add(user)
            db.session.flush()  # Get user ID
            
            # Store face data if provided
            if face_data:
                try:
                    from models.face_encoding import FaceEncoding
                    face_encoding = FaceEncoding(
                        user_id=user.id,
                        encoding=face_data
                    )
                    db.session.add(face_encoding)
                except Exception as face_error:
                    print(f"Error storing face data: {face_error}")
                    # Continue without face data
            
            db.session.commit()
            
            success_msg = f'User {username} created successfully'
            if face_data:
                success_msg += ' with face authentication'
            flash(success_msg, 'success')
            return redirect(url_for('admin.users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to create user: {str(e)}', 'error')
            return redirect(url_for('admin.add_user'))
    
    departments = ['ENGINEERING', 'MARKETING', 'SALES', 'HR', 'FINANCE']
    return render_template('admin/add_user.html', departments=departments)

@admin_bp.route('/assign-department', methods=['POST'])
@login_required
@admin_required
def assign_department():
    """Assign user to department"""
    data = request.get_json()
    user_id = data.get('user_id')
    department = data.get('department')
    
    if not user_id or not department:
        return jsonify({'success': False, 'message': 'User ID and department are required'}), 400
    
    user = User.query.get_or_404(user_id)
    user.department = department
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'User {user.username} assigned to {department}'
    })

@admin_bp.route('/api/user-face/<int:user_id>')
@login_required
@admin_required
def get_user_face(user_id):
    """Get user face image"""
    try:
        from models.face_encoding import FaceEncoding
        face_encoding = FaceEncoding.query.filter_by(user_id=user_id).first()
        
        if face_encoding and face_encoding.encoding:
            # Return the base64 image data
            return jsonify({
                'success': True,
                'face_data': face_encoding.encoding
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No face data found'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@admin_bp.route('/api/send-message', methods=['POST'])
@login_required
@admin_required
def send_message_api():
    """Send message to user via API"""
    data = request.get_json()
    user_id = data.get('user_id')
    message = data.get('message')
    
    if not user_id or not message:
        return jsonify({'success': False, 'message': 'User ID and message are required'}), 400
    
    user = User.query.get_or_404(user_id)
    
    # Create notification
    notification = Notification(
        user_id=user_id,
        title='Message from Admin',
        message=message,
        type='message',
        icon='envelope'
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Message sent to {user.username}'
    })

@admin_bp.route('/api/messages')
@login_required
@admin_required
def get_messages():
    """Get recent messages for live updates"""
    messages = Notification.query.filter_by(type='message').order_by(
        Notification.created_at.desc()
    ).limit(10).all()
    
    message_data = []
    for msg in messages:
        message_data.append({
            'id': msg.id,
            'title': msg.title,
            'message': msg.message,
            'user_id': msg.user_id,
            'username': msg.user.username if msg.user else 'Unknown',
            'created_at': msg.created_at.isoformat(),
            'is_read': msg.is_read
        })
    
    return jsonify({
        'success': True,
        'messages': message_data
    })
@admin_bp.route('/api/broadcast-notification', methods=['POST'])
@login_required
@admin_required
def broadcast_notification():
    """Broadcast notification to all online users"""
    data = request.get_json()
    title = data.get('title')
    message = data.get('message')
    notification_type = data.get('type', 'info')
    
    if not title or not message:
        return jsonify({'success': False, 'message': 'Title and message are required'}), 400
    
    # Get all online users
    online_users = User.query.filter_by(is_admin=False).all()
    
    # Send notification to all online users
    for user in online_users:
        if user.is_online:
            notification = Notification(
                user_id=user.id,
                title=title,
                message=message,
                type=notification_type,
                icon='broadcast-tower'
            )
            db.session.add(notification)
            
            # Note: Real-time notifications would be sent via WebSocket here
            print(f"Notification sent to user {user.id}: {title}")
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Notification sent to {len([u for u in online_users if u.is_online])} online users'
    })

@admin_bp.route('/api/broadcast-alert', methods=['POST'])
@login_required
@admin_required
def broadcast_alert():
    """Broadcast alert using the quick alert popup"""
    data = request.get_json()
    alert_type = data.get('type', 'info')
    message = data.get('message')
    target = data.get('target', 'all')
    title = data.get('title', 'Alert')
    
    if not message:
        return jsonify({'success': False, 'message': 'Message is required'}), 400
    
    # Determine target users
    if target == 'all':
        target_users = User.query.filter_by(is_admin=False).all()
    else:
        # Target specific department
        target_users = User.query.filter_by(is_admin=False, department=target).all()
    
    # Create notifications for target users
    notification_count = 0
    for user in target_users:
        notification = Notification(
            user_id=user.id,
            title=title,
            message=message,
            type=alert_type,
            icon='exclamation-triangle' if alert_type in ['warning', 'urgent', 'emergency'] else 'info-circle'
        )
        db.session.add(notification)
        notification_count += 1
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Alert sent to {notification_count} users'
    })

@admin_bp.route('/messages')
@login_required
@admin_required
def messages():
    """Admin messages page"""
    return render_template('admin/messages.html')

@admin_bp.route('/api/users-for-messaging')
@login_required
@admin_required
def get_users_for_messaging():
    """Get all users for messaging"""
    try:
        users = User.query.filter_by(is_admin=False).all()
        users_data = []
        
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_online': user.is_online if hasattr(user, 'is_online') else False
            })
        
        return jsonify({
            'success': True,
            'users': users_data
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/api/messages/<int:user_id>')
@login_required
@admin_required
def get_admin_messages(user_id):
    """Get messages between admin and specific user"""
    try:
        messages = []
        
        # Get messages sent to the user from admin
        sent_to_user = Notification.query.filter(
            Notification.user_id == user_id,
            Notification.type == 'message',
            Notification.title.like('Message from %')
        ).all()
        
        for msg in sent_to_user:
            messages.append({
                'id': msg.id,
                'content': msg.message,
                'sender_name': 'Admin',
                'is_admin': True,
                'created_at': msg.created_at.isoformat()
            })
        
        # Get messages sent by the user to admin
        user = User.query.get(user_id)
        if user:
            sent_by_user = Notification.query.filter(
                Notification.type == 'message',
                Notification.title == f'Message from {user.username}'
            ).all()
            
            for msg in sent_by_user:
                messages.append({
                    'id': msg.id,
                    'content': msg.message,
                    'sender_name': user.username,
                    'is_admin': False,
                    'created_at': msg.created_at.isoformat()
                })
        
        # Sort messages by timestamp
        messages.sort(key=lambda x: x['created_at'])
        
        return jsonify({
            'success': True,
            'messages': messages
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/api/send-message-by-username', methods=['POST'])
@login_required
@admin_required
def send_message_by_username():
    """Send message to user by username"""
    try:
        data = request.get_json()
        username = data.get('username')
        message = data.get('message')
        
        if not username or not message:
            return jsonify({'success': False, 'message': 'Username and message are required'})
        
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'success': False, 'message': 'User not found'})
        
        # Create notification for the user
        notification = Notification(
            user_id=user.id,
            title=f'Message from Admin',
            message=message,
            type='message',
            icon='envelope'
        )
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Message sent to {username}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/delete-user/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Don't allow deleting admin users
        if user.is_admin:
            return jsonify({'success': False, 'message': 'Cannot delete admin users'}), 403
        
        # Don't allow deleting yourself
        if user.id == current_user.id:
            return jsonify({'success': False, 'message': 'Cannot delete your own account'}), 403
        
        username = user.username
        
        # Delete related records first
        Notification.query.filter_by(user_id=user_id).delete()
        Log.query.filter_by(user_id=user_id).delete()
        
        # Delete face encodings if they exist
        try:
            from models.face_encoding import FaceEncoding
            FaceEncoding.query.filter_by(user_id=user_id).delete()
        except:
            pass  # Face encoding model might not exist
        
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'User {username} deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
@admin_bp.route('/messages/whatsapp')
@login_required
@admin_required
def messages_whatsapp():
    """Admin WhatsApp-style messaging interface"""
    return render_template('admin/messages_whatsapp.html')