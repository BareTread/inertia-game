import pygame
import math
from utils.constants import YELLOW, BLUE, GREEN, PURPLE
from utils.helpers import circle_circle_collision

class PowerUp:
    """A power-up that provides special abilities when collected."""
    
    # Power-up types and their colors
    TYPES = {
        "energy": {"color": YELLOW, "description": "Restores energy"},
        "speed": {"color": BLUE, "description": "Increases speed"},
        "size": {"color": GREEN, "description": "Changes ball size"},
        "time": {"color": PURPLE, "description": "Adds time"}
    }
    
    def __init__(self, x, y, powerup_type="energy", value=50, radius=15):
        self.x = x
        self.y = y
        self.radius = radius
        self.type = powerup_type
        self.value = value
        self.collected = False
        
        # Get color from type
        self.color = self.TYPES.get(powerup_type, self.TYPES["energy"])["color"]
        
        # Animation properties
        self.pulse_timer = 0
        self.pulse_amount = 0
        self.rotation = 0
        self.glow_radius = radius * 1.5
        self.glow_color = (*self.color[:3], 100)  # Semi-transparent glow
    
    def update(self, dt):
        """Update the power-up's animation."""
        if self.collected:
            return
            
        # Update pulse animation
        self.pulse_timer += dt
        self.pulse_amount = math.sin(self.pulse_timer * 3) * 2
        
        # Update rotation
        self.rotation += 90 * dt  # 90 degrees per second
        if self.rotation >= 360:
            self.rotation -= 360
    
    def draw(self, surface):
        """Draw the power-up on the given surface."""
        if self.collected:
            return
            
        # Calculate current radius with pulse effect
        current_radius = self.radius + self.pulse_amount
        
        # Draw glow effect
        glow_surf = pygame.Surface((int(self.glow_radius * 2), int(self.glow_radius * 2)), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, self.glow_color, (int(self.glow_radius), int(self.glow_radius)), int(self.glow_radius))
        surface.blit(glow_surf, (self.x - self.glow_radius, self.y - self.glow_radius), special_flags=pygame.BLEND_ADD)
        
        # Draw main circle
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(current_radius))
        
        # Draw a symbol based on the power-up type
        if self.type == "energy":
            # Draw a lightning bolt
            points = [
                (self.x - current_radius * 0.3, self.y - current_radius * 0.5),
                (self.x + current_radius * 0.1, self.y - current_radius * 0.1),
                (self.x - current_radius * 0.1, self.y + current_radius * 0.1),
                (self.x + current_radius * 0.3, self.y + current_radius * 0.5)
            ]
            pygame.draw.lines(surface, (255, 255, 255), False, points, 2)
            
        elif self.type == "speed":
            # Draw a fast-forward symbol
            pygame.draw.polygon(surface, (255, 255, 255), [
                (self.x - current_radius * 0.4, self.y - current_radius * 0.3),
                (self.x - current_radius * 0.1, self.y),
                (self.x - current_radius * 0.4, self.y + current_radius * 0.3)
            ])
            pygame.draw.polygon(surface, (255, 255, 255), [
                (self.x, self.y - current_radius * 0.3),
                (self.x + current_radius * 0.3, self.y),
                (self.x, self.y + current_radius * 0.3)
            ])
            
        elif self.type == "size":
            # Draw a resize symbol
            pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), int(current_radius * 0.5), 2)
            
        elif self.type == "time":
            # Draw a clock symbol
            pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), int(current_radius * 0.6), 1)
            # Draw clock hands
            angle = math.radians(self.rotation)
            hand_length = current_radius * 0.5
            end_x = self.x + math.cos(angle) * hand_length
            end_y = self.y + math.sin(angle) * hand_length
            pygame.draw.line(surface, (255, 255, 255), (self.x, self.y), (end_x, end_y), 2)
    
    def check_collision(self, ball):
        """
        Check if the ball is colliding with this power-up.
        Returns (collision, normal_x, normal_y) where normal is the collision normal vector.
        """
        if self.collected:
            return False, 0, 0
            
        return circle_circle_collision(
            ball.x, ball.y, ball.radius,
            self.x, self.y, self.radius
        )
    
    def handle_collision(self, ball):
        """
        Handle collision between the ball and this power-up.
        Returns the power-up type and value if collected, False otherwise.
        """
        if self.collected:
            return False
            
        collision, _, _ = self.check_collision(ball)
        
        if collision:
            self.collected = True
            return {"type": self.type, "value": self.value}
        
        return False 