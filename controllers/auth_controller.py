from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import cv2
import numpy as np
from PIL import Image
import base64
import io
from models.user import User
from models.log import Log
from app import db
from datetime import datetime
import os
# Face recognition disabled for now
# from utils.face_recognition import face_recognition

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        face_image = request.files.get('face_image')
        
        # Validate input
        if not all([username, email, password, face_image]):
            flash('All fields are required', 'error')
            return render_template('auth/register.html')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return render_template('auth/register.html')
        
        # Process face image using DeepFace
        try:
            # Read and process image
            image = Image.open(face_image)
            image_array = np.array(image)
            
            # Detect faces first
            face_locations = face_recognition.detect_faces(image_array)
            
            if not face_locations:
                flash('No face detected in the image. Please try again.', 'error')
                return render_template('auth/register.html')
            
            # Extract face encoding using DeepFace
            face_encoding = face_recognition.extract_face_encoding(image_array)
            if face_encoding is None:
                flash('Could not extract face features. Please try again.', 'error')
                return render_template('auth/register.html')
            
            # Create user
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.flush()  # Get user ID
            
            # Add face encoding using DeepFace
            from models.face_encoding import FaceEncoding
            face_encoding_obj = FaceEncoding(
                user_id=user.id,
                encoding=face_encoding.tolist() if hasattr(face_encoding, 'tolist') else face_encoding,
                model_name='VGG-Face'
            )
            db.session.add(face_encoding_obj)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            flash(f'Error processing face image: {str(e)}', 'error')
            return render_template('auth/register.html')
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        face_image = request.files.get('face_image')
        
        if not all([username, password, face_image]):
            flash('All fields are required', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Verify face using DeepFace
            try:
                # Process face image
                image = Image.open(face_image)
                image_array = np.array(image)
                
                # Detect faces first
                face_locations = face_recognition.detect_faces(image_array)
                
                if not face_locations:
                    flash('No face detected in the image', 'error')
                    return render_template('auth/login.html')
                
                # Extract face encoding using DeepFace
                face_encoding = face_recognition.extract_face_encoding(image_array)
                if face_encoding is None:
                    flash('Could not extract face features', 'error')
                    return render_template('auth/login.html')
                
                # Get stored face encodings
                stored_encodings = user.get_face_encodings()
                if not stored_encodings:
                    flash('No face data found for this user', 'error')
                    return render_template('auth/login.html')
                
                # Convert stored encodings to numpy arrays
                stored_arrays = [np.array(encoding) for encoding in stored_encodings]
                
                # Compare faces using DeepFace
                matches = face_recognition.compare_faces(stored_arrays, face_encoding)
                
                if any(matches):
                    login_user(user)
                    user.last_login = datetime.utcnow()
                    user.update_activity()
                    
                    # Log login
                    log = Log(
                        user_id=user.id,
                        action='login',
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent')
                    )
                    db.session.add(log)
                    db.session.commit()
                    
                    flash('Login successful!', 'success')
                    return redirect(url_for('dashboard.index'))
                else:
                    flash('Face verification failed', 'error')
                    return render_template('auth/login.html')
                    
            except Exception as e:
                flash(f'Error during face verification: {str(e)}', 'error')
                return render_template('auth/login.html')
        else:
            flash('Invalid username or password', 'error')
            return render_template('auth/login.html')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    # Log logout
    log = Log(
        user_id=current_user.id,
        action='logout',
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    db.session.add(log)
    db.session.commit()
    
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/verify_face', methods=['POST'])
@login_required
def verify_face():
    """Periodic face verification during work hours using DeepFace"""
    try:
        face_image = request.files.get('face_image')
        if not face_image:
            return jsonify({'success': False, 'message': 'No image provided'})
        
        # Process face image using DeepFace
        image = Image.open(face_image)
        image_array = np.array(image)
        
        # Detect faces first
        face_locations = face_recognition.detect_faces(image_array)
        
        if not face_locations:
            return jsonify({'success': False, 'message': 'No face detected'})
        
        # Extract face encoding using DeepFace
        face_encoding = face_recognition.extract_face_encoding(image_array)
        if face_encoding is None:
            return jsonify({'success': False, 'message': 'Could not extract face features'})
        
        # Get stored face encodings
        stored_encodings = current_user.get_face_encodings()
        if not stored_encodings:
            return jsonify({'success': False, 'message': 'No face data found'})
        
        # Convert stored encodings to numpy arrays
        stored_arrays = [np.array(encoding) for encoding in stored_encodings]
        
        # Compare faces using DeepFace
        matches = face_recognition.compare_faces(stored_arrays, face_encoding)
        
        if any(matches):
            # Log successful verification
            log = Log(
                user_id=current_user.id,
                action='face_verification',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                details={'result': 'success'}
            )
            db.session.add(log)
            db.session.commit()
            
            current_user.update_activity()
            return jsonify({'success': True, 'message': 'Face verification successful'})
        else:
            # Log failed verification
            log = Log(
                user_id=current_user.id,
                action='face_verification',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                details={'result': 'failed'}
            )
            db.session.add(log)
            db.session.commit()
            
            return jsonify({'success': False, 'message': 'Face verification failed'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@auth_bp.route('/continuous_face_check', methods=['POST'])
@login_required
def continuous_face_check():
    """Continuous face recognition check for monitoring"""
    try:
        if 'face_image' not in request.files:
            return jsonify({'success': False, 'message': 'No image provided'})
        
        face_image = request.files['face_image']
        if face_image.filename == '':
            return jsonify({'success': False, 'message': 'No image selected'})
        
        # Read image
        image_data = face_image.read()
        nparr = np.frombuffer(image_data, np.uint8)
        img_array = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img_array is None:
            return jsonify({'success': False, 'message': 'Invalid image format'})
        
        # Detect faces
        face_locations = face_recognition.detect_faces(img_array)
        
        if not face_locations:
            # No face detected - possible sleep or absence
            return jsonify({
                'success': True, 
                'face_recognized': False, 
                'sleep_detected': True,
                'message': 'No face detected'
            })
        
        # Extract face encoding
        face_encoding = face_recognition.extract_face_encoding(img_array)
        
        if face_encoding is None:
            return jsonify({
                'success': True, 
                'face_recognized': False, 
                'sleep_detected': True,
                'message': 'Could not extract face encoding'
            })
        
        # Get current user's face encodings
        known_encodings = current_user.get_face_encodings()
        
        if not known_encodings:
            return jsonify({
                'success': True, 
                'face_recognized': False, 
                'sleep_detected': False,
                'message': 'No face encodings found for user'
            })
        
        # Compare faces
        matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.6)
        
        if any(matches):
            # Face recognized - update activity
            current_user.update_activity()
            
            # Log successful recognition
            log = Log(
                user_id=current_user.id,
                action='face_verification_success',
                details='Continuous monitoring - face recognized'
            )
            db.session.add(log)
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'face_recognized': True, 
                'sleep_detected': False,
                'message': 'Face recognized successfully'
            })
        else:
            # Face not recognized - wrong person
            # Log security alert
            log = Log(
                user_id=current_user.id,
                action='security_alert',
                details='Continuous monitoring - face not recognized (possible unauthorized access)'
            )
            db.session.add(log)
            
            # Create notification for admin
            from models.notification import Notification
            admin_users = User.query.filter_by(is_admin=True).all()
            for admin in admin_users:
                notification = Notification(
                    user_id=admin.id,
                    title='Security Alert',
                    message=f'Unauthorized face detected for user {current_user.username}',
                    type='security',
                    icon='exclamation-triangle'
                )
                db.session.add(notification)
            
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'face_recognized': False, 
                'sleep_detected': False,
                'message': 'Face not recognized - security alert triggered'
            })
            
    except Exception as e:
        return jsonify({'success': False, 'message': 'Internal server error'})
