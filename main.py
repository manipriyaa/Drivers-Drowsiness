import cv2
import tensorflow as tf

from camera import Camera
from image_processing import ImageEnhancer
from detectors import FaceDetector
from alert import AlertSystem, AlertLevel  
from ui import UI
from temporal import TemporalModel
from fatigue_scoring import YawnEventDetector
from fatigue_scoring import ImprovedFatigueManager 


try:
    eye_model = tf.keras.models.load_model("eye_model.h5")
    yawn_model = tf.keras.models.load_model("yawn_model.h5")
except Exception as e:
    print(f"AI Model files not found: {e}")
    print("Make sure eye_model.h5 and yawn_model.h5 exist.")
    exit()


eye_temporal = TemporalModel()
yawn_temporal = TemporalModel()

yawn_detector = YawnEventDetector()

fatigue_manager = ImprovedFatigueManager(
    eye_threshold=0.4,              
    consecutive_frames_eye=20,     
    yawn_window_seconds=60,         
    max_yawns_per_minute=3,
    recovery_time=5.0              
)


LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]
MOUTH_FULL = [61, 185, 13, 409, 291, 375, 14, 146]


def crop_region(frame, pts):
    if not pts or len(pts) == 0:
        return None
    
    try:
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]

        x1, x2 = max(min(xs), 0), min(max(xs), frame.shape[1])
        y1, y2 = max(min(ys), 0), min(max(ys), frame.shape[0])

        if x2 <= x1 or y2 <= y1:
            return None

        crop = frame[y1:y2, x1:x2]

        if crop.size == 0:
            return None

        crop = cv2.resize(crop, (64, 64))
        crop = crop / 255.0
        return crop.reshape(1, 64, 64, 3)
    except Exception as e:
        print(f"Crop error: {e}")
        return None


def main():

    try:
        cam = Camera()
    except ValueError as e:
        print(e)
        return

    enhancer = ImageEnhancer()
    detector = FaceDetector()
    alert_system = AlertSystem("alert.wav")
    ui = UI()

    print("✅ System Started. Press 'q' to quit, 'r' to reset.")

    while True:

        frame = cam.get_frame()
        if frame is None:
            break

        processed_frame = enhancer.enhance(frame)
        display_frame = processed_frame.copy()

        face_landmarks = detector.detect(processed_frame)

        status = "SAFE"
        alarm_on = False
        eye_score = 1.0
        yawn_score = 0.0
        fatigue_score = 0.0

        if face_landmarks:

            h, w, _ = display_frame.shape
            points = detector.get_landmarks_points(face_landmarks, w, h)

            left_eye_points = [points[i] for i in LEFT_EYE]
            right_eye_points = [points[i] for i in RIGHT_EYE]
            mouth_points = [points[i] for i in MOUTH_FULL]

            eye_img = crop_region(display_frame, left_eye_points + right_eye_points)
            if eye_img is not None:
                eye_pred = eye_model.predict(eye_img, verbose=0)[0][0]
                eye_score = eye_temporal.update(eye_pred)

            mouth_img = crop_region(display_frame, mouth_points)
            if mouth_img is not None:
                yawn_pred = yawn_model.predict(mouth_img, verbose=0)[0][0]
                yawn_event = yawn_detector.update(yawn_pred)

                if yawn_event:
                    yawn_score = 1.0
                else:
                    yawn_score = yawn_temporal.update(yawn_pred)

            status, alarm_on = fatigue_manager.update(eye_score, yawn_event)
         
            metrics = fatigue_manager.get_metrics()
            fatigue_score = (metrics['danger_streak'] / 3) * 100 
            

            ui.draw_landmarks(
                display_frame,
                points,
                LEFT_EYE + RIGHT_EYE,
                MOUTH_FULL
            )

        else:
            status = "NO FACE"
            fatigue_score = 0.0
            alert_system.stop()

        
        alert_level = fatigue_manager.get_alert_level()
        
        if alert_level == "CRITICAL":
            alert_system.play(AlertLevel.CRITICAL)
        elif alert_level == "DANGER":
            alert_system.play(AlertLevel.DANGER)
        elif alert_level == "WARNING":
            alert_system.play(AlertLevel.WARNING)
        else:
            alert_system.stop()
       
        ui.draw_status(
            display_frame,
            status,
            eye_score,
            yawn_score,
            fatigue_score
        )

        cv2.imshow("Drowsiness Detection", display_frame)

       
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        elif key == ord('r'):
            fatigue_manager.reset()
            ui.reset_session()
            print("✅ System reset")
      

    cam.release()
    alert_system.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()