import pygame
from utils.constants import WHITE

class Slider:
    """A slider for adjusting numeric values."""
    
    def __init__(self, x, y, width, height, min_value=0, max_value=1, 
                 initial_value=0.5, label="", font=None, text_color=WHITE,
                 bg_color=(50, 50, 50), handle_color=(200, 200, 200),
                 active_color=(100, 200, 255), callback=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.label = label
        if font is None:
            self.font = pygame.font.Font(None, 24)
        else:
            self.font = font
        self.text_color = text_color
        self.bg_color = bg_color
        self.handle_color = handle_color
        self.active_color = active_color
        self.callback = callback
        self.active = False
        
        # Create the slider track rectangle
        self.track_rect = pygame.Rect(
            x - width/2,
            y - height/2,
            width,
            height
        )
        
        # Create the handle rectangle
        self.handle_width = height * 2
        self.handle_rect = pygame.Rect(
            self._get_handle_x() - self.handle_width/2,
            y - height,
            self.handle_width,
            height * 2
        )
        
        # Pre-render label
        self.label_surface = self.font.render(label, True, text_color)
        self.label_rect = self.label_surface.get_rect(midright=(x - width/2 - 10, y))
        
        # Pre-render value text
        self.value_surface = self.font.render(f"{self.value:.2f}", True, text_color)
        self.value_rect = self.value_surface.get_rect(midleft=(x + width/2 + 10, y))
    
    def _get_handle_x(self):
        """Calculate the x position of the handle based on the current value."""
        normalized_value = (self.value - self.min_value) / (self.max_value - self.min_value)
        return self.track_rect.left + normalized_value * self.width
    
    def _update_handle_position(self):
        """Update the handle position based on the current value."""
        self.handle_rect.centerx = self._get_handle_x()
    
    def _update_value_from_mouse(self, mouse_x):
        """Update the value based on the mouse x position."""
        # Clamp mouse_x to the track bounds
        mouse_x = max(self.track_rect.left, min(mouse_x, self.track_rect.right))
        
        # Calculate normalized position (0 to 1)
        normalized_pos = (mouse_x - self.track_rect.left) / self.width
        
        # Calculate the actual value
        new_value = self.min_value + normalized_pos * (self.max_value - self.min_value)
        
        # Update the value
        self.set_value(new_value)
    
    def update(self, mouse_pos, mouse_pressed):
        """Update the slider state based on mouse position and button state."""
        mouse_x, mouse_y = mouse_pos
        
        # Check if mouse is over the handle or if the slider is active
        handle_hovered = self.handle_rect.collidepoint(mouse_pos)
        track_hovered = self.track_rect.collidepoint(mouse_pos)
        
        # Start dragging if mouse is pressed on the handle
        if mouse_pressed[0]:
            if handle_hovered or track_hovered:
                self.active = True
            
            if self.active:
                self._update_value_from_mouse(mouse_x)
                return True
        else:
            # Stop dragging when mouse is released
            self.active = False
        
        return False
    
    def draw(self, surface):
        """Draw the slider on the given surface."""
        # Draw track
        pygame.draw.rect(surface, self.bg_color, self.track_rect, border_radius=3)
        
        # Draw filled portion
        filled_width = self.handle_rect.centerx - self.track_rect.left
        if filled_width > 0:
            filled_rect = pygame.Rect(
                self.track_rect.left,
                self.track_rect.top,
                filled_width,
                self.height
            )
            pygame.draw.rect(surface, self.active_color, filled_rect, border_radius=3)
        
        # Draw handle
        handle_color = self.active_color if self.active else self.handle_color
        pygame.draw.rect(surface, handle_color, self.handle_rect, border_radius=5)
        
        # Draw label
        surface.blit(self.label_surface, self.label_rect)
        
        # Update and draw value text
        value_text = f"{self.value:.2f}"
        self.value_surface = self.font.render(value_text, True, self.text_color)
        self.value_rect = self.value_surface.get_rect(midleft=(self.track_rect.right + 10, self.y))
        surface.blit(self.value_surface, self.value_rect)
    
    def set_value(self, value):
        """Set the slider value and update the handle position."""
        # Clamp value to min/max range
        self.value = max(self.min_value, min(value, self.max_value))
        
        # Update handle position
        self._update_handle_position()
        
        # Call the callback if provided
        if self.callback:
            self.callback(self.value)
    
    def get_value(self):
        """Get the current slider value."""
        return self.value 