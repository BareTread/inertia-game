import pygame
import math
from utils.constants import GREEN

class Target:
    def __init__(self, x, y, radius=20, points=100, required=True):
        self.x = x
        self.y = y
        self.radius = radius
        self.points = points
        self.required = required
        self.color = GREEN if required else (200, 200, 0)
        self.pulse_timer = 0
        self.pulse_amount = 0
        self.collected = False
        self.collection_animation = 0
        self.collection_duration = 0.5
        self.glow_radius = radius * 1.5
        self.glow_color = (*self.color[:3], 100)  # Semi-transparent glow
        self.hit = False  # Explicitly initialize as not hit
        self.game = None  # Will be set by the game
        
    def update(self, dt):
        """Update target animation"""
        if self.hit:
            return
            
        # Update pulse animation
        self.pulse_timer += dt
        
    def draw(self, surface, camera_offset=(0, 0)):
        """Draw the target with enhanced visuals"""
        if self.hit:
            return
            
        # Calculate position with camera offset
        adjusted_x = self.x - camera_offset[0]
        adjusted_y = self.y - camera_offset[1]
            
        # Calculate pulse effect
        pulse = math.sin(self.pulse_timer * 3) * 0.1 + 0.9
        current_radius = int(self.radius * pulse)
        
        # Draw glow
        glow_surface = pygame.Surface((self.glow_radius * 4, self.glow_radius * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, self.glow_color, 
                          (self.glow_radius * 2, self.glow_radius * 2), self.glow_radius * 2)
        surface.blit(glow_surface, (adjusted_x - self.glow_radius * 2, adjusted_y - self.glow_radius * 2), 
                    special_flags=pygame.BLEND_ADD)
        
        # Draw main target
        pygame.draw.circle(surface, self.color, (int(adjusted_x), int(adjusted_y)), current_radius)
        
        # Draw concentric circles
        for i in range(1, 4):
            ring_radius = current_radius * (1 - i * 0.25)
            ring_width = max(1, int(3 - i))
            pygame.draw.circle(surface, (255, 255, 255), (int(adjusted_x), int(adjusted_y)), 
                              int(ring_radius), ring_width)
        
        # Draw points value for non-required targets
        if not self.required and self.game and hasattr(self.game, 'small_font'):
            points_text = self.game.small_font.render(f"{self.points}", True, (255, 255, 255))
            text_rect = points_text.get_rect(center=(adjusted_x, adjusted_y))
            surface.blit(points_text, text_rect)
    
    def check_collision(self, ball):
        """Check if the ball is colliding with this target"""
        if self.hit:
            return False
            
        # Calculate distance between centers
        dx = ball.x - self.x
        dy = ball.y - self.y
        distance_squared = dx**2 + dy**2
        
        # Check if collision occurred
        collision_distance = ball.radius + self.radius
        if distance_squared < collision_distance**2:
            # Mark the target as hit
            self.hit = True
            
            # Create particle effect if game reference exists
            if self.game and hasattr(self.game, 'particle_system'):
                # Create particles at target position
                self.game.particle_system.create_particles(
                    self.x, self.y,
                    20,  # Number of particles
                    self.color,  # Use target color
                    min_speed=30,
                    max_speed=150,
                    min_lifetime=0.3,
                    max_lifetime=1.0
                )
                
                # Add points/score if game has score attribute
                if hasattr(self.game, 'score'):
                    self.game.score += self.points
                    
                    # Show floating score text
                    if hasattr(self.game, 'floating_text'):
                        self.game.floating_text.add_text(
                            f"+{self.points}",
                            self.x, self.y,
                            color=(255, 255, 200),
                            size=20,
                            lifetime=1.0,
                            velocity=(0, -50)
                        )
            
            return True
        
        return False
    
    def get_position(self):
        """Return the current position of the target."""
        return (self.x, self.y)
    
    def set_position(self, position):
        """Set the position of the target."""
        self.x, self.y = position 