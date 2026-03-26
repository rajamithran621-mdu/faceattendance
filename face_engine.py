import cv2
import numpy as np
import os
import json
from PIL import Image

BASE_DIR = os.path.dirname(__file__)
FACES_DIR = os.path.join(BASE_DIR, 'faces')
MODEL_PATH = os.path.join(BASE_DIR, 'face_model.yml')
LABELS_PATH = os.path.join(BASE_DIR, 'face_labels.json')

# Ensure faces directory exists
os.makedirs(FACES_DIR, exist_ok=True)

# Load Haar Cascade for face detection
CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

def detect_face(image):
    """Detect face in an image and return the face region."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
    )
    if len(faces) == 0:
        return None, None
    # Return the largest face
    (x, y, w, h) = max(faces, key=lambda f: f[2] * f[3])
    face_roi = gray[y:y+h, x:x+w]
    return face_roi, (x, y, w, h)

def save_face_image(student_id, image_data):
    """Save a face image for a student from base64 decoded bytes."""
    student_dir = os.path.join(FACES_DIR, str(student_id))
    os.makedirs(student_dir, exist_ok=True)

    # Convert bytes to numpy array
    nparr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return None

    # Detect face
    face_roi, coords = detect_face(img)
    if face_roi is None:
        # Save original image anyway  
        img_count = len(os.listdir(student_dir))
        img_path = os.path.join(student_dir, f'face_{img_count}.jpg')
        cv2.imwrite(img_path, img)
        return img_path

    # Save the cropped face
    img_count = len(os.listdir(student_dir))
    img_path = os.path.join(student_dir, f'face_{img_count}.jpg')
    cv2.imwrite(img_path, face_roi)
    return img_path

def train_model():
    """Train the LBPH face recognizer with all stored faces."""
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    faces = []
    labels = []
    label_map = {}

    for student_id_str in os.listdir(FACES_DIR):
        student_dir = os.path.join(FACES_DIR, student_id_str)
        if not os.path.isdir(student_dir):
            continue

        try:
            student_id = int(student_id_str)
        except ValueError:
            continue

        label_map[student_id] = student_id_str

        for img_file in os.listdir(student_dir):
            img_path = os.path.join(student_dir, img_file)
            try:
                pil_img = Image.open(img_path).convert('L')  # grayscale
                img_array = np.array(pil_img, 'uint8')
                # Resize to standard size
                img_array = cv2.resize(img_array, (200, 200))
                faces.append(img_array)
                labels.append(student_id)
            except Exception:
                continue

    if len(faces) == 0:
        return False

    recognizer.train(faces, np.array(labels))
    recognizer.write(MODEL_PATH)

    with open(LABELS_PATH, 'w') as f:
        json.dump(label_map, f)

    return True

def recognize_face(image_data):
    """Recognize a face from image data. Returns (student_id, confidence) or (None, None)."""
    if not os.path.exists(MODEL_PATH):
        return None, None

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(MODEL_PATH)

    # Decode image
    nparr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return None, None

    face_roi, coords = detect_face(img)
    if face_roi is None:
        return None, None

    # Resize to match training size
    face_roi = cv2.resize(face_roi, (200, 200))

    student_id, confidence = recognizer.predict(face_roi)

    # Lower confidence = better match in LBPH. Threshold ~80
    if confidence < 80:
        return student_id, confidence
    else:
        return None, confidence

def get_all_face_images(student_id):
    """Get list of face image paths for a student."""
    student_dir = os.path.join(FACES_DIR, str(student_id))
    if not os.path.exists(student_dir):
        return []
    return [os.path.join(student_dir, f) for f in os.listdir(student_dir) if f.endswith('.jpg')]

def delete_face_images(student_id):
    """Delete all face images for a student."""
    student_dir = os.path.join(FACES_DIR, str(student_id))
    if os.path.exists(student_dir):
        import shutil
        shutil.rmtree(student_dir)
