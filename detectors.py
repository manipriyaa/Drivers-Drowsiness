import cv2
import mediapipe as mp
import numpy as np
class FaceDetector:
    def __init__(self, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
    def detect(self, frame):
        results = self.face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        if not results.multi_face_landmarks:
            return None
        
        return results.multi_face_landmarks[0] 
    def get_landmarks_points(self, face_landmarks, frame_w, frame_h):
    
        points = []
        for lm in face_landmarks.landmark:
            x, y = int(lm.x * frame_w), int(lm.y * frame_h)
            points.append((x, y))
        return points