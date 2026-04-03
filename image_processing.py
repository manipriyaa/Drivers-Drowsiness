import cv2
import numpy as np
class ImageEnhancer:
    def __init__(self):
      
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    def enhance(self, frame):
      
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        
       
        l, a, b = cv2.split(lab)
       
        cl = self.clahe.apply(l)
      
        limg = cv2.merge((cl, a, b))
        
     
        enhanced_frame = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        
        return enhanced_frame
