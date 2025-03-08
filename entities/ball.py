import pygame
import math
from utils.constants import WIDTH, HEIGHT, WHITE, RED, BLUE, FRICTION
from utils.helpers import clamp
from utils.constants import MIN_FORCE_THRESHOLD, MAX_FORCE, MAX_SHAKE

class Ball:
    """The main player-controlled ball."""
    
    def __init__(self, x, y, radius=15, color=BLUE):
        # Basic properties
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.vel_x = 0
        self.vel_y = 0
        self.original_radius = radius
        
        # Visual effects
        self.pulse_timer = 0
        self.pulse_amount = 0
        self.trail_positions = []
        self.max_trail_length = 10
        self.trail_timer = 0
        self.trail_interval = 0.05  # Time between trail points
        self.trail_lifetime = 1.0  # Lifetime of trail points in seconds
        self.glow_radius = radius * 1.5
        self.glow_color = (70, 130, 230, 120)  # Blueish glow
        self.trail_color = color
        
        # Physics properties
        self.mass = 1.0
        self.mass_inverse = 1.0 / self.mass
        self.prev_x = x
        self.prev_y = y
        self.current_surface_friction = None
        
        # Game reference
        self.game = None
        
        # Powerup effects
        self.speed_multiplier = 1.0
        self.collision_particles_enabled = False
        self.collision_particle_color = WHITE
        self.pulse_color = WHITE
        self.pulse_strength = 1.0
        
    def get_position(self):
        """Return the current position of the ball."""
        return (self.x, self.y)
    
    def set_position(self, position):
        """Set the position of the ball."""
        self.x, self.y = position
        
    def apply_force(self, force_x, force_y):
        """Apply force with improved feel"""
        # Calculate force magnitude
        magnitude = math.sqrt(force_x**2 + force_y**2)
        
        # Apply minimum force threshold
        if magnitude < 0.1:  # Minimum threshold
            if magnitude > 0:
                # Scale up to minimum threshold while preserving direction
                force_x = force_x * (0.1 / magnitude)
                force_y = force_y * (0.1 / magnitude)
                magnitude = 0.1
            
        # Apply force with "weight" feel
        force_multiplier = 1.2  # Slightly increase impact
        self.vel_x += force_x * force_multiplier * self.mass_inverse
        self.vel_y += force_y * force_multiplier * self.mass_inverse
        
        # Add extra push when starting from rest
        if abs(self.vel_x) < 0.1 and abs(self.vel_y) < 0.1:
            self.vel_x += force_x * 0.3
            self.vel_y += force_y * 0.3
        
        # Apply velocity bounds (same as in Ball class)
        max_velocity = 15.0
        if abs(self.vel_x) > max_velocity:
            self.vel_x = max_velocity * (1 if self.vel_x > 0 else -1)
        if abs(self.vel_y) > max_velocity:
            self.vel_y = max_velocity * (1 if self.vel_y > 0 else -1)
    
    def update(self, dt, friction=FRICTION):
        """Update with improved physics"""
        # Store previous position for collision resolution
        self.prev_x = self.x
        self.prev_y = self.y
        
        # Calculate current speed for physics adjustments
        speed = math.sqrt(self.vel_x**2 + self.vel_y**2)
        damping = 0.99 if speed < 5 else 0.98  # More damping at higher speeds
        
        # Use surface friction if available
        effective_friction = self.current_surface_friction if self.current_surface_friction is not None else friction
        
        # Update position with normalized time step
        self.x += self.vel_x * dt * 60 * self.speed_multiplier
        self.y += self.vel_y * dt * 60 * self.speed_multiplier
        
        # Apply friction and damping
        self.vel_x *= effective_friction * damping
        self.vel_y *= effective_friction * damping
        
        # Stop if very slow
        if abs(self.vel_x) < 0.05 and abs(self.vel_y) < 0.05:
            self.vel_x = 0
            self.vel_y = 0
        
        # Update pulse animation
        self.pulse_timer += dt
        self.pulse_amount = math.sin(self.pulse_timer * 5) * 2
        
        # Update trail positions
        self.trail_timer += dt
        if self.trail_timer >= self.trail_interval and (abs(self.vel_x) > 0.5 or abs(self.vel_y) > 0.5):
            self.trail_timer = 0
            self.trail_positions.append((self.x, self.y, 0.0))  # Add age of 0.0
            
            # Limit trail length
            if len(self.trail_positions) > self.max_trail_length:
                self.trail_positions.pop(0)
        
        # Update age of trail positions
        updated_trail = []
        for pos_x, pos_y, age in self.trail_positions:
            new_age = age + dt
            if new_age < self.trail_lifetime:  # Only keep positions that haven't expired
                updated_trail.append((pos_x, pos_y, new_age))
        self.trail_positions = updated_trail
    
    def draw(self, surface, camera_offset=(0, 0)):
        # Calculate adjusted position with camera offset
        adjusted_x = self.x - camera_offset[0]
        adjusted_y = self.y - camera_offset[1]
        
        # Check if the ball is too far outside the screen bounds
        # If it's extremely far away, don't attempt to draw it
        max_coordinate = 1000000  # Arbitrary large limit to prevent overflow
        if (abs(adjusted_x) > max_coordinate or abs(adjusted_y) > max_coordinate or
            math.isnan(adjusted_x) or math.isnan(adjusted_y)):
            return
            
        # Draw trail effect
        if self.trail_positions:
            for i, (pos_x, pos_y, age) in enumerate(self.trail_positions):
                # Calculate trail position with camera offset
                trail_x = pos_x - camera_offset[0]
                trail_y = pos_y - camera_offset[1]
                
                # Skip if trail point is out of bounds
                if (abs(trail_x) > max_coordinate or abs(trail_y) > max_coordinate or
                    math.isnan(trail_x) or math.isnan(trail_y)):
                    continue
                
                # Fade alpha based on age
                alpha = int(255 * (1 - age / self.trail_lifetime))
                size = int(self.radius * 0.8 * (1 - age / self.trail_lifetime))
                
                if size > 0:
                    trail_color = (self.color[0], self.color[1], self.color[2], alpha)
                    glow_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surface, trail_color, (size, size), size)
                    surface.blit(glow_surface, (trail_x - size, trail_y - size),
                                special_flags=pygame.BLEND_ALPHA_SDL2)
        
        # Draw glow effect
        if self.glow_radius > 0:
            glow_surface = pygame.Surface((self.glow_radius * 2, self.glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, self.glow_color, 
                              (self.glow_radius, self.glow_radius), self.glow_radius)
            surface.blit(glow_surface, (adjusted_x - self.glow_radius, adjusted_y - self.glow_radius), 
                        special_flags=pygame.BLEND_ALPHA_SDL2)
        
        # Draw the ball with pulsing effect
        pulse_radius = self.radius + self.pulse_amount
        pygame.draw.circle(surface, self.color, (int(adjusted_x), int(adjusted_y)), int(pulse_radius))
        
        # Draw direction indicator if moving significantly
        if abs(self.vel_x) > 0.5 or abs(self.vel_y) > 0.5:
            speed = math.sqrt(self.vel_x**2 + self.vel_y**2)
            norm_x = self.vel_x / speed
            norm_y = self.vel_y / speed
            
            indicator_length = min(self.radius * 0.8, speed * 0.3)
            pygame.draw.line(
                surface,
                (255, 255, 255),
                (int(adjusted_x), int(adjusted_y)),
                (int(adjusted_x + norm_x * indicator_length), 
                 int(adjusted_y + norm_y * indicator_length)),
                max(1, int(self.radius / 5))
            )