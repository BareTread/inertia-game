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
        self.x += self.vel_x
        self.y += self.vel_y
        
        # Update trail
        self.trail_timer += dt
        if self.trail_timer >= self.trail_interval:
            self.trail_timer = 0
            self.trail_positions.append((self.x, self.y))
            
            # Limit trail length
            if len(self.trail_positions) > self.max_trail_length:
                self.trail_positions.pop(0)
                
        # Clamp ball position to prevent it from going off-screen
        self.x = clamp(self.x, self.radius, WIDTH - self.radius)
        self.y = clamp(self.y, self.radius, HEIGHT - self.radius)
        
    def draw(self, surface):
        """Draw the ball and its trail on the given surface."""
        # Draw trail
        if len(self.trail_positions) > 1:
            for i in range(1, len(self.trail_positions)):
                # Calculate alpha value based on position in trail
                alpha = int(255 * (i / len(self.trail_positions)))
                # Calculate size based on position in trail
                size = int(self.radius * 0.8 * (i / len(self.trail_positions)))
                
                prev_pos = self.trail_positions[i-1]
                curr_pos = self.trail_positions[i]
                
                # Draw trail segment with gradient color
                speed = math.sqrt(self.vel_x**2 + self.vel_y**2)
                color_intensity = min(255, int(speed * 10))
                trail_color = (100, 100, 255, alpha)  # Blue trail
                
                pygame.draw.line(
                    surface,
                    trail_color,
                    prev_pos,
                    curr_pos,
                    max(1, size)
                )
        
        # Calculate current radius with pulse effect
        current_radius = self.radius + self.pulse_amount
        
        # Draw dynamic glow effect based on speed
        speed = math.sqrt(self.vel_x**2 + self.vel_y**2)
        glow_intensity = min(150, int(50 + speed * 5))
        dynamic_glow_radius = self.glow_radius + speed * 0.2
        
        # Create a surface for the glow with per-pixel alpha
        glow_surf = pygame.Surface((int(dynamic_glow_radius * 2), int(dynamic_glow_radius * 2)), pygame.SRCALPHA)
        
        # Draw multiple circles with decreasing alpha for a better glow effect
        for r in range(int(dynamic_glow_radius), 0, -5):
            alpha = int(glow_intensity * (r / dynamic_glow_radius))
            pygame.draw.circle(
                glow_surf, 
                (100, 150, 255, alpha), 
                (int(dynamic_glow_radius), int(dynamic_glow_radius)), 
                r
            )
        
        # Blit the glow surface
        surface.blit(
            glow_surf, 
            (self.x - dynamic_glow_radius, self.y - dynamic_glow_radius), 
            special_flags=pygame.BLEND_ADD
        )
        
        # Draw main ball
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(current_radius))
        
        # Draw velocity vector line
        if abs(self.vel_x) > 0.1 or abs(self.vel_y) > 0.1:
            # Calculate normalized velocity vector
            vel_length = math.sqrt(self.vel_x**2 + self.vel_y**2)
            norm_vel_x = self.vel_x / vel_length if vel_length > 0 else 0
            norm_vel_y = self.vel_y / vel_length if vel_length > 0 else 0
            
            # Draw line in the direction of movement
            line_length = min(vel_length * 3, self.radius * 2)
            end_x = self.x + norm_vel_x * line_length
            end_y = self.y + norm_vel_y * line_length
            
            pygame.draw.line(surface, RED, (self.x, self.y), (end_x, end_y), 2)
    
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