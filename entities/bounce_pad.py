import pygame
import math
from typing import Tuple, Optional
from utils.constants import ORANGE, WHITE, YELLOW

class BouncePad:
    """A surface that bounces the ball in a specific direction."""
    
    def __init__(self, x, y, width=60, height=15, angle=0, strength=1.5, color=(0, 200, 255)):
        """
        Initialize a new bounce pad.
        
        Args:
            x: Center x position
            y: Center y position
            width: Width of the bounce pad
            height: Height of the bounce pad
            angle: Angle in degrees (0 = right, 180 = left, 270 = down)
            strength: Bounce strength multiplier
            color: Color of the bounce pad
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.angle = angle  # Angle in degrees
        self.strength = strength  # Bounce strength multiplier
        self.color = color
        
        # Visual properties
        self.active = False
        self.active_time = 0
        self.activate_cooldown = 0
        self.pulse_timer = 0
        
        # Calculate bounce direction from angle
        angle_rad = math.radians(angle)
        self.direction = (math.cos(angle_rad), math.sin(angle_rad))
        
        # Create rectangle for collision detection
        self.rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
        
        # Rotate rectangle to match angle
        self.points = self._get_rotated_points()
        
        # Precompute half dimensions for faster collision checks
        self.half_width = width / 2
        self.half_height = height / 2
        
        # Arrow properties
        self.arrow_length = min(width, height) * 0.4
        self.arrow_width = self.arrow_length * 0.3
    
    def update(self, dt: float) -> None:
        """Update the bounce pad animation."""
        self.pulse_timer += dt
        
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
        pulse = math.sin(self.pulse_timer * 5) * 0.2
        color_value = int(255 * (0.8 + pulse))
        pad_color = (self.color[0], color_value, self.color[2])
        
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
    
    def _bounce_ball(self, ball):
        """Apply bounce effect to the ball."""
        # Calculate current ball speed
        current_speed = math.sqrt(ball.vel_x**2 + ball.vel_y**2)
        
        # Skip tiny speeds
        if current_speed < 0.1:
            return
            
        # Get bounce strength as a float (handle cases where it might be a tuple or list)
        bounce_strength = self.strength
        if isinstance(bounce_strength, (list, tuple)):
            if len(bounce_strength) > 0:
                bounce_strength = float(bounce_strength[0])
            else:
                bounce_strength = 1.5  # Default value
        elif not isinstance(bounce_strength, (int, float)):
            bounce_strength = 1.5  # Default value for unknown types
        
        # Calculate bounce speed
        bounce_speed = max(current_speed * bounce_strength, 200.0)
        
        # Get normalized direction based on bounce pad angle
        angle_rad = math.radians(self.angle)
        direction_x = math.cos(angle_rad)
        direction_y = math.sin(angle_rad)
        
        # Apply bounce velocity
        ball.vel_x = direction_x * bounce_speed
        ball.vel_y = direction_y * bounce_speed
        
        # Add visual feedback
        if hasattr(ball, 'game') and ball.game and hasattr(ball.game, 'particle_system'):
            # Create bounce particles
            opposite_dir_x = -direction_x
            opposite_dir_y = -direction_y
            
            # Position particles at the bounce point (edge of bounce pad)
            particle_x = self.x + (self.width / 2) * direction_x
            particle_y = self.y + (self.height / 2) * direction_y
            
            # Create particles
            ball.game.particle_system.create_particles(
                particle_x, particle_y,
                15,  # Number of particles
                self.color,  # Use bounce pad color
                min_speed=50,
                max_speed=150,
                min_lifetime=0.2,
                max_lifetime=0.6,
                direction=(opposite_dir_x, opposite_dir_y),
                spread=1.2  # Wide spread
            )
    
    def get_position(self):
        """Return the current position of the bounce pad."""
        return (self.x, self.y)
    
    def set_position(self, position):
        """Set the position of the bounce pad."""
        self.x, self.y = position
        self.rect.x, self.rect.y = position 

    def _get_rotated_points(self):
        """Return the rotated points of the bounce pad."""
        # Calculate the rotated points of the rectangle
        angle_rad = math.radians(self.angle)
        cos_angle = math.cos(angle_rad)
        sin_angle = math.sin(angle_rad)
        
        # Calculate the rotated points
        points = [
            (self.x - self.half_width * cos_angle - self.half_height * sin_angle,
             self.y - self.half_width * sin_angle + self.half_height * cos_angle),
            (self.x + self.half_width * cos_angle - self.half_height * sin_angle,
             self.y + self.half_width * sin_angle + self.half_height * cos_angle),
            (self.x + self.half_width * cos_angle + self.half_height * sin_angle,
             self.y + self.half_width * sin_angle - self.half_height * cos_angle),
            (self.x - self.half_width * cos_angle + self.half_height * sin_angle,
             self.y - self.half_width * sin_angle - self.half_height * cos_angle)
        ]
        
        return points 