import pygame
import math
from entities.wall import Wall
from utils.constants import BLACK, WHITE

class EnhancedWall(Wall):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.impact_timer = 0
        self.impact_duration = 0.3
        self.impact_color = None
        
    def get_position(self):
        """Return the current position of the wall."""
        return (self.rect.x, self.rect.y)
    
    def set_position(self, position):
        """Set the position of the wall."""
        self.rect.x, self.rect.y = position
        
    def update(self, dt):
        """Update wall state"""
        if self.impact_timer > 0:
            self.impact_timer -= dt
            
    def draw(self, surface, camera_offset=(0, 0)):
        """Draw the wall with impact effect"""
        # Calculate adjusted position with camera offset
        adjusted_x = self.rect.left - camera_offset[0]
        adjusted_y = self.rect.top - camera_offset[1]
        
        # Draw normal wall with a bright, highly visible color
        wall_color = (20, 40, 220)  # Bright blue color for high visibility
        pygame.draw.rect(surface, wall_color, 
                        (adjusted_x, adjusted_y, self.rect.width, self.rect.height))
        
        # Add border with contrasting color for better visibility
        pygame.draw.rect(surface, (255, 255, 0), 
                        (adjusted_x, adjusted_y, self.rect.width, self.rect.height), 2)
        
        # Draw impact highlight if active
        if self.impact_timer > 0:
            # Calculate alpha based on remaining time
            alpha = int(255 * (self.impact_timer / self.impact_duration))
            
            # Draw a highlight rectangle
            highlight_rect = pygame.Rect(adjusted_x - 3, adjusted_y - 3, 
                                        self.rect.width + 6, self.rect.height + 6)
            
            highlight_surface = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
            highlight_color = (*self.impact_color[:3], alpha)
            pygame.draw.rect(highlight_surface, highlight_color, 
                           (0, 0, highlight_rect.width, highlight_rect.height), 3)
            
            surface.blit(highlight_surface, highlight_rect.topleft)
            
    def check_collision(self, ball):
        """Check and handle ball collision with improved feedback"""
        # Original collision detection logic
        closest_x = max(self.rect.left, min(ball.x, self.rect.right))
        closest_y = max(self.rect.top, min(ball.y, self.rect.bottom))
        
        distance_x = ball.x - closest_x
        distance_y = ball.y - closest_y
        distance_squared = distance_x**2 + distance_y**2
        
        if distance_squared < ball.radius**2:
            # Handle collision physics
            overlap = ball.radius - math.sqrt(distance_squared)
            
            # Normalize direction
            if distance_squared > 0:
                norm_x = distance_x / math.sqrt(distance_squared)
                norm_y = distance_y / math.sqrt(distance_squared)
            else:
                norm_x, norm_y = 1, 0
                
            # Move ball out of collision
            ball.x += norm_x * overlap
            ball.y += norm_y * overlap
            
            # Calculate impact speed for effects
            impact_speed = math.sqrt(ball.vel_x**2 + ball.vel_y**2)
            
            # Bounce with improved feel
            dot_product = ball.vel_x * norm_x + ball.vel_y * norm_y
            ball.vel_x -= 1.8 * dot_product * norm_x
            ball.vel_y -= 1.8 * dot_product * norm_y
            
            # Add visual impact effect
            self.impact_timer = self.impact_duration
            self.impact_color = (255, 255, 255)  # White flash
            
            # Add particle effect at collision point
            if hasattr(ball, 'game') and ball.game and hasattr(ball.game, 'particle_system'):
                particle_system = ball.game.particle_system
                
                # Calculate actual collision point
                collision_x = ball.x - norm_x * ball.radius
                collision_y = ball.y - norm_y * ball.radius
                
                # Number of particles based on impact speed
                particle_count = int(min(30, max(5, impact_speed * 3)))
                
                # Add particles
                particle_system.add_explosion(
                    collision_x, collision_y,
                    (255, 255, 255),  # White particles
                    count=particle_count,
                    speed=100,  # Fixed speed parameter
                    size_range=(1, 4),
                    lifetime_range=(0.2, 0.5),
                    glow=impact_speed > 5
                )
                
                # Add screen shake based on impact
                shake_amount = min(12, impact_speed * 0.8)
                particle_system.screen_shake(shake_amount)
            
            # Play sound with volume based on impact
            from utils.sound import play_sound
            volume = min(1.0, impact_speed / 10)
            play_sound("collision", volume)
            
            return True
        return False 