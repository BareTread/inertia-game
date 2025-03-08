import pygame
import math
import random
from typing import Optional, Tuple, List
from utils.constants import PURPLE, CYAN, WHITE, BLACK

class Teleporter:
    """A teleporter that can transport the ball to another location."""
    
    def __init__(self, x: int, y: int, pair_id: int, target_teleporter=None, 
                 radius: int = 25, cooldown: float = 1.0):
        """
        Initialize a new teleporter.
        
        Args:
            x: X-coordinate
            y: Y-coordinate
            pair_id: ID to match teleporter pairs
            target_teleporter: The teleporter this one links to
            radius: Radius of the teleporter
            cooldown: Time before teleporter can be used again
        """
        self.x = x
        self.y = y
        self.pair_id = pair_id
        self.target_teleporter = target_teleporter
        self.radius = radius
        self.cooldown = cooldown
        
        # Animation properties
        self.time = 0
        self.active = False
        self.active_time = 0
        self.cooldown_timer = 0
        self.portal_particles: List[Tuple[float, float, float, float, float]] = []
        self.color = PURPLE
        self.secondary_color = CYAN
        
        # Precomputed to avoid recalculation
        self.outer_radius = radius * 1.2
        self.inner_radius = radius * 0.7
    
    def update(self, dt: float) -> None:
        """Update the teleporter state and animations."""
        self.time += dt
        
        # Update cooldown timer
        if self.cooldown_timer > 0:
            self.cooldown_timer -= dt
        
        # Update activation effect
        if self.active:
            self.active_time += dt
            if self.active_time >= 0.5:
                self.active = False
                self.active_time = 0
        
        # Update portal particles
        # Add new particles
        if len(self.portal_particles) < 20 and random.random() < 0.3:
            angle = random.uniform(0, math.pi * 2)
            distance = random.uniform(0, self.radius * 0.6)
            x = self.x + math.cos(angle) * distance
            y = self.y + math.sin(angle) * distance
            
            # Start from center and move outward
            speed = random.uniform(20, 50)
            life = random.uniform(0.5, 1.0)
            particle_angle = math.atan2(y - self.y, x - self.x)
            
            # [x, y, angle, speed, life]
            self.portal_particles.append((x, y, particle_angle, speed, life))
        
        # Update existing particles
        updated_particles = []
        for p_x, p_y, p_angle, p_speed, p_life in self.portal_particles:
            # Move particle outward along its angle
            p_x += math.cos(p_angle) * p_speed * dt
            p_y += math.sin(p_angle) * p_speed * dt
            p_life -= dt
            
            # Keep particle if still alive
            if p_life > 0:
                updated_particles.append((p_x, p_y, p_angle, p_speed, p_life))
        
        self.portal_particles = updated_particles
    
    def draw(self, surface: pygame.Surface, camera_offset=(0, 0)) -> None:
        """Draw the teleporter on the surface."""
        # Calculate adjusted position
        adjusted_x = self.x - camera_offset[0]
        adjusted_y = self.y - camera_offset[1]
        
        # Draw outer glow
        glow_radius = self.outer_radius + math.sin(self.time * 2) * 3
        glow_alpha = 100 + int(50 * math.sin(self.time * 3))
        glow_color = (*self.color[:3], glow_alpha)
        
        # Create glow surface
        glow_size = int(glow_radius * 2)
        glow_surface = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, glow_color, (glow_size//2, glow_size//2), glow_radius)
        surface.blit(glow_surface, (adjusted_x - glow_size//2, adjusted_y - glow_size//2))
        
        # Draw outer ring
        pygame.draw.circle(surface, self.color, (adjusted_x, adjusted_y), self.radius)
        
        # Draw inner portal
        inner_radius = self.inner_radius + math.sin(self.time * 4) * 2
        pygame.draw.circle(surface, BLACK, (adjusted_x, adjusted_y), inner_radius)
        
        # Draw portal particles
        for p_x, p_y, _, _, p_life in self.portal_particles:
            # Particle size and opacity based on remaining life
            p_size = int(3 * p_life)
            p_alpha = int(255 * p_life)
            p_color = (*self.secondary_color[:3], p_alpha)
            
            # Adjust particle positions
            adjusted_p_x = p_x - camera_offset[0]
            adjusted_p_y = p_y - camera_offset[1]
            
            # Draw the particle
            pygame.draw.circle(surface, p_color, (int(adjusted_p_x), int(adjusted_p_y)), p_size)
        
        # Draw activation effect
        if self.active:
            ring_expansion = self.active_time * 2  # Expand over 0.5 seconds
            ring_radius = self.radius + ring_expansion * 30
            ring_width = max(1, 5 - 10 * self.active_time)
            ring_alpha = int(255 * (1 - self.active_time / 0.5))
            ring_color = (*WHITE[:3], ring_alpha)
            
            pygame.draw.circle(surface, ring_color, (adjusted_x, adjusted_y), ring_radius, int(ring_width))
        
        # Draw cooldown indicator if on cooldown
        if self.cooldown_timer > 0:
            # Draw a clock-like indicator showing cooldown progress
            angle = (1 - self.cooldown_timer / self.cooldown) * math.pi * 2
            pygame.draw.arc(surface, WHITE, 
                           (adjusted_x - self.radius - 5, adjusted_y - self.radius - 5, 
                            self.radius * 2 + 10, self.radius * 2 + 10), 
                           -math.pi/2, angle - math.pi/2, 3)
        
        # Draw pair ID
        font = pygame.font.Font(None, 24)
        id_text = font.render(str(self.pair_id), True, WHITE)
        id_rect = id_text.get_rect(center=(adjusted_x, adjusted_y))
        surface.blit(id_text, id_rect)
    
    def check_collision(self, ball) -> bool:
        """Check if ball collides with teleporter and teleport it if possible."""
        # Calculate distance
        dx = ball.x - self.x
        dy = ball.y - self.y
        distance = math.sqrt(dx * dx + dy * dy)
        
        # If ball touches teleporter and not on cooldown
        if distance < self.radius + ball.radius and self.cooldown_timer <= 0:
            self.activate()
            return True
        
        return False
    
    def activate(self) -> None:
        """Activate the teleporter for visual effect."""
        self.active = True
        self.active_time = 0
        self.cooldown_timer = self.cooldown
    
    def teleport_ball(self, ball) -> None:
        """Teleport the ball to the target teleporter."""
        if self.target_teleporter:
            # Transfer ball velocity with a small bonus
            velocity_bonus = 1.1
            ball.x = self.target_teleporter.x
            ball.y = self.target_teleporter.y
            
            # Update velocity with a bonus
            ball.vel_x *= velocity_bonus
            ball.vel_y *= velocity_bonus
            
            # Activate target teleporter
            self.target_teleporter.activate()
    
    def get_position(self):
        """Return the current position of the teleporter."""
        return (self.x, self.y)
    
    def set_position(self, position):
        """Set the position of the teleporter."""
        self.x, self.y = position 