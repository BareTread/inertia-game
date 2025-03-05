import pygame
import math
from utils.constants import GREEN, RED
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
    
    def draw(self, surface):
        """Draw the target on the given surface."""
        # Calculate current radius with pulse effect
        current_radius = self.radius + self.pulse_amount
        
        # Draw glow effect
        glow_surf = pygame.Surface((int(self.glow_radius * 2), int(self.glow_radius * 2)), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, self.glow_color, (int(self.glow_radius), int(self.glow_radius)), int(self.glow_radius))
        surface.blit(glow_surf, (self.x - self.glow_radius, self.y - self.glow_radius), special_flags=pygame.BLEND_ADD)
        
        # Draw main target
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(current_radius))
        
        # Draw inner circle
        inner_radius = current_radius * 0.7
        pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), int(inner_radius))
        
        # Draw center dot
        center_radius = current_radius * 0.3
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(center_radius))
        
        # Add pulsing outline for required targets
        if self.required and not self.hit:
            outline_radius = self.radius + 5 + math.sin(self.pulse_timer * 2) * 3
            pygame.draw.circle(
                surface,
                (255, 255, 100),
                (int(self.x), int(self.y)),
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
            return True
        
        return False 