import pygame
from utils.constants import WHITE

class Button:
    """A clickable button for the UI."""
    
    def __init__(self, x, y, width, height, text, font=None, text_color=WHITE, 
                 bg_color=(100, 100, 100), hover_color=(150, 150, 150), 
                 border_color=(200, 200, 200), border_width=2, 
                 callback=None, padding=10):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.font = font or pygame.font.Font(None, 32)
        self.text_color = text_color
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.border_color = border_color
        self.border_width = border_width
        self.callback = callback
        self.padding = padding
        self.hovered = False
        self.pressed = False
        self.disabled = False
        
        # Create the rectangle
        self.rect = pygame.Rect(
            x - width/2,
            y - height/2,
            width,
            height
        )
        
        # Pre-render text
        self.text_surface = self.font.render(text, True, text_color)
        self.text_rect = self.text_surface.get_rect(center=(x, y))
    
    def update(self, mouse_pos, mouse_pressed):
        """Update the button state based on mouse position and button state."""
        if self.disabled:
            return False
            
        # Check if mouse is over the button
        self.hovered = self.rect.collidepoint(mouse_pos)
        
        # Check if button is being pressed
        was_pressed = self.pressed
        self.pressed = self.hovered and mouse_pressed[0]
        
        # Check for click (button was pressed and now released while still hovering)
        if was_pressed and not self.pressed and self.hovered:
            if self.callback:
                self.callback()
            return True
            
        return False
    
    def draw(self, surface):
        """Draw the button on the given surface."""
        # Determine the button color based on state
        color = self.bg_color
        if self.disabled:
            color = (70, 70, 70)
        elif self.pressed:
            color = (80, 80, 80)
        elif self.hovered:
            color = self.hover_color
        
        # Draw button background
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        
        # Draw border
        if self.border_width > 0:
            pygame.draw.rect(surface, self.border_color, self.rect, self.border_width, border_radius=5)
        
        # Draw text
        text_color = self.text_color
        if self.disabled:
            text_color = (150, 150, 150)
        
        text_surface = self.font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
    
    def set_text(self, text):
        """Change the button text."""
        self.text = text
        self.text_surface = self.font.render(text, True, self.text_color)
        self.text_rect = self.text_surface.get_rect(center=(self.x, self.y))
    
    def set_position(self, x, y):
        """Change the button position."""
        self.x = x
        self.y = y
        self.rect.center = (x, y)
        self.text_rect.center = (x, y)
    
    def set_disabled(self, disabled):
        """Enable or disable the button."""
        self.disabled = disabled 