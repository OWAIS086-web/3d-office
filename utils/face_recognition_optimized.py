#!/usr/bin/env python3
"""
Optimized face recognition utilities with caching and lazy loading
"""

import base64
import io
import numpy as np
from PIL import Image
import cv2
import os
import tempfile
import threading
import time
from functools import lru_cache

# Global variables for model caching
_deepface_loaded = False
_deepface_lock = threading.Lock()
_deepface_module = None

def lazy_load_deepface():
    """Lazy load DeepFace only when needed"""
    global _deepface_loaded, _deepface_module
    
    if _deepface_loaded:
        return _deepface_module
    
    with _deepface_lock:
        if _deepface_loaded:
            return _deepface_module
        
        try:
            # Set TensorFlow to be less verbose
            os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
            
            # Import DeepFace
            from deepface import DeepFace
            _deepface_module = DeepFace
            _deepface_loaded = True
            
            print("✅ DeepFace loaded successfully")
            return _deepface_module
            
        except ImportError:
            print("❌ DeepFace not available. Install with: pip install deepface")
            return None
        except Exception as e:
            print(f"❌ Error loading DeepFace: {e}")
            return None

@lru_cache(maxsize=128)
def base64_to_image_cached(base64_string):
    """Convert base64 string to PIL Image with caching"""
    try:
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Decode base64
        image_data = base64.b64decode(base64_string)
        
        # Convert to PIL Image
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        return image
    except Exception as e:
        print(f"Error converting base64 to image: {str(e)}")
        return None

def image_to_numpy(image):
    """Convert PIL Image to numpy array for OpenCV"""
    try:
        # Convert PIL to numpy array
        img_array = np.array(image)
        
        # Convert RGB to BGR for OpenCV
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        return img_bgr
    except Exception as e:
        print(f"Error converting image to numpy: {str(e)}")
        return None

def extract_face_encoding_optimized(face_data):
    """Extract face encoding with optimized loading"""
    deepface = lazy_load_deepface()
    if not deepface:
        return None
    
    try:
        # Convert base64 to image
        image = base64_to_image_cached(face_data)
        if image is None:
            return None
        
        # Convert to numpy array
        img_array = image_to_numpy(image)
        if img_array is None:
            return None
        
        # Save to temporary file for DeepFace
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            cv2.imwrite(temp_file.name, img_array)
            temp_path = temp_file.name
        
        try:
            # Extract face embedding using DeepFace
            embedding = deepface.represent(
                img_path=temp_path,
                model_name='VGG-Face',
                enforce_detection=True
            )
            
            if embedding and len(embedding) > 0:
                face_encoding = embedding[0]['embedding']
                return face_encoding
            else:
                return None
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except Exception as e:
        print(f"Error extracting face encoding: {str(e)}")
        return None

def verify_faces_optimized(face_data1, face_data2, threshold=0.6):
    """Verify faces with optimized loading and basic fallback"""
    deepface = lazy_load_deepface()
    
    # If DeepFace is not available, use basic comparison
    if not deepface:
        return basic_face_comparison(face_data1, face_data2)
    
    try:
        # Convert both images
        image1 = base64_to_image_cached(face_data1)
        image2 = base64_to_image_cached(face_data2)
        
        if image1 is None or image2 is None:
            return basic_face_comparison(face_data1, face_data2)
        
        # Convert to numpy arrays
        img_array1 = image_to_numpy(image1)
        img_array2 = image_to_numpy(image2)
        
        if img_array1 is None or img_array2 is None:
            return basic_face_comparison(face_data1, face_data2)
        
        # Save to temporary files
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file1:
            cv2.imwrite(temp_file1.name, img_array1)
            temp_path1 = temp_file1.name
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file2:
            cv2.imwrite(temp_file2.name, img_array2)
            temp_path2 = temp_file2.name
        
        try:
            # Verify faces using DeepFace
            result = deepface.verify(
                img1_path=temp_path1,
                img2_path=temp_path2,
                model_name='VGG-Face',
                enforce_detection=True,
                distance_metric='cosine'
            )
            
            is_verified = result['verified']
            distance = result['distance']
            
            print(f"Face verification result: {is_verified}, distance: {distance:.4f}")
            return is_verified
            
        finally:
            # Clean up temporary files
            if os.path.exists(temp_path1):
                os.unlink(temp_path1)
            if os.path.exists(temp_path2):
                os.unlink(temp_path2)
        
    except Exception as e:
        print(f"DeepFace verification failed, using fallback: {str(e)}")
        return basic_face_comparison(face_data1, face_data2)

