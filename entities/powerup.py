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
    
    def draw(self, surface, camera_offset=(0, 0)):
        """Draw the powerup on the surface."""
        # Calculate adjusted position
        adjusted_x = self.x - camera_offset[0]
        adjusted_y = self.y - camera_offset[1]
        
        # Draw pulsing outer glow
        glow_radius = self.radius * (1.0 + 0.2 * math.sin(self.pulse_timer * 5))
        glow_surf = pygame.Surface((int(glow_radius * 3), int(glow_radius * 3)), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.color[:3], 100), (int(glow_radius * 1.5), int(glow_radius * 1.5)), int(glow_radius * 1.2))
        surface.blit(glow_surf, (adjusted_x - glow_radius * 1.5, adjusted_y - glow_radius * 1.5), special_flags=pygame.BLEND_ADD)
        
        # Draw main circle
        pygame.draw.circle(surface, self.color, (int(adjusted_x), int(adjusted_y)), int(self.radius))
        
        # Draw icon or symbol based on powerup type
        if self.type == "energy":
            # Draw a lightning bolt or battery icon
            icon_size = self.radius * 0.8
            # Simple lightning bolt - adjust as needed
            points = [
                (adjusted_x - icon_size * 0.3, adjusted_y - icon_size * 0.5),
                (adjusted_x + icon_size * 0.1, adjusted_y - icon_size * 0.1),
                (adjusted_x - icon_size * 0.1, adjusted_y + 0),
                (adjusted_x + icon_size * 0.3, adjusted_y + icon_size * 0.5),
                (adjusted_x + 0, adjusted_y + 0),
                (adjusted_x + icon_size * 0.2, adjusted_y - icon_size * 0.2)
            ]
            pygame.draw.polygon(surface, (255, 255, 0), points)
            
        elif self.type == "speed":
            # Draw speed arrows
            arrow_size = self.radius * 0.6
            arrow_width = arrow_size * 0.3
            for offset in [-arrow_size * 0.7, 0, arrow_size * 0.7]:
                points = [
                    (adjusted_x - arrow_size + offset, adjusted_y),
                    (adjusted_x - arrow_size * 0.5 + offset, adjusted_y - arrow_width),
                    (adjusted_x - arrow_size * 0.5 + offset, adjusted_y + arrow_width)
                ]
                pygame.draw.polygon(surface, (255, 255, 255), points)
            
        elif self.type == "size":
            # Draw a resize symbol
            pygame.draw.circle(surface, (255, 255, 255), (int(adjusted_x), int(adjusted_y)), int(self.radius * 0.5), 2)
            
        elif self.type == "time":
            # Draw a clock symbol
            pygame.draw.circle(surface, (255, 255, 255), (int(adjusted_x), int(adjusted_y)), int(self.radius * 0.6), 1)
            # Draw clock hands
            angle = math.radians(self.rotation)
            hand_length = self.radius * 0.5
            end_x = adjusted_x + math.cos(angle) * hand_length
            end_y = adjusted_y + math.sin(angle) * hand_length
            pygame.draw.line(surface, (255, 255, 255), (adjusted_x, adjusted_y), (end_x, end_y), 2)
    
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