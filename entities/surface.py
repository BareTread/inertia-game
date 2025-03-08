import pygame
import random
import math
from utils.constants import WHITE, BLACK, WIDTH, HEIGHT

class Surface:
    """A surface with custom properties that the ball can move on."""
    
    def __init__(self, x, y, width, height, friction=0.99, color=(255, 255, 255, 180), game=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)
        self.friction = friction
        self.color = color
        self.game = game
        self.animation_timer = 0
            
    def update(self, dt):
        """Update surface animations."""
        self.animation_timer += dt
            
    def draw(self, surface, camera_offset=(0, 0)):
        """Draw the surface on the screen."""
        # Calculate adjusted position
        adjusted_x = self.rect.x - camera_offset[0]
        adjusted_y = self.rect.y - camera_offset[1]
        
        # Create a transparent surface
        surface_rect = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
        # Draw with transparency
        pygame.draw.rect(surface_rect, self.color, (0, 0, self.rect.width, self.rect.height))
        
        # Draw the transparent surface onto the main surface
        surface.blit(surface_rect, (adjusted_x, adjusted_y))
        
        # Draw borders
        pygame.draw.rect(surface, BLACK, pygame.Rect(
            adjusted_x, adjusted_y, self.rect.width, self.rect.height
        ), 2)
    
    def handle_collision(self, ball):
        """
        Check if the ball is on this surface and return the friction value.
        """
        if self.rect.collidepoint(ball.x, ball.y):
            return self.friction
        return None
        
    def check_collision(self, ball):
        """Check if the ball is colliding with this surface."""
        # Simple point-rectangle collision check
        return self.rect.collidepoint(ball.x, ball.y)

    def get_position(self):
        """Return the current position of the surface."""
        return (self.x, self.y)
    
    def set_position(self, position):
        """Set the position of the surface."""
        self.x, self.y = position
        self.rect.x, self.rect.y = position 