import time
from collections import deque


class ImprovedFatigueManager:
    """
    Unified fatigue detection combining ML predictions with robust state tracking.
    Works with ML model outputs (0-1 predictions) instead of geometric ratios.
    """
    
    def __init__(
        self,
        eye_threshold=0.4,           # Threshold for ML eye closure prediction
        yawn_threshold=0.75,         # Threshold for ML yawn prediction
        consecutive_frames_eye=20,   # Frames to trigger SLEEPING
        yawn_window_seconds=60,      # Window for tracking yawn frequency
        max_yawns_per_minute=3,      # Max acceptable yawn rate
        recovery_time=5.0            # Seconds of safety before recovery
    ):
        # Thresholds for ML predictions
        self.EYE_THRESHOLD = eye_threshold
        self.YAWN_THRESHOLD = yawn_threshold
        self.EYE_CONSEC_FRAMES = consecutive_frames_eye
        
        # Yawn frequency tracking
        self.YAWN_WINDOW_SECONDS = yawn_window_seconds
        self.MAX_YAWNS_PER_MINUTE = max_yawns_per_minute
        self.yawn_timestamps = deque()
        
        # Counters
        self.counter_eye = 0
        self.consecutive_safe_frames = 0
        
        # Danger streak for critical alerts
        self.danger_streak = 0
        self.last_danger_time = time.time()
        self.RECOVERY_TIME = recovery_time
        self.DANGER_STREAK_MAX = 3
        
        # State
        self.status = "SAFE"
        self.alarm_on = False
        self.stop_required = False
        
        # Metrics
        self.session_start = time.time()
        self.total_events = {
            'eye_closures': 0,
            'yawns': 0,
            'danger_alerts': 0
        }

    def update(self, eye_score, yawn_event):
        """
        Update fatigue state based on ML predictions.
        
        Args:
            eye_score: ML prediction for eye openness (0=closed, 1=open)
            yawn_event: Boolean indicating yawn detected by YawnEventDetector
            
        Returns:
            (status, alarm_on) tuple
        """
        now = time.time()
        
        # --- Eye Closure Detection ---
        eye_closed = eye_score < self.EYE_THRESHOLD
        
        if eye_closed:
            self.counter_eye += 1
            self.consecutive_safe_frames = 0
        else:
            # Gradual decay to prevent flickering
            self.counter_eye = max(0, self.counter_eye - 1)
            self.consecutive_safe_frames += 1
        
        # --- Yawn Event Tracking ---
        if yawn_event:
            self.yawn_timestamps.append(now)
            self.total_events['yawns'] += 1
        
        # Clean old yawn timestamps (sliding window)
        while self.yawn_timestamps and (now - self.yawn_timestamps[0]) > self.YAWN_WINDOW_SECONDS:
            self.yawn_timestamps.popleft()
        
        # Calculate yawn frequency
        yawns_per_minute = len(self.yawn_timestamps) / (self.YAWN_WINDOW_SECONDS / 60)
        
        # --- Danger Streak Logic ---
        danger_signal = False
        
        # Triggers for danger
        if eye_closed or yawn_event:
            danger_signal = True
            self.last_danger_time = now
        else:
            # Allow recovery if safe long enough
            if now - self.last_danger_time > self.RECOVERY_TIME:
                self.danger_streak = max(0, self.danger_streak - 1)
                self.last_danger_time = now
        
        # Update streak
        if danger_signal:
            self.danger_streak += 1
        else:
            # Only decay during recovery window
            pass
        
        # Cap streak
        self.danger_streak = min(self.danger_streak, 10)
        
        # --- State Machine (Priority Order) ---
        
        # 1. CRITICAL: Extended eye closure
        if self.counter_eye >= self.EYE_CONSEC_FRAMES:
            self.status = "SLEEPING"
            self.alarm_on = True
            self.stop_required = True
            self.total_events['danger_alerts'] += 1
            return self.status, self.alarm_on
        
        # 2. CRITICAL: Excessive danger streak
        if self.danger_streak >= self.DANGER_STREAK_MAX:
            self.status = "PLEASE STOP VEHICLE"
            self.alarm_on = True
            self.stop_required = True
            return self.status, self.alarm_on
        
        # 3. HIGH ALERT: Too many yawns
        if yawns_per_minute > self.MAX_YAWNS_PER_MINUTE:
            self.status = "DROWSY - HIGH YAWN RATE"
            self.alarm_on = True
            return self.status, self.alarm_on
        
        # 4. WARNING: Eyes closing (50% threshold)
        if self.counter_eye >= self.EYE_CONSEC_FRAMES * 0.5:
            self.status = "EYES CLOSING"
            self.alarm_on = False
            return self.status, self.alarm_on
        
        # 5. WARNING: Moderate danger streak
        if self.danger_streak >= 2:
            self.status = "DANGER"
            self.alarm_on = False
            return self.status, self.alarm_on
        
        # 6. WARNING: Some recent yawns
        if len(self.yawn_timestamps) >= 2:
            self.status = "DROWSY"
            self.alarm_on = False
            return self.status, self.alarm_on
        
        # 7. Safe state with hysteresis
        if self.alarm_on:
            # Keep alarm on briefly to prevent flickering
            if self.consecutive_safe_frames >= 30:  # ~1 second at 30fps
                self.alarm_on = False
                self.stop_required = False
        
        if self.danger_streak >= 1:
            self.status = "TIRED"
        else:
            self.status = "SAFE"
            
        return self.status, self.alarm_on

    def get_metrics(self):
        """Return comprehensive metrics"""
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
            "total_eye_closures": self.total_events['eye_closures'],
            "total_danger_alerts": self.total_events['danger_alerts']
        }

    def reset(self):
        """Reset tracking - use when driver takes break"""
        self.counter_eye = 0
        self.consecutive_safe_frames = 0
        self.danger_streak = 0
        self.yawn_timestamps.clear()
        self.alarm_on = False
        self.stop_required = False
        self.status = "SAFE"
        self.last_danger_time = time.time()
        
        # Don't reset session_start or total_events - those are cumulative

    def get_alert_level(self):
        """Get appropriate alert level for AlertSystem"""
        if self.status in ["SLEEPING", "PLEASE STOP VEHICLE"]:
            return "CRITICAL"
        elif self.status in ["DROWSY - HIGH YAWN RATE", "DANGER"]:
            return "DANGER"
        elif self.status in ["EYES CLOSING", "DROWSY", "TIRED"]:
            return "WARNING"
        else:
            return "NONE"