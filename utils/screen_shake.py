import random
import math
from typing import Tuple

class ScreenShake:
    def __init__(self):
        """Initialize screen shake effect."""
        self.duration = 0  # Duration of the effect in seconds
        self.intensity = 0  # Maximum shake offset in pixels
        self.falloff = 1.5  # How quickly the shake effect diminishes (higher = faster)
        self.offset = (0, 0)  # Current shake offset
    
    def start(self, duration: float, intensity: float, falloff: float = 1.5) -> None:
        """
        Start a screen shake effect.
        
        Args:
            duration: How long the effect should last in seconds
            intensity: Maximum shake offset in pixels
            falloff: How quickly the shake effect diminishes (higher = faster)
        """
        # Only set new values if they are more intense than current ones
        if intensity > self.intensity or duration > self.duration:
            self.duration = duration
            self.intensity = intensity
            self.falloff = falloff
    
    def update(self, dt: float) -> None:
        """
        Update screen shake effect.
        
        Args:
            dt: Delta time in seconds
        """
        if self.duration > 0:
            # Decrease duration
            self.duration -= dt
            
            if self.duration <= 0:
                # Effect is over
                self.duration = 0
                self.intensity = 0
                self.offset = (0, 0)
            else:
                # Calculate current intensity based on remaining duration and falloff
                current_intensity = self.intensity * pow(self.duration, self.falloff)
                
                # Calculate random offset
                angle = random.uniform(0, math.pi * 2)
                distance = random.uniform(0, current_intensity)
                offset_x = math.cos(angle) * distance
                offset_y = math.sin(angle) * distance
                
                self.offset = (offset_x, offset_y)
    
    def get_offset(self) -> Tuple[float, float]:
        """
        Get the current screen shake offset.
        
        Returns:
            (x, y) offset to apply to all screen elements
        """
        return self.offset
    
    def is_active(self) -> bool:
        """
        Check if screen shake effect is active.
        
        Returns:
            True if screen shake is active, False otherwise
        """
        return self.duration > 0 