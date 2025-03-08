import pygame
from typing import Tuple, Optional
import math
from utils.constants import PURPLE, BLUE, WHITE
import random

class GravityWell:
    """A gravity well that attracts or repels the ball."""
    
    def __init__(self, x: int, y: int, radius: int = 50, strength: float = 0.5, repel: bool = False):
        """
        Initialize a new gravity well.
        
        Args:
            x: Center x position
            y: Center y position
            radius: Radius of the gravity field
            strength: Strength of the gravitational pull/push
            repel: If True, this well repels instead of attracts
        """
        self.x = x
        self.y = y
        self.radius = radius
        self.strength = strength
        self.repel = repel
        
        # Animation properties
        self.time = 0
        self.pulse_speed = 0.5
        self.pulse_amount = 0
        self.glow_radius = self.radius * 0.2
        self.glow_opacity = 128
        
        # Create surfaces for drawing efficiency
        self.field_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        self.update_field_surface()
        
        self.pulse_timer = 0
        self.active = True
        self.color = (100, 0, 150)  # Purple
        self.glow_color = (150, 50, 200, 100)  # Semi-transparent purple
    
    def update_field_surface(self) -> None:
        """Update the pre-rendered field surface."""
        self.field_surface.fill((0, 0, 0, 0))
        
        # Draw gradient field with concentric circles
        steps = 10
        for i in range(steps, 0, -1):
            alpha = int(80 * (i / steps))
            color = BLUE if not self.repel else PURPLE
            color_with_alpha = (*color[:3], alpha)
            radius = int(self.radius * (i / steps))
            pygame.draw.circle(self.field_surface, color_with_alpha, 
                              (self.radius, self.radius), radius)
    
    def update(self, dt: float) -> None:
        """Update the gravity well animation."""
        self.time += dt
        
        # Update glow effect
        self.glow_opacity = 128 + int(40 * math.sin(self.time * 2))
    
    def draw(self, surface: pygame.Surface, camera_offset=(0, 0)) -> None:
        """Draw the gravity well on the surface."""
        # Calculate adjusted position
        adjusted_x = self.x - camera_offset[0]
        adjusted_y = self.y - camera_offset[1]
        
        # Draw the gravity field
        field_rect = self.field_surface.get_rect(center=(adjusted_x, adjusted_y))
        surface.blit(self.field_surface, field_rect)
        
        # Draw core
        pulse = math.sin(self.time * self.pulse_speed) * self.pulse_amount
        core_radius = int(self.radius * 0.3 * (1 + pulse))
        color = BLUE if not self.repel else PURPLE
        
        # Draw core glow
        glow_radius = core_radius + self.glow_radius
        glow_color = (*color[:3], self.glow_opacity)
        pygame.draw.circle(surface, glow_color, (adjusted_x, adjusted_y), glow_radius)
        
        # Draw solid core
        pygame.draw.circle(surface, color, (adjusted_x, adjusted_y), core_radius)
        
        # Draw core border
        pygame.draw.circle(surface, WHITE, (adjusted_x, adjusted_y), core_radius, 2)
        
        # Draw direction indicator
        if self.repel:
            # Draw outward arrows
            for angle in range(0, 360, 90):
                rad = math.radians(angle)
                start_x = adjusted_x + math.cos(rad) * core_radius
                start_y = adjusted_y + math.sin(rad) * core_radius
                end_x = adjusted_x + math.cos(rad) * (core_radius + 15)
                end_y = adjusted_y + math.sin(rad) * (core_radius + 15)
                
                # Draw arrow line
                pygame.draw.line(surface, WHITE, (start_x, start_y), (end_x, end_y), 2)
                
                # Draw arrowhead
                arr_angle1 = rad + math.radians(140)
                arr_angle2 = rad + math.radians(220)
                arr_len = 7
                
                arr_x1 = end_x + math.cos(arr_angle1) * arr_len
                arr_y1 = end_y + math.sin(arr_angle1) * arr_len
                arr_x2 = end_x + math.cos(arr_angle2) * arr_len
                arr_y2 = end_y + math.sin(arr_angle2) * arr_len
                
                pygame.draw.line(surface, WHITE, (end_x, end_y), (arr_x1, arr_y1), 2)
                pygame.draw.line(surface, WHITE, (end_x, end_y), (arr_x2, arr_y2), 2)
        else:
            # Draw inward arrows
            for angle in range(0, 360, 90):
                rad = math.radians(angle)
                start_x = adjusted_x + math.cos(rad) * (core_radius + 15)
                start_y = adjusted_y + math.sin(rad) * (core_radius + 15)
                end_x = adjusted_x + math.cos(rad) * core_radius
                end_y = adjusted_y + math.sin(rad) * core_radius
                
                # Draw arrow line
                pygame.draw.line(surface, WHITE, (start_x, start_y), (end_x, end_y), 2)
                
                # Draw arrowhead
                arr_angle1 = rad - math.radians(40)
                arr_angle2 = rad - math.radians(320)
                arr_len = 7
                
                arr_x1 = start_x + math.cos(arr_angle1) * arr_len
                arr_y1 = start_y + math.sin(arr_angle1) * arr_len
                arr_x2 = start_x + math.cos(arr_angle2) * arr_len
                arr_y2 = start_y + math.sin(arr_angle2) * arr_len
                
                pygame.draw.line(surface, WHITE, (start_x, start_y), (arr_x1, arr_y1), 2)
                pygame.draw.line(surface, WHITE, (start_x, start_y), (arr_x2, arr_y2), 2)
    
    def apply_force(self, ball, dt):
        """Apply gravitational force to the ball."""
        # Calculate distance
        dx = self.x - ball.x
        dy = self.y - ball.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Add visual effect when force is applied
        if distance < self.radius * 2 and hasattr(ball, 'game') and hasattr(ball.game, 'particle_system'):
            # Create particles flowing toward/away from gravity well
            if random.random() < 0.3:
                # Calculate position along the line between ball and gravity well
                pos_factor = random.uniform(0.1, 0.9)
                particle_x = ball.x + dx * pos_factor
                particle_y = ball.y + dy * pos_factor
                
                # Direction depends on attraction/repulsion
                direction = -1 if not self.repel else 1
                color = BLUE if not self.repel else PURPLE
                
                ball.game.particle_system.add_particle(
                    particle_x, particle_y,
                    dx/distance * 0.1 * direction, 
                    dy/distance * 0.1 * direction,
                    color,
                    random.uniform(1, 3),
                    0.5,
                    fade_mode="smooth",
                    glow=True
                )
        
        # Apply force with improved falloff
        if distance > 0 and distance < self.radius * 3:
            # Inverse square law for more realistic gravity
            strength = self.strength / (distance * distance) * 1000
            force_x = dx / distance * strength * dt
            force_y = dy / distance * strength * dt
            
            # Apply force (negative if repulsive)
            direction = 1 if not self.repel else -1
            ball.vel_x += force_x * direction
            ball.vel_y += force_y * direction
    
    def get_position(self):
        """Return the current position of the gravity well."""
        return (self.x, self.y)
    
    def set_position(self, position):
        """Set the position of the gravity well."""
        self.x, self.y = position 