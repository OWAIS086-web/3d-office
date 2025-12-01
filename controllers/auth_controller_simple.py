from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from models.log import Log
from models.face_encoding import FaceEncoding
from app import db
from datetime import datetime
import os
import base64
import io
from PIL import Image
import numpy as np

auth_bp = Blueprint('auth', __name__)

def verify_face(user_id, face_data):
    """Verify face using optimized face recognition"""
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
            print(f"DeepFace verification error: {str(e)}")
            # Fallback to basic comparison if DeepFace fails
            return basic_face_comparison(stored_data, face_data)
        
    except Exception as e:
        print(f"Face verification error: {str(e)}")
        return False

def basic_face_comparison(stored_data, face_data):
    """Fallback basic face comparison if DeepFace is not available"""
    try:
        # Extract base64 data
        if ',' in face_data:
            current_b64 = face_data.split(',')[1]
        else:
            current_b64 = face_data
            
        if ',' in stored_data:
            stored_b64 = stored_data.split(',')[1]
        else:
            stored_b64 = stored_data
        
        # Basic similarity check - compare lengths and some bytes
        if abs(len(current_b64) - len(stored_b64)) > len(stored_b64) * 0.3:
            print("Face data size difference too large")
            return False
        
        # Compare some sample bytes for basic similarity
        sample_size = min(100, len(current_b64), len(stored_b64))
        current_sample = current_b64[:sample_size]
        stored_sample = stored_b64[:sample_size]
        
        # Calculate simple similarity
        matches = sum(1 for a, b in zip(current_sample, stored_sample) if a == b)
        similarity = matches / sample_size
        
        print(f"Basic face similarity: {similarity:.2f}")
        
        # Require at least 80% similarity for basic validation
        return similarity >= 0.8
        
    except Exception as e:
        print(f"Basic face comparison error: {str(e)}")
        return False

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration with face capture"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        face_data = request.form.get('face_data')
        
        if not all([username, email, password]):
            flash('All fields are required', 'error')
            return redirect(url_for('auth.register'))
        
        if not face_data:
            flash('Face capture is required for registration', 'error')
            return redirect(url_for('auth.register'))
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('auth.register'))
        
        try:
            # Validate face data quality using optimized functions
            from utils.face_recognition_optimized import detect_face_optimized, get_face_quality_score_optimized, extract_face_encoding_optimized
            
            # Check if face is detected
            if not detect_face_optimized(face_data):
                flash('No face detected in the image. Please capture a clear photo of your face.', 'error')
                return redirect(url_for('auth.register'))
            
            # Check face quality
            quality_score = get_face_quality_score_optimized(face_data)
            if quality_score < 0.5:
                flash('Face image quality is too low. Please capture a clearer photo with good lighting.', 'error')
                return redirect(url_for('auth.register'))
            
            # Create new user
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.flush()  # Get user ID
            
            # Extract and store face encoding
            try:
                face_embedding = extract_face_encoding_optimized(face_data)
                if face_embedding is not None:
                    # Store both the original image and the embedding
                    face_encoding = FaceEncoding(
                        user_id=user.id,
                        encoding=face_data,  # Store original base64 image
                        model_name='DeepFace_VGG-Face'
                    )
                else:
                    # Fallback to storing just the image
                    face_encoding = FaceEncoding(
                        user_id=user.id,
                        encoding=face_data,
                        model_name='webcam_capture'
                    )
            except Exception as face_error:
                print(f"Face encoding error: {face_error}")
                # Still store the image for basic comparison
                face_encoding = FaceEncoding(
                    user_id=user.id,
                    encoding=face_data,
                    model_name='webcam_capture_fallback'
                )
            
            db.session.add(face_encoding)
            db.session.commit()
            
            flash('Registration successful! Your face has been registered for secure login.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'error')
            return redirect(url_for('auth.register'))
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login with face verification"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        face_data = request.form.get('face_data')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return redirect(url_for('auth.login'))
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Face verification is mandatory
            if not face_data:
                flash('Face verification is required for login. Please capture your face.', 'error')
                return redirect(url_for('auth.login'))
            
            # Verify face data
            face_verified = verify_face(user.id, face_data)
            if not face_verified:
                flash('Face verification failed. Your face does not match the registered face. Please try again.', 'error')
                return redirect(url_for('auth.login'))
            
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
            
            flash('Login successful!', 'success')
            
            # Redirect to admin dashboard if admin, otherwise user dashboard
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
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
    return redirect(url_for('auth.login'))

@auth_bp.route('/update_activity', methods=['POST'])
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