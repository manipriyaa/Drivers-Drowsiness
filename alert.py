import pygame
import os
import numpy as np
from enum import Enum


class AlertLevel(Enum):

    NONE = 0
    WARNING = 1      
    DANGER = 2      
    CRITICAL = 3    

class AlertSystem:
    def __init__(self, sound_file="alert.wav", fallback_enabled=True):
 
        self.sound_file = sound_file
        self.fallback_enabled = fallback_enabled
        self.has_sound = False
        self.playing = False
        self.current_level = AlertLevel.NONE

        self.volumes = {
            AlertLevel.WARNING: 0.4,
            AlertLevel.DANGER: 0.7,
            AlertLevel.CRITICAL: 1.0
        }
 
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self._load_sounds()
        except pygame.error as e:
            print(f"⚠️ Failed to initialize audio system: {e}")
            self.has_sound = False

    def _load_sounds(self):
    
        
        self.sounds = {}

        if os.path.exists(self.sound_file):
            try:
                base_sound = pygame.mixer.Sound(self.sound_file)
              
                self.sounds[AlertLevel.WARNING] = base_sound
                self.sounds[AlertLevel.DANGER] = base_sound
                self.sounds[AlertLevel.CRITICAL] = base_sound
                
                self.has_sound = True
                print(f"✅ Loaded alert sound: {self.sound_file}")
                
            except pygame.error as e:
                print(f"⚠️ Failed to load {self.sound_file}: {e}")
                self._generate_fallback_sounds()
        else:
            print(f"⚠️ Sound file not found: {self.sound_file}")
            self._generate_fallback_sounds()

    def _generate_fallback_sounds(self):
  
        
        if not self.fallback_enabled:
            print("❌ Fallback sounds disabled. Audio system inactive.")
            return
        
        try:
            sample_rate = 22050
            
            self.sounds[AlertLevel.WARNING] = self._generate_beep(
                frequency=440, duration=0.2, sample_rate=sample_rate
            )
           
            beep1 = self._generate_beep(880, 0.15, sample_rate)
            silence = self._generate_silence(0.1, sample_rate)
            beep2 = self._generate_beep(880, 0.15, sample_rate)
            self.sounds[AlertLevel.DANGER] = self._combine_sounds([beep1, silence, beep2])
 
            self.sounds[AlertLevel.CRITICAL] = self._generate_siren(
                freq1=800, freq2=1000, duration=1.0, sample_rate=sample_rate
            )
            
            self.has_sound = True
            print("✅ Generated synthetic alert sounds")
            
        except Exception as e:
            print(f"❌ Failed to generate fallback sounds: {e}")
            self.has_sound = False

    def _generate_beep(self, frequency, duration, sample_rate):

        
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples, False)
        
 
        wave = np.sin(2 * np.pi * frequency * t)
        
        fade_len = int(sample_rate * 0.01)  # 10ms fade
        fade_in = np.linspace(0, 1, fade_len)
        fade_out = np.linspace(1, 0, fade_len)
        
        wave[:fade_len] *= fade_in
        wave[-fade_len:] *= fade_out
        
        wave = (wave * 32767).astype(np.int16)
        
        stereo = np.zeros((samples, 2), dtype=np.int16)
        stereo[:, 0] = wave
        stereo[:, 1] = wave
        
        return pygame.sndarray.make_sound(stereo)

    def _generate_siren(self, freq1, freq2, duration, sample_rate):
        """Generate an alternating siren sound"""
        
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples, False)
   
        freq_mod = freq1 + (freq2 - freq1) * (np.sin(2 * np.pi * 2 * t) + 1) / 2
        
        # Generate wave with varying frequency
        phase = np.cumsum(2 * np.pi * freq_mod / sample_rate)
        wave = np.sin(phase)
        
        # Convert to 16-bit
        wave = (wave * 32767).astype(np.int16)
        
        # Stereo
        stereo = np.zeros((samples, 2), dtype=np.int16)
        stereo[:, 0] = wave
        stereo[:, 1] = wave
        
        return pygame.sndarray.make_sound(stereo)

    def _generate_silence(self, duration, sample_rate):
        """Generate silence"""
        
        samples = int(sample_rate * duration)
        stereo = np.zeros((samples, 2), dtype=np.int16)
        return pygame.sndarray.make_sound(stereo)

    def _combine_sounds(self, sound_list):
        """Combine multiple pygame sounds into one"""
        
        # Convert sounds to arrays and concatenate
        arrays = [pygame.sndarray.array(sound) for sound in sound_list]
        combined = np.concatenate(arrays, axis=0)
        return pygame.sndarray.make_sound(combined)

    def play(self, level=AlertLevel.CRITICAL):
        """
        Play alert at specified level.
        
        Args:
            level: AlertLevel enum (WARNING, DANGER, or CRITICAL)
        """
        
        if not self.has_sound:
            # Fallback to console alert
            print(f"🚨 ALERT: {level.name}")
            return
        
        # If already playing at this level, do nothing
        if self.playing and self.current_level == level:
            return
        
        # Stop current sound if different level
        if self.playing and self.current_level != level:
            self.stop()
        
        # Play new sound
        if level in self.sounds:
            try:
                sound = self.sounds[level]
                sound.set_volume(self.volumes[level])
                
                # Loop critical alerts, play once for others
                loops = -1 if level == AlertLevel.CRITICAL else 0
                sound.play(loops=loops)
                
                self.playing = True
                self.current_level = level
                
            except pygame.error as e:
                print(f"⚠️ Error playing sound: {e}")

    def stop(self):
        """Stop all alerts"""
        
        if self.has_sound and self.playing:
            try:
                pygame.mixer.stop()
                self.playing = False
                self.current_level = AlertLevel.NONE
            except pygame.error as e:
                print(f"⚠️ Error stopping sound: {e}")

    def set_volume(self, level, volume):
        """
        Set volume for specific alert level.
        
        Args:
            level: AlertLevel enum
            volume: Float between 0.0 and 1.0
        """
        
        volume = max(0.0, min(1.0, volume))  # Clamp to valid range
        self.volumes[level] = volume
        
        # Update if currently playing
        if self.playing and self.current_level == level and level in self.sounds:
            self.sounds[level].set_volume(volume)

    def test_all_levels(self):
        """Test all alert levels (for debugging/setup)"""
        
        import time
        
        print("\n🔊 Testing alert levels...")
        
        for level in [AlertLevel.WARNING, AlertLevel.DANGER, AlertLevel.CRITICAL]:
            print(f"Playing: {level.name}")
            self.play(level)
            time.sleep(2)
            self.stop()
            time.sleep(0.5)
        
        print("✅ Test complete\n")

    def cleanup(self):
        """Clean up pygame mixer"""
        
        self.stop()
        try:
            pygame.mixer.quit()
        except:
            pass