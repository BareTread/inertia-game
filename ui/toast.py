import pygame
from typing import Tuple, Optional

class Toast:
    """A temporary notification message that appears and fades out."""
    
    def __init__(self, message: str, duration: float = 3.0, color: Tuple[int, int, int] = (255, 255, 255), 
                 bg_color: Optional[Tuple[int, int, int]] = None, font_size: int = 24):
        """
        Initialize a toast notification.
        
        Args:
            message: Text to display
            duration: How long to display the toast in seconds
            color: Text color (RGB)
            bg_color: Background color (RGB) or None for transparent black
            font_size: Font size
        """
        self.message = message
        self.duration = duration
        self.time_remaining = duration
        self.color = color
        self.bg_color = bg_color or (0, 0, 0, 200)  # Transparent black by default
        self.font_size = font_size
        self.font = pygame.font.Font(None, font_size)
        self.alpha = 255  # Opacity for fade effects
        
        # Pre-render text to get dimensions
        self._update_text_surface()
    
    def _update_text_surface(self) -> None:
        """Update the text surface with current message and color."""
        self.text_surface = self.font.render(self.message, True, self.color)
        self.text_rect = self.text_surface.get_rect()
        
        # Calculate padding and toast dimensions
        self.padding = 10
        self.width = self.text_rect.width + self.padding * 2
        self.height = self.text_rect.height + self.padding * 2
    
    def update(self, dt: float) -> None:
        """
        Update the toast notification.
        
        Args:
            dt: Delta time in seconds
        """
        self.time_remaining -= dt
        
        # Fade out during the last 0.5 seconds
        if self.time_remaining < 0.5:
            self.alpha = int(255 * (self.time_remaining / 0.5))
            self.alpha = max(0, min(255, self.alpha))
    
    def draw(self, surface: pygame.Surface, position: Tuple[int, int]) -> None:
        """
        Draw the toast notification with improved visuals.
        
        Args:
            surface: Surface to draw on
            position: (x, y) position to draw at (top-left corner)
        """
        # Create a surface for the toast
        toast_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Draw background with gradient
        for i in range(self.height):
            # Create gradient from top to bottom
            alpha = int(self.alpha * (0.7 + 0.3 * (1 - i / self.height)))
            if len(self.bg_color) == 3:
                color = (*self.bg_color, alpha)
            else:
                # Use alpha from bg_color but scale it by our fade effect
                color = (*self.bg_color[:3], int(self.bg_color[3] * self.alpha / 255))
            pygame.draw.line(toast_surface, color, (0, i), (self.width, i))
        
        # Draw rounded rectangle border
        border_color = (*self.color[:3], self.alpha)
        pygame.draw.rect(toast_surface, border_color, 
                        (0, 0, self.width, self.height), width=2, border_radius=5)
        
        # Draw text with shadow
        shadow_surface = self.font.render(self.message, True, (0, 0, 0, self.alpha))
        text_surface = self.font.render(self.message, True, (*self.color[:3], self.alpha))
        
        # Position text in center
        text_x = (self.width - text_surface.get_width()) // 2
        text_y = (self.height - text_surface.get_height()) // 2
        
        # Draw shadow slightly offset
        toast_surface.blit(shadow_surface, (text_x + 1, text_y + 1))
        toast_surface.blit(text_surface, (text_x, text_y))
        
        # Add a slight bounce effect when appearing/disappearing
        y_offset = 0
        if self.time_remaining > self.duration - 0.3:
            # Appearing
            progress = (self.duration - self.time_remaining) / 0.3
            y_offset = int(10 * (1 - progress))
        elif self.time_remaining < 0.3:
            # Disappearing
            progress = self.time_remaining / 0.3
            y_offset = int(10 * (1 - progress))
        
        # Draw the toast with the bounce effect
        surface.blit(toast_surface, (position[0], position[1] - y_offset))
    
    def should_remove(self) -> bool:
        """
        Check if the toast should be removed.
        
        Returns:
            True if the toast's time is up, False otherwise
        """
        return self.time_remaining <= 0
    
    def get_dimensions(self) -> Tuple[int, int]:
        """
        Get the toast dimensions.
        
        Returns:
            (width, height) of the toast
        """
        return (self.width, self.height) 