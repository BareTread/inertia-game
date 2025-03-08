import pygame
import math
from typing import Tuple, Optional
from utils.constants import ORANGE, WHITE, YELLOW

class BouncePad:
    """A surface that bounces the ball in a specific direction."""
    
    def __init__(self, x: int, y: int, width: int, height: int, strength: float = 1.5, angle: float = 90):
        """
        Initialize a new bounce pad.
        
        Args:
            x: Center x position
            y: Center y position
            width: Width of the bounce pad
            height: Height of the bounce pad
            strength: Bounce strength multiplier
            angle: Angle in degrees (90 = up, 0 = right, 180 = left, 270 = down)
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.strength = strength
        self.rect = pygame.Rect(x, y, width, height)
        
        # Convert angle to direction vector
        angle_rad = math.radians(angle)
        self.direction = [math.cos(angle_rad), -math.sin(angle_rad)]  # Negative y because pygame y increases downward
        
        self.active = True
        self.color = (255, 165, 0)  # Orange
        self.activated = False
        self.activation_timer = 0
        self.activation_duration = 0.3
        
        # Animation properties
        self.time = 0
        self.active_time = 0
        self.activate_cooldown = 0
        
        # Precompute half dimensions for faster collision checks
        self.half_width = width / 2
        self.half_height = height / 2
        
        # Arrow properties
        self.arrow_length = min(width, height) * 0.4
        self.arrow_width = self.arrow_length * 0.3
    
    def update(self, dt: float) -> None:
        """Update the bounce pad animation."""
        self.time += dt
        
        # Update activation animation
        if self.active:
            self.active_time += dt
            if self.active_time >= 0.2:
                self.active = False
                self.active_time = 0
        
        # Update cooldown
        if self.activate_cooldown > 0:
            self.activate_cooldown -= dt
    
    def draw(self, surface: pygame.Surface, camera_offset=(0, 0)) -> None:
        """Draw the bounce pad on the surface."""
        # Calculate adjusted position
        adjusted_x = self.x - camera_offset[0]
        adjusted_y = self.y - camera_offset[1]
        
        # Base rectangle
        # Calculate color pulsation for the pad
        pulse = math.sin(self.time * 5) * 0.2
        color_value = int(255 * (0.8 + pulse))
        pad_color = (ORANGE[0], color_value, ORANGE[2])
        
        # Create rectangle for the pad
        rect = pygame.Rect(
            adjusted_x - self.half_width,
            adjusted_y - self.half_height,
            self.width,
            self.height
        )
        
        # Draw the pad with a border
        pygame.draw.rect(surface, pad_color, rect)
        pygame.draw.rect(surface, WHITE, rect, 2)
        
        # Draw direction arrow
        self._draw_direction_arrow(surface, camera_offset)
        
        # Draw activation effect
        if self.active:
            # Create expanding ring effect when activated
            expansion_factor = self.active_time * 10  # Expands over 0.2 seconds
            expansion_width = int(max(1, 5 - 20 * self.active_time))
            
            expanded_rect = pygame.Rect(
                adjusted_x - self.half_width - expansion_factor * 5,
                adjusted_y - self.half_height - expansion_factor * 5,
                self.width + expansion_factor * 10,
                self.height + expansion_factor * 10
            )
            
            # Draw with fading alpha
            alpha = int(255 * (1 - self.active_time / 0.2))
            if alpha > 0:
                # Create a surface for the alpha effect
                effect_surface = pygame.Surface((expanded_rect.width, expanded_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(effect_surface, (*YELLOW[:3], alpha), 
                                (0, 0, expanded_rect.width, expanded_rect.height), 
                                expansion_width)
                surface.blit(effect_surface, expanded_rect)
    
    def _draw_direction_arrow(self, surface: pygame.Surface, camera_offset=(0, 0)) -> None:
        """Draw an arrow indicating the bounce direction."""
        # Calculate adjusted position
        adjusted_x = self.x - camera_offset[0]
        adjusted_y = self.y - camera_offset[1]
        
        # Calculate arrow start point at center of pad
        start_x = adjusted_x
        start_y = adjusted_y
        
        # Calculate arrow end point
        end_x = start_x + self.direction[0] * self.arrow_length
        end_y = start_y + self.direction[1] * self.arrow_length
        
        # Draw arrow line
        pygame.draw.line(surface, WHITE, (start_x, start_y), (end_x, end_y), 3)
        
        # Calculate arrowhead points
        # Get perpendicular direction for arrowhead
        perp_x = -self.direction[1]
        perp_y = self.direction[0]
        
        # Calculate arrowhead points
        arrow_size = self.arrow_width / 2
        p1_x = end_x - self.direction[0] * arrow_size + perp_x * arrow_size
        p1_y = end_y - self.direction[1] * arrow_size + perp_y * arrow_size
        
        p2_x = end_x - self.direction[0] * arrow_size - perp_x * arrow_size
        p2_y = end_y - self.direction[1] * arrow_size - perp_y * arrow_size
        
        # Draw arrowhead
        pygame.draw.polygon(surface, WHITE, [(end_x, end_y), (p1_x, p1_y), (p2_x, p2_y)])
    
    def check_collision(self, ball) -> bool:
        """Check if ball collides with bounce pad and apply bounce if needed."""
        # Find closest point on rectangle to circle center
        closest_x = max(self.x - self.half_width, min(ball.x, self.x + self.half_width))
        closest_y = max(self.y - self.half_height, min(ball.y, self.y + self.half_height))
        
        # Calculate distance from closest point to circle center
        dx = ball.x - closest_x
        dy = ball.y - closest_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        # Check if distance is less than circle radius (collision occurred)
        if distance < ball.radius:
            self._bounce_ball(ball)
            return True
        
        return False
    
    def _bounce_ball(self, ball) -> None:
        """Apply bounce effect to the ball."""
        if self.activate_cooldown <= 0:
            # Calculate more satisfying bounce
            current_speed = math.sqrt(ball.vel_x**2 + ball.vel_y**2)
            
            # Minimum bounce speed ensures consistency
            bounce_speed = max(current_speed * self.strength, 200)
            
            ball.vel_x = self.direction[0] * bounce_speed
            ball.vel_y = self.direction[1] * bounce_speed
            
            # Activate visual effect
            self.active = True
            self.active_time = 0
            self.activate_cooldown = 0.1  # Prevent rapid consecutive bounces 
    
    def get_position(self):
        """Return the current position of the bounce pad."""
        return (self.x, self.y)
    
    def set_position(self, position):
        """Set the position of the bounce pad."""
        self.x, self.y = position
        self.rect.x, self.rect.y = position 