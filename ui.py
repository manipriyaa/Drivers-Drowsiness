import cv2
import time
import numpy as np


class UI:
    def __init__(self):

        self.blink_state = True
        self.last_blink = time.time()
        self.blink_interval = 0.5
        
        self.session_start = time.time()

        self.COLORS = {
            "SAFE": (0, 255, 0),           # Green
            "ACTIVE": (0, 255, 0),         # Green
            "DROWSY": (0, 255, 255),       # Yellow
            "TIRED": (0, 200, 255),        # Orange
            "DANGER": (0, 100, 255),       # Dark Orange
            "SLEEPING": (0, 0, 255),       # Red
            "PLEASE STOP VEHICLE": (0, 0, 255),  # Red
            "YAWNING": (0, 255, 255),      # Yellow
            "EYES CLOSING": (0, 165, 255), # Orange
            "WHITE": (255, 255, 255),
            "BLACK": (0, 0, 0),
            "RED": (0, 0, 255),
            "GRAY": (128, 128, 128)
        }

    def draw_text_with_background(self, frame, text, position, font=cv2.FONT_HERSHEY_SIMPLEX,
                                   font_scale=0.7, text_color=(255, 255, 255),
                                   thickness=2, bg_color=(0, 0, 0), padding=5):

        
        x, y = position
        

        (text_width, text_height), baseline = cv2.getTextSize(
            text, font, font_scale, thickness
        )
 
        cv2.rectangle(
            frame,
            (x - padding, y - text_height - padding),
            (x + text_width + padding, y + baseline + padding),
            bg_color,
            -1
        )
        
     
        cv2.putText(
            frame, text, (x, y),
            font, font_scale, text_color, thickness, cv2.LINE_AA
        )
        
        return text_height + baseline + 2 * padding

    def draw_progress_bar(self, frame, label, value, max_value, position, width=200, height=20):

        
        x, y = position
        
    
        progress = min(max(value / max_value, 0), 1)
        
    
        if progress < 0.3:
            bar_color = (0, 255, 0)  
        elif progress < 0.6:
            bar_color = (0, 255, 255)  
        else:
            bar_color = (0, 0, 255) 
     
        cv2.rectangle(frame, (x, y), (x + width, y + height), self.COLORS["GRAY"], -1)

        progress_width = int(width * progress)
        if progress_width > 0:
            cv2.rectangle(frame, (x, y), (x + progress_width, y + height), bar_color, -1)

        cv2.rectangle(frame, (x, y), (x + width, y + height), self.COLORS["WHITE"], 1)
        
 
        label_text = f"{label}: {value:.1f}/{max_value:.0f}"
        self.draw_text_with_background(
            frame, label_text, (x, y - 5),
            font_scale=0.5, thickness=1, padding=3
        )

    def draw_status(self, frame, status, eye_score, yawn_score, fatigue_score):
        """Main status drawing function"""
        
        h, w, _ = frame.shape
        
    
        margin = 20
        panel_width = min(300, w - 2 * margin)
        
        y_offset = 40

        status_color = self.COLORS.get(status, self.COLORS["WHITE"])
        line_height = self.draw_text_with_background(
            frame,
            f"Status: {status}",
            (margin, y_offset),
            font_scale=0.8,
            text_color=status_color,
            thickness=2,
            padding=8
        )
        
        y_offset += line_height + 10

        self.draw_text_with_background(
            frame,
            f"Eye Open: {eye_score:.2f}",
            (margin, y_offset),
            font_scale=0.6,
            thickness=1,
            padding=5
        )
        y_offset += 30
   
        self.draw_text_with_background(
            frame,
            f"Yawn: {yawn_score:.2f}",
            (margin, y_offset),
            font_scale=0.6,
            thickness=1,
            padding=5
        )
        y_offset += 40
        
        
        self.draw_progress_bar(
            frame,
            "Fatigue",
            fatigue_score,
            100,
            (margin, y_offset),
            width=panel_width - 2 * margin
        )
      
        session_time = int(time.time() - self.session_start)
        minutes = session_time // 60
        seconds = session_time % 60
        
        timer_text = f"Session: {minutes:02d}:{seconds:02d}"
        (text_width, _), _ = cv2.getTextSize(
            timer_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1
        )
        
        self.draw_text_with_background(
            frame,
            timer_text,
            (w - text_width - margin - 10, 40),
            font_scale=0.6,
            thickness=1,
            padding=5
        )
        
        if status == "PLEASE STOP VEHICLE" or status == "SLEEPING":
            self._draw_critical_alert(frame, status)

    def _draw_critical_alert(self, frame, status):
        """Draw blinking critical alert overlay"""
        
        h, w, _ = frame.shape
        current_time = time.time()

        if current_time - self.last_blink > self.blink_interval:
            self.blink_state = not self.blink_state
            self.last_blink = current_time
        
        if self.blink_state:
           
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, h), self.COLORS["RED"], -1)
            cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
          
            alert_text = status
            font = cv2.FONT_HERSHEY_DUPLEX
            font_scale = min(2.0, w / 400)  
            thickness = 4
            
            (text_width, text_height), baseline = cv2.getTextSize(
                alert_text, font, font_scale, thickness
            )
            
    
            text_x = (w - text_width) // 2
            text_y = (h + text_height) // 2

            cv2.putText(
                frame, alert_text, (text_x, text_y),
                font, font_scale, self.COLORS["BLACK"], thickness + 4, cv2.LINE_AA
            )
           
            cv2.putText(
                frame, alert_text, (text_x, text_y),
                font, font_scale, self.COLORS["WHITE"], thickness, cv2.LINE_AA
            )
       
            self._draw_warning_triangle(frame, (w // 2, h // 4), size=50)

    def _draw_warning_triangle(self, frame, center, size=40):
        """Draw a warning triangle icon"""
        
        cx, cy = center
        

        points = np.array([
            [cx, cy - size],              
            [cx - size, cy + size // 2],  
            [cx + size, cy + size // 2]   
        ], np.int32)
    
        cv2.fillPoly(frame, [points], self.COLORS["RED"])
        cv2.polylines(frame, [points], True, self.COLORS["WHITE"], 3)

        cv2.putText(
            frame, "!",
            (cx - 10, cy + 15),
            cv2.FONT_HERSHEY_DUPLEX, 1.5,
            self.COLORS["WHITE"], 3, cv2.LINE_AA
        )

    def draw_landmarks(self, frame, points, eye_indices, mouth_indices):
        """Draw facial landmarks"""
     
        for idx in eye_indices:
            if idx < len(points):
                cv2.circle(frame, points[idx], 2, (0, 255, 0), -1)
        
        for idx in mouth_indices:
            if idx < len(points):
                cv2.circle(frame, points[idx], 2, (0, 255, 255), -1)

    def reset_session(self):
        """Reset session timer"""
        self.session_start = time.time()