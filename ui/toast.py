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
        Draw the toast notification to the surface.
        
        Args:
            surface: Surface to draw on
            position: (x, y) position to draw at (top-left corner)
        """
        # Create a surface for the toast
        toast_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Draw background
        if len(self.bg_color) == 4:
            # RGBA background
            pygame.draw.rect(toast_surface, self.bg_color, 
                            (0, 0, self.width, self.height), border_radius=5)
        else:
            # RGB background with set alpha
            pygame.draw.rect(toast_surface, (*self.bg_color, self.alpha), 
                            (0, 0, self.width, self.height), border_radius=5)
        
        # Draw text with alpha
        text_alpha_surface = pygame.Surface(self.text_rect.size, pygame.SRCALPHA)
        text_alpha_surface.fill((255, 255, 255, self.alpha))
        
        # Create a copy of the text surface with current alpha
        text_surface_with_alpha = self.text_surface.copy()
        text_surface_with_alpha.blit(text_alpha_surface, (0, 0), 
                                    special_flags=pygame.BLEND_RGBA_MULT)
        
        # Blit text to toast
        toast_surface.blit(text_surface_with_alpha, 
                          (self.padding, self.padding))
        
        # Blit toast to surface
        surface.blit(toast_surface, position)
    
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