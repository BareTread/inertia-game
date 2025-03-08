import pygame
import math
from utils.constants import WIDTH, HEIGHT, WHITE, RED, BLUE
from utils.helpers import clamp
from utils.constants import MIN_FORCE_THRESHOLD, MAX_FORCE, MAX_SHAKE

class Ball:
    """The main player-controlled ball."""
    
    def __init__(self, x, y, radius=15, color=BLUE):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color  # Now accepting color as a parameter with default BLUE
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
        
        # Mastery reward visual effects
        self.trail_enabled = False
        self.trail_color = color  # Using the provided color for trail
        self.collision_particles_enabled = False
        self.collision_particle_color = WHITE
        self.pulse_color = WHITE
        self.pulse_strength = 1.0
        
        # Add property for inverse mass (for more consistent physics)
        self.mass = 1.0
        self.mass_inverse = 1.0 / self.mass
        
        # Store previous position for collision resolution
        self.prev_x = x
        self.prev_y = y
        
        # Current surface friction (if the ball is on a special surface)
        self.current_surface_friction = None
        
        # Reference to game (will be set by level manager)
        self.game = None
        
        # Added for power-up effects
        self.speed_multiplier = 1.0
        
    def apply_force(self, force_x, force_y):
        """Apply a force to the ball with improved feel."""
        # Calculate the magnitude of the force
        magnitude = math.sqrt(force_x**2 + force_y**2)
        
        # Apply minimum force threshold to avoid tiny, unsatisfying movements
        if magnitude < 0.1:  # MIN_FORCE_THRESHOLD
            if magnitude > 0:
                # Scale up to minimum threshold while preserving direction
                force_x = force_x * (0.1 / magnitude)
                force_y = force_y * (0.1 / magnitude)
                magnitude = 0.1
        
        # Add "weight" to movement for better feel
        force_multiplier = 1.2  # Slightly increase force impact
        self.vel_x += force_x * force_multiplier * self.mass_inverse
        self.vel_y += force_y * force_multiplier * self.mass_inverse
        
        # Add subtle "boost" effect when starting from standstill
        if abs(self.vel_x) < 0.1 and abs(self.vel_y) < 0.1:
            self.vel_x += force_x * 0.3  # Extra initial push
            self.vel_y += force_y * 0.3
        
        # Apply velocity bounds
        max_velocity = 15.0
        if abs(self.vel_x) > max_velocity:
            self.vel_x = max_velocity * (1 if self.vel_x > 0 else -1)
        if abs(self.vel_y) > max_velocity:
            self.vel_y = max_velocity * (1 if self.vel_y > 0 else -1)
        
    def update(self, dt, friction=0.99):
        """Update the ball's position with improved physics."""
        # Store previous position for collision resolution
        self.prev_x = self.x
        self.prev_y = self.y
        
        # Calculate current speed for physics adjustments
        speed = (self.vel_x**2 + self.vel_y**2)**0.5
        
        # Apply non-linear damping for better feel
        damping = 0.99 if speed < 5 else 0.98  # More damping at higher speeds
        
        # Update position with speed multiplier
        self.x += self.vel_x * dt * 60 * self.speed_multiplier  # Apply speed multiplier
        self.y += self.vel_y * dt * 60 * self.speed_multiplier  # Apply speed multiplier
        
        # Apply friction and damping
        self.vel_x *= friction * damping
        self.vel_y *= friction * damping
        
        # Apply surface friction if on a special surface
        if self.current_surface_friction:
            self.vel_x *= self.current_surface_friction
            self.vel_y *= self.current_surface_friction
            self.current_surface_friction = None  # Reset after applying
        
        # Update pulse animation
        self.pulse_timer += dt
        self.pulse_amount = math.sin(self.pulse_timer * 5) * 2
        
        # If velocity is very small, stop completely (prevents endless sliding)
        if abs(self.vel_x) < 0.05 and abs(self.vel_y) < 0.05:
            self.vel_x = 0
            self.vel_y = 0
        
        # Update trail positions
        self.trail_timer += dt
        if self.trail_timer >= self.trail_interval and (abs(self.vel_x) > 0.5 or abs(self.vel_y) > 0.5):
            self.trail_timer = 0
            self.trail_positions.append((self.x, self.y))
            
            # Limit trail length
            if len(self.trail_positions) > self.max_trail_length:
                self.trail_positions.pop(0)
        
        # Position clamping to world boundaries (not screen boundaries)
        if hasattr(self, 'game') and self.game:
            self.x = clamp(self.x, self.radius, self.game.world_width - self.radius)
            self.y = clamp(self.y, self.radius, self.game.world_height - self.radius)
        
    def draw(self, screen, camera_offset=(0, 0)):
        """Draw the ball with enhanced visual feedback."""
        # Get adjusted position
        adjusted_x = self.x - camera_offset[0]
        adjusted_y = self.y - camera_offset[1]
        
        # Draw trail first (behind ball)
        if self.trail_enabled and len(self.trail_positions) > 2:
            # Draw trail as a fading line
            for i in range(len(self.trail_positions) - 1):
                # Calculate alpha based on position in trail
                alpha = int(255 * (i / len(self.trail_positions)))
                color = (*self.trail_color[:3], alpha)
                pos1 = (self.trail_positions[i][0] - camera_offset[0], 
                        self.trail_positions[i][1] - camera_offset[1])
                pos2 = (self.trail_positions[i + 1][0] - camera_offset[0], 
                        self.trail_positions[i + 1][1] - camera_offset[1])
                # Calculate width based on position (thicker toward the ball)
                width = int(1 + (i / len(self.trail_positions)) * 3)
                pygame.draw.line(screen, color, pos1, pos2, width)
        
        # Draw velocity-based trail when moving fast
        speed = (self.vel_x**2 + self.vel_y**2)**0.5
        if speed > 1.0:  # Only show velocity trail when moving fast enough
            # Create a surface for alpha blending if the game has one
            alpha_surface = None
            if hasattr(self, 'game') and hasattr(self.game, 'alpha_surface'):
                alpha_surface = self.game.alpha_surface
            else:
                # Fall back to the screen if no alpha surface is available
                alpha_surface = screen
                
            trail_length = min(10, int(speed))
            for i in range(trail_length):
                # Calculate trail position
                t = i / trail_length
                trail_x = self.x - self.vel_x * t * 0.5
                trail_y = self.y - self.vel_y * t * 0.5
                
                # Calculate trail opacity
                alpha = int(255 * (1 - t))
                trail_radius = self.radius * (1 - t * 0.7)
                
                # Draw trail circle
                pygame.draw.circle(
                    alpha_surface,
                    (*self.color[:3], alpha) if len(self.color) == 3 else self.color,
                    (int(trail_x - camera_offset[0]), int(trail_y - camera_offset[1])),
                    int(trail_radius)
                )
        
        # Draw glow effect
        if self.glow_radius > 0:
            # Create a surface for the glow with alpha
            glow_surface = pygame.Surface((self.glow_radius * 2, self.glow_radius * 2), pygame.SRCALPHA)
            # Draw radial gradient for glow
            pygame.draw.circle(glow_surface, self.glow_color, (self.glow_radius, self.glow_radius), self.glow_radius)
            # Draw the glow surface on the screen
            screen.blit(glow_surface, (self.x - self.glow_radius - camera_offset[0], self.y - self.glow_radius - camera_offset[1]), special_flags=pygame.BLEND_ALPHA_SDL2)
            
        # Calculate pulsing size
        pulse_radius = self.radius + self.pulse_amount * self.pulse_strength
            
        # Draw the ball itself
        pygame.draw.circle(screen, self.color, (int(self.x - camera_offset[0]), int(self.y - camera_offset[1])), int(pulse_radius))
        
        # Draw pulse outline if pulsing
        if self.pulse_amount > 0.1 and self.pulse_strength > 0:
            pygame.draw.circle(screen, self.pulse_color, (int(self.x - camera_offset[0]), int(self.y - camera_offset[1])), int(pulse_radius), 2)
    
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
        # Update previous position to avoid physics artifacts
        self.prev_x = x
        self.prev_y = y
        # Clear the trail when teleporting
        self.trail_positions = [] 


class EnhancedBall(Ball):
    """Enhanced version of the player ball with improved physics and effects."""
    
    def __init__(self, x, y, radius=15, color=BLUE):
        """Initialize enhanced ball with position, radius and color."""
        super().__init__(x, y, radius, color)
        # Additional EnhancedBall specific initialization can go here