def basic_face_comparison(stored_data, face_data):
    """Fallback basic face comparison"""
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
        
        # Basic similarity check
        if abs(len(current_b64) - len(stored_b64)) > len(stored_b64) * 0.3:
            return False
        
        # Compare sample bytes
        sample_size = min(100, len(current_b64), len(stored_b64))
        current_sample = current_b64[:sample_size]
        stored_sample = stored_b64[:sample_size]
        
        matches = sum(1 for a, b in zip(current_sample, stored_sample) if a == b)
        similarity = matches / sample_size
        
        print(f"Basic face similarity: {similarity:.2f}")
        return similarity >= 0.8
        
    except Exception as e:
        print(f"Basic face comparison error: {str(e)}")
        return False

def detect_face_optimized(face_data):
    """Detect face with optimized loading"""
    deepface = lazy_load_deepface()
    
    # If DeepFace not available, do basic checks
    if not deepface:
        return basic_face_detection(face_data)
    
    try:
        image = base64_to_image_cached(face_data)
        if image is None:
            return False
        
        img_array = image_to_numpy(image)
        if img_array is None:
            return False
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            cv2.imwrite(temp_file.name, img_array)
            temp_path = temp_file.name
        
        try:
            embedding = deepface.represent(
                img_path=temp_path,
                model_name='VGG-Face',
                enforce_detection=True
            )
            return len(embedding) > 0
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except Exception as e:
        print(f"Face detection failed, using basic check: {str(e)}")
        return basic_face_detection(face_data)

def basic_face_detection(face_data):
    """Basic face detection using OpenCV"""
    try:
        image = base64_to_image_cached(face_data)
        if image is None:
            return False
        
        # Convert to grayscale for face detection
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Use OpenCV's built-in face detector
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        return len(faces) > 0
        
    except Exception as e:
        print(f"Basic face detection error: {str(e)}")
        # If all else fails, assume there's a face if image is valid
        return face_data and len(face_data) > 100

def get_face_quality_score_optimized(face_data):
    """Get face quality score with optimizations"""
    try:
        image = base64_to_image_cached(face_data)
        if image is None:
            return 0.0
        
        img_array = image_to_numpy(image)
        if img_array is None:
            return 0.0
        
        height, width = img_array.shape[:2]
        
        # Size check
        size_score = min(1.0, (width * height) / (300 * 300))
        
        # Brightness check
        gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        brightness_score = 1.0 - abs(brightness - 128) / 128
        
        # Contrast check
        contrast = np.std(gray)
        contrast_score = min(1.0, contrast / 50)
        
        # Overall quality score
        quality_score = (size_score + brightness_score + contrast_score) / 3
        return quality_score
        
    except Exception as e:
        print(f"Error calculating face quality: {str(e)}")
        return 0.5  # Return neutral score on error

# Compatibility functions for existing code
def detect_face(face_data):
    """Compatibility wrapper"""
    return detect_face_optimized(face_data)

def verify_faces(face_data1, face_data2, threshold=0.6):
    """Compatibility wrapper"""
    return verify_faces_optimized(face_data1, face_data2, threshold)

def extract_face_encoding(face_data):
    """Compatibility wrapper"""
    return extract_face_encoding_optimized(face_data)

def get_face_quality_score(face_data):
    """Compatibility wrapper"""
    return get_face_quality_score_optimized(face_data)