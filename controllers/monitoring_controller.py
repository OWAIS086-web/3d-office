from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from models.user import User
from models.log import Log
from models.notification import Notification
from utils.face_recognition import face_recognition
from datetime import datetime, timedelta
import cv2
import numpy as np
from PIL import Image
import io
import base64

monitoring_bp = Blueprint('monitoring', __name__)

@monitoring_bp.route('/api/user-stream/<int:user_id>')
@login_required
def user_stream_details(user_id):
    """Get stream details for a specific user"""
    # Check if current user is admin or the user themselves
    if not current_user.is_admin and current_user.id != user_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    user = User.query.get_or_404(user_id)
    
    # Get the latest log entries for this user
    recent_logs = Log.query.filter_by(user_id=user_id).order_by(Log.timestamp.desc()).limit(10).all()
    
    logs_data = []
    for log in recent_logs:
        logs_data.append({
            'action': log.action,
            'details': log.details,
            'timestamp': log.timestamp.isoformat()
        })
    
    return jsonify({
        'success': True,
        'user_id': user.id,
        'username': user.username,
        'is_online': user.is_online,
        'last_active': user.last_active.isoformat() if user.last_active else None,
        'recent_logs': logs_data
    })

@monitoring_bp.route('/live')
@login_required
def live():
    """Live monitoring page"""
    return render_template('monitoring/live.html')

@monitoring_bp.route('/continuous_face_check', methods=['POST'])
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
            # Log absence detection
            log = Log(
                user_id=current_user.id,
                action='absence_detected',
                details='Continuous monitoring - no face detected (possible sleep or absence)'
            )
            from app import db
            db.session.add(log)
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'face_recognized': False, 
                'sleep_detected': True,
                'message': 'No face detected'
            })
        
        # Check for sleep detection using eye aspect ratio
        is_sleeping = detect_sleep(img_array, face_locations)
        if is_sleeping:
            # Log sleep detection
            log = Log(
                user_id=current_user.id,
                action='sleep_detected',
                details='Continuous monitoring - sleep detected (eyes closed)'
            )
            from app import db
            db.session.add(log)
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'face_recognized': True, 
                'sleep_detected': True,
                'message': 'Sleep detected'
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
            from app import db
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
            from app import db
            db.session.add(log)
            
            # Create notification for admin
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
        current_app.logger.error(f"Error in continuous face check: {str(e)}")
        return jsonify({'success': False, 'message': 'Internal server error'})

def detect_sleep(image, face_locations):
    """
    Detect if a person is sleeping based on eye aspect ratio
    
    Args:
        image: Image array
        face_locations: List of face bounding boxes
        
    Returns:
        Boolean indicating if sleep is detected
    """
    try:
        import dlib
        from scipy.spatial import distance
        
        # Initialize dlib's face detector and facial landmark predictor
        detector = dlib.get_frontal_face_detector()
        predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
        
        # Convert face_locations to dlib rectangles
        dlib_rects = []
        for (top, right, bottom, left) in face_locations:
            dlib_rects.append(dlib.rectangle(left, top, right, bottom))
        
        # For each face, check eye aspect ratio
        for rect in dlib_rects:
            # Get facial landmarks
            shape = predictor(image, rect)
            
            # Extract eye coordinates
            left_eye = []
            right_eye = []
            
            # Left eye points (36-41)
            for i in range(36, 42):
                left_eye.append((shape.part(i).x, shape.part(i).y))
            
            # Right eye points (42-47)
            for i in range(42, 48):
                right_eye.append((shape.part(i).x, shape.part(i).y))
            
            # Calculate eye aspect ratio
            left_ear = calculate_ear(left_eye)
            right_ear = calculate_ear(right_eye)
            
            # Average the eye aspect ratio
            ear = (left_ear + right_ear) / 2.0
            
            # Check if eyes are closed (EAR < threshold)
            if ear < 0.2:  # Threshold for closed eyes
                return True
        
        return False
        
    except Exception as e:
        current_app.logger.error(f"Error in sleep detection: {str(e)}")
        return False

def calculate_ear(eye):
    """
    Calculate eye aspect ratio
    
    Args:
        eye: List of 6 (x, y) coordinates of the eye landmarks
        
    Returns:
        Eye aspect ratio
    """
    from scipy.spatial import distance
    
    # Calculate vertical distances
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    
    # Calculate horizontal distance
    C = distance.euclidean(eye[0], eye[3])
    
    # Calculate eye aspect ratio
    ear = (A + B) / (2.0 * C)
    
    return ear

@monitoring_bp.route('/sleep_detection', methods=['POST'])
@login_required
def sleep_detection():
    """Advanced sleep detection using eye tracking"""
    try:
        if 'face_image' not in request.files:
            return jsonify({'success': False, 'message': 'No image provided'})
        
        face_image = request.files['face_image']
        image_data = face_image.read()
        nparr = np.frombuffer(image_data, np.uint8)
        img_array = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img_array is None:
            return jsonify({'success': False, 'message': 'Invalid image format'})
        
        # Convert to grayscale for eye detection
        gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
        
        # Load Haar cascade for eye detection
        eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        eyes = eye_cascade.detectMultiScale(gray, 1.1, 3)
        
        if len(eyes) == 0:
            # No eyes detected - possible sleep
            return jsonify({
                'success': True, 
                'sleep_detected': True,
                'confidence': 0.9,
                'message': 'No eyes detected - possible sleep'
            })
        elif len(eyes) < 2:
            # Only one eye detected - possible sleep or partial face
            return jsonify({
                'success': True, 
                'sleep_detected': True,
                'confidence': 0.7,
                'message': 'Only one eye detected - possible sleep'
            })
        else:
            # Both eyes detected - check if they're open
            eyes_open = 0
            for (ex, ey, ew, eh) in eyes:
                eye_roi = gray[ey:ey+eh, ex:ex+ew]
                # Simple eye openness detection based on brightness variance
                variance = np.var(eye_roi)
                if variance > 100:  # Threshold for open eyes
                    eyes_open += 1
            
            if eyes_open < 2:
                return jsonify({
                    'success': True, 
                    'sleep_detected': True,
                    'confidence': 0.8,
                    'message': 'Eyes appear closed - possible sleep'
                })
            else:
                return jsonify({
                    'success': True, 
                    'sleep_detected': False,
                    'confidence': 0.9,
                    'message': 'Eyes open - user appears awake'
                })
                
    except Exception as e:
        current_app.logger.error(f"Error in sleep detection: {str(e)}")
        return jsonify({'success': False, 'message': 'Internal server error'})

@monitoring_bp.route('/activity_status')
@login_required
def activity_status():
    """Get current user's activity status"""
    try:
        # Check if user has been active in the last 5 minutes
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
        is_active = current_user.last_activity and current_user.last_activity > five_minutes_ago
        
        # Get work hours today
        work_hours = current_user.get_total_work_hours_today()
        
        return jsonify({
            'success': True,
            'is_active': is_active,
            'work_hours_today': work_hours,
            'last_activity': current_user.last_activity.isoformat() if current_user.last_activity else None,
            'is_online': current_user.is_online
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting activity status: {str(e)}")
        return jsonify({'success': False, 'message': 'Internal server error'})

@monitoring_bp.route('/update_activity', methods=['POST'])
@login_required
def update_activity():
    """Update user's last activity timestamp"""
    try:
        current_user.update_activity()
        return jsonify({'success': True, 'message': 'Activity updated'})
    except Exception as e:
        current_app.logger.error(f"Error updating activity: {str(e)}")
        return jsonify({'success': False, 'message': 'Internal server error'})