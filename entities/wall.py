import pygame
import math
from utils.constants import BLACK, WHITE

class Wall:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
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
        
        # If collision detected
        if distance_squared < ball.radius**2:
            # Calculate collision normal and penetration
            distance = math.sqrt(distance_squared)
            
            # Avoid division by zero
            if distance < 0.001:
                # Handle rare case of distance being almost zero
                normal_x, normal_y = 0, -1  # Default normal
                penetration = ball.radius
            else:
                normal_x = distance_x / distance
                normal_y = distance_y / distance
                penetration = ball.radius - distance
            
            # Position correction to prevent sticking
            correction_factor = penetration * 1.01  # Slight extra push to prevent sticking
            ball.x += normal_x * correction_factor
            ball.y += normal_y * correction_factor
            
            # Reflect velocity with energy loss
            dot_product = ball.vel_x * normal_x + ball.vel_y * normal_y
            
            # Only reflect if moving into the wall
            if dot_product < 0:
                restitution = 0.85  # Energy retention; 1.0 = perfect bounce
                
                # Calculate reflection velocity
                ball.vel_x -= (1 + restitution) * dot_product * normal_x
                ball.vel_y -= (1 + restitution) * dot_product * normal_y
                
                # Apply impact visual feedback
                self.impact_timer = self.impact_duration
                
                # Color based on impact force
                impact_force = -dot_product
                if impact_force > 10:
                    self.impact_color = (255, 50, 50)  # Strong impact (red)
                elif impact_force > 5:
                    self.impact_color = (255, 255, 50)  # Medium impact (yellow)
                else:
                    self.impact_color = (50, 255, 50)  # Light impact (green)
                
                # Create particles if game and ball have particle systems
                if hasattr(ball, 'game') and ball.game and hasattr(ball.game, 'particle_system'):
                    impact_point = (closest_x, closest_y)
                    
                    # Determine color based on impact force
                    particle_color = (255, 255, 255)
                    if impact_force > 12:
                        particle_color = (255, 100, 100)  # Red for hard impacts
                    elif impact_force > 6:
                        particle_color = (255, 255, 100)  # Yellow for medium impacts
                    
                    # Spawn more particles for harder impacts
                    particle_count = min(int(impact_force), 15)
                    
                    # Create impact particles
                    ball.game.particle_system.create_particles(
                        impact_point[0], impact_point[1], 
                        particle_count,
                        particle_color,
                        min_speed=impact_force * 0.5,
                        max_speed=impact_force * 1.5,
                        min_lifetime=0.2,
                        max_lifetime=0.5,
                        direction=(-normal_x, -normal_y),  # Reverse of normal
                        spread=0.7  # 0.7 radians spread
                    )
                
            return True
        
        return False 