#!/usr/bin/env python3
"""
Face recognition utilities using DeepFace
"""

import base64
import io
import numpy as np
from PIL import Image
import cv2
import os
import tempfile

try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    print("DeepFace not installed. Install with: pip install deepface")

def base64_to_image(base64_string):
    """Convert base64 string to PIL Image"""
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

def extract_face_encoding(face_data):
    """Extract face encoding from base64 image data using DeepFace"""
    if not DEEPFACE_AVAILABLE:
        print("DeepFace not available")
        return None
    
    try:
        # Convert base64 to image
        image = base64_to_image(face_data)
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
            embedding = DeepFace.represent(
                img_path=temp_path,
                model_name='VGG-Face',  # You can use 'Facenet', 'OpenFace', 'DeepFace', 'DeepID', 'ArcFace', 'Dlib'
                enforce_detection=True
            )
            
            # DeepFace.represent returns a list of dictionaries
            if embedding and len(embedding) > 0:
                face_encoding = embedding[0]['embedding']
                return face_encoding
            else:
                print("No face detected in image")
                return None
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except Exception as e:
        print(f"Error extracting face encoding: {str(e)}")
        return None

def verify_faces(face_data1, face_data2, threshold=0.6):
    """Verify if two face images are of the same person using DeepFace"""
    if not DEEPFACE_AVAILABLE:
        print("DeepFace not available")
        return False
    
    try:
        # Convert both images
        image1 = base64_to_image(face_data1)
        image2 = base64_to_image(face_data2)
        
        if image1 is None or image2 is None:
            return False
        
        # Convert to numpy arrays
        img_array1 = image_to_numpy(image1)
        img_array2 = image_to_numpy(image2)
        
        if img_array1 is None or img_array2 is None:
            return False
        
        # Save to temporary files
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file1:
            cv2.imwrite(temp_file1.name, img_array1)
            temp_path1 = temp_file1.name
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file2:
            cv2.imwrite(temp_file2.name, img_array2)
            temp_path2 = temp_file2.name
        
        try:
            # Verify faces using DeepFace
            result = DeepFace.verify(
                img1_path=temp_path1,
                img2_path=temp_path2,
                model_name='VGG-Face',
                enforce_detection=True,
                distance_metric='cosine'
            )
            
            # Check if faces match
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
        print(f"Error verifying faces: {str(e)}")
        return False

def detect_face(face_data):
    """Detect if there's a face in the image"""
    if not DEEPFACE_AVAILABLE:
        print("DeepFace not available")
        return False
    
    try:
        # Convert base64 to image
        image = base64_to_image(face_data)
        if image is None:
            return False
        
        # Convert to numpy array
        img_array = image_to_numpy(image)
        if img_array is None:
            return False
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            cv2.imwrite(temp_file.name, img_array)
            temp_path = temp_file.name
        
        try:
            # Try to extract face - if successful, face exists
            embedding = DeepFace.represent(
                img_path=temp_path,
                model_name='VGG-Face',
                enforce_detection=True
            )
            
            return len(embedding) > 0
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except Exception as e:
        print(f"No face detected: {str(e)}")
        return False

def get_face_quality_score(face_data):
    """Get a quality score for the face image (0-1, higher is better)"""
    try:
        # Convert base64 to image
        image = base64_to_image(face_data)
        if image is None:
            return 0.0
        
        # Convert to numpy array
        img_array = image_to_numpy(image)
        if img_array is None:
            return 0.0
        
        # Basic quality checks
        height, width = img_array.shape[:2]
        
        # Size check (prefer larger images)
        size_score = min(1.0, (width * height) / (300 * 300))
        
        # Brightness check (avoid too dark or too bright)
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
        return 0.0