import pygame
import math
import random
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
        
        # Skip if force is negligible
        if magnitude < 0.05:
            return
            
        # Apply minimum force threshold
        if magnitude < 0.1:  # Minimum threshold
            # Scale up to minimum threshold while preserving direction
            force_x = force_x * (0.1 / magnitude)
            force_y = force_y * (0.1 / magnitude)
            magnitude = 0.1
            
        # Calculate current speed
        current_speed = math.sqrt(self.vel_x**2 + self.vel_y**2)
        max_speed = 10.0  # Maximum velocity
        
        # Only apply force if not already at max speed
        if current_speed < max_speed:
            # Apply force with weight feel and variable force multiplier
            # Lower multiplier at higher speeds for better control
            force_multiplier = 2.0 - min(1.5, current_speed / max_speed)
            
            # Apply force
            self.vel_x += force_x * force_multiplier * self.mass_inverse
            self.vel_y += force_y * force_multiplier * self.mass_inverse
            
            # Add extra push when starting from rest
            if current_speed < 0.5:
                boost_factor = 0.5 * (1.0 - current_speed / 0.5)
                self.vel_x += force_x * boost_factor
                self.vel_y += force_y * boost_factor
        
        # Create particle effect for thrust if game is available
        if hasattr(self, 'game') and self.game and hasattr(self.game, 'particle_system'):
            # Calculate direction for particles (opposite to force)
            if magnitude > 0:
                direction = (-force_x / magnitude, -force_y / magnitude)
                particle_count = int(min(5, magnitude * 5))
                
                # Create particles in opposite direction to force
                self.game.particle_system.create_particles(
                    self.x, self.y,
                    particle_count,
                    (100, 100, 255),  # Blue thrust
                    min_speed=50,
                    max_speed=150,
                    min_lifetime=0.1,
                    max_lifetime=0.3,
                    direction=direction,
                    spread=0.3
                )
        
        # Apply velocity bounds
        new_speed = math.sqrt(self.vel_x**2 + self.vel_y**2)
        if new_speed > max_speed:
            scale = max_speed / new_speed
            self.vel_x *= scale
            self.vel_y *= scale
    
    def brake(self):
        """Apply braking to slow down the ball."""
        # Calculate current speed
        speed = math.sqrt(self.vel_x**2 + self.vel_y**2)
        
        # Only brake if moving
        if speed > 0.1:
            # Apply strong braking force
            brake_factor = 0.85  # Reduce velocity by 15% per frame
            self.vel_x *= brake_factor
            self.vel_y *= brake_factor
            
            # Create brake particle effect
            if hasattr(self, 'game') and self.game and hasattr(self.game, 'particle_system'):
                # Create particles in the direction opposite to movement
                if speed > 0.5:
                    direction_x = -self.vel_x / speed
                    direction_y = -self.vel_y / speed
                    
                    # Create more particles for higher speeds
                    particle_count = int(min(8, speed * 2))
                    
                    # Use red/orange particles for braking
                    brake_color = (255, 100, 50)
                    
                    for _ in range(particle_count):
                        angle_variance = math.radians(random.uniform(-15, 15))
                        dir_x = direction_x * math.cos(angle_variance) - direction_y * math.sin(angle_variance)
                        dir_y = direction_x * math.sin(angle_variance) + direction_y * math.cos(angle_variance)
                        
                        self.game.particle_system.add_particle(
                            self.x, self.y,
                            dir_x * random.uniform(10, 30),
                            dir_y * random.uniform(10, 30),
                            brake_color,
                            random.uniform(2, 4),
                            random.uniform(0.2, 0.4),
                            fade_mode="late",
                            glow=True
                        )
    
    def update(self, dt, friction=FRICTION):
        """Update with improved physics."""
        # Store previous position for collision resolution
        self.prev_x = self.x
        self.prev_y = self.y
        
        # Calculate current speed
        speed = math.sqrt(self.vel_x**2 + self.vel_y**2)
        
        # Apply variable damping based on speed
        if speed > 10.0:
            # More damping at high speeds
            damping = 0.97
        elif speed > 5.0:
            # Medium damping at medium speeds
            damping = 0.98
        else:
            # Less damping at low speeds
            damping = 0.99
        
        # Use surface friction if available
        effective_friction = self.current_surface_friction if self.current_surface_friction is not None else friction
        
        # Update position with normalized time step
        self.x += self.vel_x * dt * 60 * self.speed_multiplier
        self.y += self.vel_y * dt * 60 * self.speed_multiplier
        
        # Apply friction and damping
        self.vel_x *= effective_friction * damping
        self.vel_y *= effective_friction * damping
        
        # Stop if very slow (prevent endless drifting)
        if speed < 0.05:
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