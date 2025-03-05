import pygame
import math
from utils.constants import WIDTH, HEIGHT, WHITE, RED, BLUE
from utils.helpers import clamp

class Ball:
    """The main player-controlled ball."""
    
    def __init__(self, x, y, radius=15):
        self.x = x
        self.y = y
        self.radius = radius
        self.vel_x = 0
        self.vel_y = 0
        self.original_radius = radius
        self.pulse_timer = 0
        self.pulse_amount = 0
        self.trail_positions = []
        self.max_trail_length = 15  # Increased trail length
        self.trail_timer = 0
        self.trail_interval = 0.03  # More frequent trail updates
        self.glow_radius = radius * 2.0  # Larger glow
        self.glow_color = (100, 150, 255, 100)  # Blueish glow
        self.color = BLUE
        
        # Mastery reward visual effects
        self.trail_enabled = False
        self.trail_color = BLUE
        self.collision_particles_enabled = False
        self.collision_particle_color = WHITE
        self.pulse_color = WHITE
        self.pulse_strength = 1.0
        
    def apply_force(self, force_x, force_y):
        """Apply a force to the ball, changing its velocity."""
        # Add "weight" to movement for better feel
        force_multiplier = 1.2  # Slightly increase force impact
        self.vel_x += force_x * force_multiplier
        self.vel_y += force_y * force_multiplier
        
        # Add subtle "boost" effect when starting from standstill
        if abs(self.vel_x) < 0.1 and abs(self.vel_y) < 0.1:
            self.vel_x += force_x * 0.3  # Extra initial push
            self.vel_y += force_y * 0.3
        
    def update(self, dt, friction=0.99):
        """Update the ball's position and animation."""
        # Update pulse animation
        self.pulse_timer += dt
        self.pulse_amount = math.sin(self.pulse_timer * 5) * 2
        
        # Apply friction
        self.vel_x *= friction
        self.vel_y *= friction
        
        # If velocity is very small, stop completely (prevents endless sliding)
        if abs(self.vel_x) < 0.05 and abs(self.vel_y) < 0.05:
            self.vel_x = 0
            self.vel_y = 0
        
        # Update position
        self.x += self.vel_x * dt * 60  # Scale by dt and 60 to normalize for framerate
        self.y += self.vel_y * dt * 60
        
        # Update trail positions
        self.trail_timer += dt
        if self.trail_timer >= self.trail_interval and (abs(self.vel_x) > 0.5 or abs(self.vel_y) > 0.5):
            self.trail_timer = 0
            self.trail_positions.append((self.x, self.y))
            
            # Limit trail length
            if len(self.trail_positions) > self.max_trail_length:
                self.trail_positions.pop(0)
        
        # Keep ball within screen bounds
        self.x = clamp(self.x, self.radius, WIDTH - self.radius)
        self.y = clamp(self.y, self.radius, HEIGHT - self.radius)
        
    def draw(self, screen):
        """Draw the ball and its effects."""
        # Draw trail first (behind ball)
        if self.trail_enabled and len(self.trail_positions) > 2:
            # Draw trail as a fading line
            for i in range(len(self.trail_positions) - 1):
                # Calculate alpha based on position in trail
                alpha = int(255 * (i / len(self.trail_positions)))
                color = (*self.trail_color[:3], alpha)
                pos1 = self.trail_positions[i]
                pos2 = self.trail_positions[i + 1]
                # Calculate width based on position (thicker toward the ball)
                width = int(1 + (i / len(self.trail_positions)) * 3)
                pygame.draw.line(screen, color, pos1, pos2, width)
        
        # Draw glow effect
        if self.glow_radius > 0:
            # Create a surface for the glow with alpha
            glow_surface = pygame.Surface((self.glow_radius * 2, self.glow_radius * 2), pygame.SRCALPHA)
            # Draw radial gradient for glow
            pygame.draw.circle(glow_surface, self.glow_color, (self.glow_radius, self.glow_radius), self.glow_radius)
            # Draw the glow surface on the screen
            screen.blit(glow_surface, (self.x - self.glow_radius, self.y - self.glow_radius), special_flags=pygame.BLEND_ALPHA_SDL2)
            
        # Calculate pulsing size
        pulse_radius = self.radius + self.pulse_amount * self.pulse_strength
            
        # Draw the ball itself
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(pulse_radius))
        
        # Draw pulse outline if pulsing
        if self.pulse_amount > 0.1 and self.pulse_strength > 0:
            pygame.draw.circle(screen, self.pulse_color, (int(self.x), int(self.y)), int(pulse_radius), 2)
    
    def reset_velocity(self):
        """Reset the ball's velocity to zero."""
        self.vel_x = 0
        self.vel_y = 0
        
    def get_speed(self):
        """Get the current speed of the ball."""
        return math.sqrt(self.vel_x**2 + self.vel_y**2)
        
    def teleport(self, x, y):
        """Teleport the ball to a new position."""
        self.x = x
        self.y = y
        # Clear the trail when teleporting
        self.trail_positions = [] 