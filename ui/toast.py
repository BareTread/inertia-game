import pygame
import time
from utils.constants import WHITE

class Toast:
    """A temporary notification message that appears and fades out."""
    
    def __init__(self, message, duration=2.0, font=None, text_color=WHITE, 
                 bg_color=(0, 0, 0, 180), padding=10, position="bottom"):
        self.message = message
        self.duration = duration
        self.font = font or pygame.font.Font(None, 24)
        self.text_color = text_color
        self.bg_color = bg_color
        self.padding = padding
        self.position = position
        self.start_time = time.time()
        self.alpha = 255
        self.elapsed = 0.0  # Track elapsed time directly
        
        # Pre-render text
        self.text_surface = self.font.render(message, True, text_color)
        self.width = self.text_surface.get_width() + padding * 2
        self.height = self.text_surface.get_height() + padding * 2
        
        # Create background surface with alpha
        self.bg_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Set initial position (will be updated in draw)
        self.x = 0
        self.y = 0
    
    @property
    def done(self):
        """Property to check if the toast is done and should be removed."""
        return self.should_remove()
    
    def update(self, dt=None):
        """Update the toast state and alpha.
        
        Args:
            dt: Delta time in seconds since the last update.
               If None, uses system time difference.
        """
        if dt is not None:
            # Use provided delta time to update elapsed
            self.elapsed += dt
        else:
            # Fallback to original time calculation
            self.elapsed = time.time() - self.start_time
        
        # Fade in for the first 0.3 seconds
        if self.elapsed < 0.3:
            self.alpha = int(255 * (self.elapsed / 0.3))
        # Maintain full opacity for the middle portion
        elif self.elapsed < self.duration - 0.5:
            self.alpha = 255
        # Fade out for the last 0.5 seconds
        else:
            remaining = self.duration - self.elapsed
            self.alpha = int(255 * (remaining / 0.5))
            if self.alpha < 0:
                self.alpha = 0
    
    def draw(self, surface):
        """Draw the toast on the given surface."""
        # Update position based on surface size and position preference
        if self.position == "bottom":
            self.x = surface.get_width() // 2 - self.width // 2
            self.y = surface.get_height() - self.height - 20
        elif self.position == "top":
            self.x = surface.get_width() // 2 - self.width // 2
            self.y = 20
        elif self.position == "center":
            self.x = surface.get_width() // 2 - self.width // 2
            self.y = surface.get_height() // 2 - self.height // 2
        
        # Clear the background surface
        self.bg_surface.fill((0, 0, 0, 0))
        
        # Draw background with current alpha
        bg_color_with_alpha = (*self.bg_color[:3], int(self.bg_color[3] * self.alpha / 255))
        pygame.draw.rect(self.bg_surface, bg_color_with_alpha, (0, 0, self.width, self.height), border_radius=5)
        
        # Draw text with current alpha
        text_color_with_alpha = (*self.text_color[:3], self.alpha)
        text_surface = self.font.render(self.message, True, text_color_with_alpha)
        text_rect = text_surface.get_rect(center=(self.width//2, self.height//2))
        self.bg_surface.blit(text_surface, text_rect)
        
        # Draw the toast on the main surface
        surface.blit(self.bg_surface, (self.x, self.y))
    
    def should_remove(self):
        """Check if the toast should be removed."""
        return self.elapsed > self.duration 