import pygame
from utils.constants import WHITE, BLACK

# Surface types and their properties
SURFACE_TYPES = {
    "normal": {"color": WHITE, "friction": 0.99},
    "ice": {"color": (200, 200, 255), "friction": 0.995},
    "mud": {"color": (139, 69, 19), "friction": 0.9},
    "bouncy": {"color": (255, 105, 180), "friction": 1.01},  # Bouncy actually increases velocity slightly
    "deadly": {"color": (255, 0, 0), "friction": 0.99}  # Deadly surfaces cause level reset
}

class Surface:
    """A surface with custom properties that the ball can move on."""
    
    def __init__(self, x, y, width, height, surface_type="normal"):
        self.rect = pygame.Rect(x, y, width, height)
        self.type = surface_type
        
        if surface_type in SURFACE_TYPES:
            self.color = SURFACE_TYPES[surface_type]["color"]
            self.friction = SURFACE_TYPES[surface_type]["friction"]
        else:
            # Default to normal if type not found
            self.color = SURFACE_TYPES["normal"]["color"]
            self.friction = SURFACE_TYPES["normal"]["friction"]
            
    def draw(self, surface):
        """Draw the surface."""
        pygame.draw.rect(surface, self.color, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 1)  # Border
    
    def handle_collision(self, ball):
        """
        Check if the ball is on this surface and return the friction value.
        For deadly surfaces, returns "deadly" to signal level reset.
        """
        if self.rect.collidepoint(ball.x, ball.y):
            if self.type == "deadly":
                return "deadly"
            else:
                return self.friction
        return None 