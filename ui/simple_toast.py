import pygame
import time
from utils.constants import WHITE

class SimpleToast:
    """A simple temporary notification message that appears and fades out."""
    
    def __init__(self, message, duration=2.0, position="bottom", text_color=WHITE, bg_color=(0, 0, 0, 180)):
        self.message = message
        self.duration = duration
        self.position = position
        self.text_color = text_color
        self.bg_color = bg_color
        self.start_time = time.time()
        self.elapsed = 0.0
        self.alpha = 255
        self.font = pygame.font.Font(None, 24)
        
        # Pre-render text
        self.text_surface = self.font.render(message, True, text_color)
        self.width = self.text_surface.get_width() + 20  # 10px padding on each side
        self.height = self.text_surface.get_height() + 20  # 10px padding on each side
        
        # Create background surface with alpha
        self.bg_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Set initial position (will be updated in draw)
        self.x = 0
        self.y = 0
        
    @property
    def done(self):
        """Check if the toast is done and should be removed."""
        return self.elapsed >= self.duration
    
    def update(self, dt):
        """Update the toast state and alpha."""
        self.elapsed += dt
        
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