import cv2
class Camera:
    def __init__(self, source=0):
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            raise ValueError("Could not open video source")
    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame
    def release(self):
        self.cap.release()
