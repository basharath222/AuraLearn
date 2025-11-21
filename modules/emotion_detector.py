# modules/emotion_detector.py
import cv2
import mediapipe as mp
import numpy as np
import math
import time

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5
)

# Landmark Indices
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]
MOUTH = [61, 291, 0, 17] # Left corner, Right corner, Upper lip, Lower lip

def euclidean(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

def calculate_ear(landmarks, width, height):
    """Eye Aspect Ratio"""
    def get_coords(indices):
        return [np.array([landmarks[i].x * width, landmarks[i].y * height]) for i in indices]

    left_pts = get_coords(LEFT_EYE)
    right_pts = get_coords(RIGHT_EYE)

    def eye_ratio(pts):
        v1 = euclidean(pts[1], pts[5])
        v2 = euclidean(pts[2], pts[4])
        h = euclidean(pts[0], pts[3])
        return (v1 + v2) / (2.0 * h)

    return (eye_ratio(left_pts) + eye_ratio(right_pts)) / 2.0

def get_head_tilt(landmarks, width, height):
    """Head Tilt Angle"""
    left = np.array([landmarks[33].x * width, landmarks[33].y * height])
    right = np.array([landmarks[263].x * width, landmarks[263].y * height])
    dx = right[0] - left[0]
    dy = right[1] - left[1]
    return abs(math.degrees(math.atan2(dy, dx)))

def calculate_smile(landmarks, width, height):
    """Smile Ratio: Distance between mouth corners vs face width"""
    left_mouth = np.array([landmarks[61].x * width, landmarks[61].y * height])
    right_mouth = np.array([landmarks[291].x * width, landmarks[291].y * height])
    
    mouth_width = euclidean(left_mouth, right_mouth)
    
    # Normalize by face width (Ear to Ear approx)
    left_face = np.array([landmarks[234].x * width, landmarks[234].y * height])
    right_face = np.array([landmarks[454].x * width, landmarks[454].y * height])
    face_width = euclidean(left_face, right_face)

    return mouth_width / face_width

def capture_live_mood(duration=3):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return "neutral"

    start_time = time.time()
    emotions_tally = {"sleepy": 0, "confused": 0, "happy": 0, "neutral": 0}
    
    # === TUNABLE THRESHOLDS ===
    SLEEPY_THRESH = 0.24    # Increase if it thinks you are sleeping too often
    CONFUSED_ANGLE = 12     # Decrease to make it more sensitive to tilt
    SMILE_THRESH = 0.45     # Adjust based on testing (Higher = bigger smile needed)

    while time.time() - start_time < duration:
        ret, frame = cap.read()
        if not ret: break
        
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)
        
        detected = "neutral"
        if results.multi_face_landmarks:
            lm = results.multi_face_landmarks[0].landmark
            
            ear = calculate_ear(lm, w, h)
            tilt = get_head_tilt(lm, w, h)
            smile = calculate_smile(lm, w, h)

            if ear < SLEEPY_THRESH:
                detected = "sleepy"
            elif smile > SMILE_THRESH:
                detected = "happy"
            elif tilt > CONFUSED_ANGLE:
                detected = "confused"
            else:
                detected = "neutral"

        emotions_tally[detected] += 1
        
        # UI Overlay on Camera
        cv2.rectangle(frame, (0,0), (w, 60), (0,0,0), -1)
        cv2.putText(frame, f"Detecting: {detected.upper()}", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        
        cv2.imshow("AuraLearn Eye", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()
    return max(emotions_tally, key=emotions_tally.get)