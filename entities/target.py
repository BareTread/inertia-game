import pygame
import math
from utils.constants import GREEN, RED, WIDTH, HEIGHT
from utils.helpers import circle_circle_collision

class Target:
    """A target that the player needs to hit to complete the level."""
    
    def __init__(self, x, y, radius, points=100, required=True, color=None):
        self.x = x
        self.y = y
        self.radius = radius
        self.points = points
        self.required = required  # Whether this target is required to complete the level
        self.hit = False
        self.pulse_timer = 0
        self.pulse_amount = 0
        self.color = color or (GREEN if required else RED)
        self.glow_radius = radius * 1.5
        self.glow_color = (*self.color[:3], 100)  # Semi-transparent glow
    
    def update(self, dt):
        """Update the target's animation."""
        # Update pulse animation
        self.pulse_timer += dt
        self.pulse_amount = math.sin(self.pulse_timer * 3) * 2
    
    def draw(self, surface, camera_offset=(0, 0)):
        """Draw the target on the given surface."""
        # Calculate adjusted position
        adjusted_x = self.x - camera_offset[0]
        adjusted_y = self.y - camera_offset[1]
        
        # Calculate current radius with pulse effect
        current_radius = self.radius + self.pulse_amount
        
        # Draw glow effect
        glow_surf = pygame.Surface((int(self.glow_radius * 2), int(self.glow_radius * 2)), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, self.glow_color, (int(self.glow_radius), int(self.glow_radius)), int(self.glow_radius))
        surface.blit(glow_surf, (adjusted_x - self.glow_radius, adjusted_y - self.glow_radius), special_flags=pygame.BLEND_ADD)
        
        # Draw main target
        pygame.draw.circle(surface, self.color, (int(adjusted_x), int(adjusted_y)), int(current_radius))
        
        # Draw inner circle
        inner_radius = current_radius * 0.7
        pygame.draw.circle(surface, (255, 255, 255), (int(adjusted_x), int(adjusted_y)), int(inner_radius))
        
        # Draw center dot
        center_radius = current_radius * 0.3
        pygame.draw.circle(surface, self.color, (int(adjusted_x), int(adjusted_y)), int(center_radius))
        
        # Add pulsing outline for required targets
        if self.required and not self.hit:
            outline_radius = self.radius + 5 + math.sin(self.pulse_timer * 2) * 3
            pygame.draw.circle(
                surface,
                (255, 255, 100),
                (int(adjusted_x), int(adjusted_y)),
                int(outline_radius),
                2
            )
    
    def check_collision(self, ball):
        """
        Check if the ball is colliding with this target.
        Returns (collision, normal_x, normal_y) where normal is the collision normal vector.
        """
        return circle_circle_collision(
            ball.x, ball.y, ball.radius,
            self.x, self.y, self.radius
        )
    
    def handle_collision(self, ball):
        """
        Handle collision between the ball and this target.
        Returns True if the target was hit, False otherwise.
        """
        if self.hit:
            return False
            
        collision, _, _ = self.check_collision(ball)
        
        if collision:
            self.hit = True
            
            # Add immediate visual feedback
            if hasattr(ball, 'game') and hasattr(ball.game, 'particle_system'):
                # Create explosion effect using the target's color
                ball.game.particle_system.add_explosion(
                    self.x, self.y,
                    self.color,
                    count=20,
                    speed=100,
                    size_range=(2, 6),
                    lifetime_range=(0.5, 1.0),
                    glow=True
                )
                
                # Add small screen shake
                ball.game.particle_system.screen_shake(0.2)
                
                # Create a flash effect
                flash_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                flash_surface.fill((255, 255, 255, 50))  # Semi-transparent white
                
            # Play sound
            if hasattr(ball, 'game') and hasattr(ball.game, 'sound_manager'):
                ball.game.sound_manager.play_sound("target_hit")
            
            return True
        
        return False 