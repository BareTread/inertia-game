import pygame
import math
from utils.constants import BLACK

class Wall:
    """Wall object that blocks the ball."""
    
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = BLACK
    
    def draw(self, surface):
        """Draw the wall."""
        pygame.draw.rect(surface, self.color, self.rect)
    
    def handle_collision(self, ball):
        """
        Check and handle collision with a ball.
        Returns True if collision occurred, False otherwise.
        """
        # Find the closest point on the rect to the ball
        closest_x = max(self.rect.left, min(ball.x, self.rect.right))
        closest_y = max(self.rect.top, min(ball.y, self.rect.bottom))
        
        # Calculate distance from closest point to circle center
        distance_x = ball.x - closest_x
        distance_y = ball.y - closest_y
        distance_squared = distance_x**2 + distance_y**2
        
        # Check collision
        if distance_squared < ball.radius**2:
            # Handle collision
            overlap = ball.radius - math.sqrt(distance_squared)
            
            # Normalize direction
            if distance_squared > 0:
                norm_x = distance_x / math.sqrt(distance_squared)
                norm_y = distance_y / math.sqrt(distance_squared)
            else:
                # Ball is exactly at the closest point, push in arbitrary direction
                norm_x, norm_y = 1, 0
                
            # Move ball out of collision
            ball.x += norm_x * overlap
            ball.y += norm_y * overlap
            
            # Bounce (with some energy loss)
            dot_product = ball.vel_x * norm_x + ball.vel_y * norm_y
            ball.vel_x -= 1.8 * dot_product * norm_x  # 1.8 makes it more bouncy like in original game
            ball.vel_y -= 1.8 * dot_product * norm_y
            
            return True
        
        return False 