# fatigue_manager.py
import time
from collections import deque


class ImprovedFatigueManager:
  
    
    def __init__(
        self,
        eye_threshold=0.4,
        consecutive_frames_eye=20,
        yawn_window_seconds=60,
        max_yawns_per_minute=3,
        recovery_time=5.0
    ):
        self.EYE_THRESHOLD = eye_threshold
        self.EYE_CONSEC_FRAMES = consecutive_frames_eye
        
      
        self.YAWN_WINDOW_SECONDS = yawn_window_seconds
        self.MAX_YAWNS_PER_MINUTE = max_yawns_per_minute
        self.yawn_timestamps = deque()
        
        self.counter_eye = 0
        self.consecutive_safe_frames = 0
       
        self.danger_streak = 0
        self.last_danger_time = time.time()
        self.RECOVERY_TIME = recovery_time
        self.DANGER_STREAK_MAX = 3
       
        self.status = "SAFE"
        self.alarm_on = False
        self.stop_required = False
        
        self.session_start = time.time()
        self.total_events = {
            'eye_closures': 0,
            'yawns': 0,
            'danger_alerts': 0
        }

    def update(self, eye_score, yawn_event):
       
        now = time.time()
        
       
        eye_closed = eye_score < self.EYE_THRESHOLD
        
        if eye_closed:
            self.counter_eye += 1
            self.consecutive_safe_frames = 0
        else:
            self.counter_eye = max(0, self.counter_eye - 1)
            self.consecutive_safe_frames += 1
        
        
        if yawn_event:
            self.yawn_timestamps.append(now)
            self.total_events['yawns'] += 1
        
        while self.yawn_timestamps and (now - self.yawn_timestamps[0]) > self.YAWN_WINDOW_SECONDS:
            self.yawn_timestamps.popleft()
        
        yawns_per_minute = len(self.yawn_timestamps) / (self.YAWN_WINDOW_SECONDS / 60)
        
       
        danger_signal = False
        
        if eye_closed or yawn_event:
            danger_signal = True
            self.last_danger_time = now
        else:
            if now - self.last_danger_time > self.RECOVERY_TIME:
                self.danger_streak = max(0, self.danger_streak - 1)
                self.last_danger_time = now
        
        if danger_signal:
            self.danger_streak += 1
        
        self.danger_streak = min(self.danger_streak, 10)
       
        if self.counter_eye >= self.EYE_CONSEC_FRAMES:
            self.status = "SLEEPING"
            self.alarm_on = True
            self.stop_required = True
            self.total_events['danger_alerts'] += 1
            return self.status, self.alarm_on
        
        if self.danger_streak >= self.DANGER_STREAK_MAX:
            self.status = "PLEASE STOP VEHICLE"
            self.alarm_on = True
            self.stop_required = True
            return self.status, self.alarm_on
        
        if yawns_per_minute > self.MAX_YAWNS_PER_MINUTE:
            self.status = "DROWSY - HIGH YAWN RATE"
            self.alarm_on = True
            return self.status, self.alarm_on
      
        if self.counter_eye >= self.EYE_CONSEC_FRAMES * 0.5:
            self.status = "EYES CLOSING"
            self.alarm_on = False
            return self.status, self.alarm_on
        
      
        if self.danger_streak >= 2:
            self.status = "DANGER"
            self.alarm_on = False
            return self.status, self.alarm_on
       
        if len(self.yawn_timestamps) >= 2:
            self.status = "DROWSY"
            self.alarm_on = False
            return self.status, self.alarm_on
        
       
        if self.alarm_on:
            if self.consecutive_safe_frames >= 30:
                self.alarm_on = False
                self.stop_required = False
        
        if self.danger_streak >= 1:
            self.status = "TIRED"
        else:
            self.status = "SAFE"
            
        return self.status, self.alarm_on

    def get_metrics(self):
       
        now = time.time()
        session_duration = now - self.session_start
        
        return {
            "status": self.status,
            "alarm_on": self.alarm_on,
            "stop_required": self.stop_required,
            "eye_counter": self.counter_eye,
            "eye_threshold": self.EYE_CONSEC_FRAMES,
            "danger_streak": self.danger_streak,
            "recent_yawns": len(self.yawn_timestamps),
            "yawns_per_minute": len(self.yawn_timestamps) / (self.YAWN_WINDOW_SECONDS / 60),
            "consecutive_safe_frames": self.consecutive_safe_frames,
            "session_duration": session_duration,
            "total_yawns": self.total_events['yawns'],
            "total_danger_alerts": self.total_events['danger_alerts']
        }

    def reset(self):
  
        self.counter_eye = 0
        self.consecutive_safe_frames = 0
        self.danger_streak = 0
        self.yawn_timestamps.clear()
        self.alarm_on = False
        self.stop_required = False
        self.status = "SAFE"
        self.last_danger_time = time.time()

    def get_alert_level(self):
       
        if self.status in ["SLEEPING", "PLEASE STOP VEHICLE"]:
            return "CRITICAL"
        elif self.status in ["DROWSY - HIGH YAWN RATE", "DANGER"]:
            return "DANGER"
        elif self.status in ["EYES CLOSING", "DROWSY", "TIRED"]:
            return "WARNING"
        else:
            return "NONE"