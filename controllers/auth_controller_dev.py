from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from models.log import Log
from models.face_encoding import FaceEncoding
from app import db
from datetime import datetime
import os

auth_dev_bp = Blueprint('auth_dev', __name__)

def should_use_face_recognition():
    """Check if face recognition should be used"""
    return current_app.config.get('FACE_RECOGNITION_ENABLED', True)

def verify_face_dev(user_id, face_data):
    """Development face verification - can be bypassed"""
    if not should_use_face_recognition():
        print("Face recognition disabled in development mode")
        return True
    
    try:
        # Import optimized face recognition utilities
        from utils.face_recognition_optimized import verify_faces_optimized, detect_face_optimized
        
        # Get stored face encoding for user
        stored_face = FaceEncoding.query.filter_by(user_id=user_id).first()
        if not stored_face:
            print(f"No stored face found for user {user_id}")
            return False
        
        if not face_data or not face_data.startswith('data:image'):
            print("Invalid face data format")
            return False
        
        stored_data = stored_face.encoding
        if not stored_data:
            print("No stored face data")
            return False
        
        # First, check if there's a face in the current image
        if not detect_face_optimized(face_data):
            print("No face detected in login image")
            return False
        
        # Verify faces using optimized recognition
        try:
            is_match = verify_faces_optimized(stored_data, face_data)
            
            if is_match:
                print(f"Face verification successful for user {user_id}")
                return True
            else:
                print(f"Face verification failed for user {user_id} - faces do not match")
                return False
                
        except Exception as e:
            print(f"Face verification error: {str(e)}")
            # In development mode, allow fallback
            if not should_use_face_recognition():
                return True
            return False
        
    except Exception as e:
        print(f"Face verification error: {str(e)}")
        # In development mode, allow bypass
        if not should_use_face_recognition():
            return True
        return False

@auth_dev_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration with optional face capture"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        face_data = request.form.get('face_data')
        
        if not all([username, email, password]):
            flash('All fields are required', 'error')
            return redirect(url_for('auth_dev.register'))
        
        # Face capture is optional in development mode
        if should_use_face_recognition() and not face_data:
            flash('Face capture is required for registration', 'error')
            return redirect(url_for('auth_dev.register'))
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('auth_dev.register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('auth_dev.register'))
        
        try:
            # Create new user
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.flush()  # Get user ID
            
            # Store face encoding if provided and face recognition is enabled
            if face_data and should_use_face_recognition():
                try:
                    from utils.face_recognition_optimized import detect_face_optimized, get_face_quality_score_optimized
                    
                    # Check if face is detected
                    if not detect_face_optimized(face_data):
                        flash('No face detected in the image. Please capture a clear photo of your face.', 'error')
                        db.session.rollback()
                        return redirect(url_for('auth_dev.register'))
                    
                    # Check face quality
                    quality_score = get_face_quality_score_optimized(face_data)
                    if quality_score < 0.3:  # Lower threshold for development
                        flash('Face image quality is low but acceptable for development.', 'warning')
                    
                    # Store face encoding
                    face_encoding = FaceEncoding(
                        user_id=user.id,
                        encoding=face_data,
                        model_name='development_mode'
                    )
                    db.session.add(face_encoding)
                    
                except Exception as face_error:
                    print(f"Face processing error (non-critical in dev): {face_error}")
                    # Continue without face data in development
                    pass
            
            db.session.commit()
            
            if should_use_face_recognition():
                flash('Registration successful! Your face has been registered for secure login.', 'success')
            else:
                flash('Registration successful! (Face recognition disabled in development mode)', 'success')
            
            return redirect(url_for('auth_dev.login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'error')
            return redirect(url_for('auth_dev.register'))
    
    return render_template('auth/register.html')

@auth_dev_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login with optional face verification"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        face_data = request.form.get('face_data')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return redirect(url_for('auth_dev.login'))
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Face verification is optional in development mode
            if should_use_face_recognition():
                if not face_data:
                    flash('Face verification is required for login. Please capture your face.', 'error')
                    return redirect(url_for('auth_dev.login'))
                
                # Verify face data
                face_verified = verify_face_dev(user.id, face_data)
                if not face_verified:
                    flash('Face verification failed. Please try again.', 'error')
                    return redirect(url_for('auth_dev.login'))
            else:
                print("Face verification bypassed in development mode")
            
            login_user(user)
            
            # Update user activity and status
            user.last_login = datetime.utcnow()
            user.last_activity = datetime.utcnow()
            user.current_status = 'online'
            user.status = 'online'
            user.is_online = True
            db.session.commit()
            
            # Log the login
            log = Log(
                user_id=user.id,
                action='login',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(log)
            db.session.commit()
            
            if should_use_face_recognition():
                flash('Login successful!', 'success')
            else:
                flash('Login successful! (Development mode)', 'success')
            
            # Redirect to admin dashboard if admin, otherwise user dashboard
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')

@auth_dev_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    # Update user status
    current_user.current_status = 'offline'
    current_user.status = 'offline'
    current_user.is_online = False
    current_user.last_activity = datetime.utcnow()
    
    # Log the logout
    log = Log(
        user_id=current_user.id,
        action='logout',
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    db.session.add(log)
    db.session.commit()
    
    logout_user()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('auth_dev.login'))

@auth_dev_bp.route('/update_activity', methods=['POST'])
@login_required
def update_activity():
    """Update user activity timestamp"""
    try:
        current_user.last_activity = datetime.utcnow()
        if current_user.current_status == 'offline':
            current_user.current_status = 'online'
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})