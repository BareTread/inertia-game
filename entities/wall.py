import pygame
import math
from utils.constants import BLACK, WALL_BORDER_COLOR, WALL_BORDER_WIDTH

class Wall:
    """Wall object that blocks the ball."""
    
    def __init__(self, x, y, width, height, color=BLACK):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.impact_timer = 0
        self.impact_duration = 0.2  # How long impact effect lasts
        self.impact_color = None    # Will be set during collision
    
    def update(self, dt):
        """Update wall state, like impact visual effects."""
        if self.impact_timer > 0:
            self.impact_timer -= dt
    
    def draw(self, surface, camera_offset=(0, 0)):
        """Draw the wall with a visible border."""
        # Draw the main wall
        adjusted_x = self.rect.left - camera_offset[0]
        adjusted_y = self.rect.top - camera_offset[1]
        
        # Use a more visible color for the wall
        fill_color = (50, 50, 120)  # Darker blue for the wall fill
        
        # Draw the wall itself with a more visible color
        pygame.draw.rect(
            surface, 
            fill_color,
            (adjusted_x, adjusted_y, self.rect.width, self.rect.height)
        )
        
        # Draw a border around the wall with increased width for better visibility
        pygame.draw.rect(
            surface, 
            WALL_BORDER_COLOR,
            (adjusted_x, adjusted_y, self.rect.width, self.rect.height),
            WALL_BORDER_WIDTH + 1  # Increase border width
        )
        
        # Add highlight effect to make it more visible
        highlight_color = (120, 120, 255, 100)  # Light blue with some transparency
        if self.impact_timer > 0:
            # Use impact color if wall was recently hit
            pygame.draw.rect(
                surface,
                self.impact_color,
                (adjusted_x, adjusted_y, self.rect.width, self.rect.height),
                1
            )
    
    def check_collision(self, ball):
        """Check if the ball is colliding with this wall."""
        # Find the closest point on the rect to the ball
        closest_x = max(self.rect.left, min(ball.x, self.rect.right))
        closest_y = max(self.rect.top, min(ball.y, self.rect.bottom))
        
        # Calculate distance from closest point to circle center
        distance_x = ball.x - closest_x
        distance_y = ball.y - closest_y
        distance_squared = distance_x**2 + distance_y**2
        
        # Check collision
        return distance_squared < ball.radius**2
    
    def handle_collision(self, ball):
        """
        Handle collision with a ball.
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
            
            # Improve bounce feel with better energy conservation
            bounce_factor = 1.5  # Decrease from 1.8 for more controlled bounces
            energy_preservation = 0.85 + (ball.get_speed() * 0.01)  # Speed-based energy preservation
            
            ball.vel_x -= bounce_factor * dot_product * norm_x * energy_preservation
            ball.vel_y -= bounce_factor * dot_product * norm_y * energy_preservation
            
            # Add visual and audio feedback
            collision_speed = ball.get_speed()
            if collision_speed > 2.0:
                # Set impact effect
                self.impact_timer = self.impact_duration
                
                # Make impact color based on collision speed
                intensity = min(255, int(collision_speed * 20))
                self.impact_color = (intensity, intensity, 255)
                
                # Create impact particles
                if hasattr(ball, 'game') and hasattr(ball.game, 'particle_system'):
                    num_particles = min(10, int(collision_speed))
                    collision_point = [
                        ball.x + ball.radius * norm_x,
                        ball.y + ball.radius * norm_y
                    ]
                    
                    ball.game.particle_system.create_impact(
                        collision_point[0], collision_point[1],
                        num_particles=num_particles,
                        color=self.color,
                        velocity=[-ball.vel_x * 0.2, -ball.vel_y * 0.2]
                    )
                    
                    # Add screen shake based on impact force
                    shake_amount = min(0.5, collision_speed * 0.05)
                    ball.game.particle_system.screen_shake(shake_amount)
                    
                    # Play sound with volume based on impact
                    if hasattr(ball.game, 'sound_manager'):
                        volume = min(1.0, collision_speed / 10.0)
                        ball.game.sound_manager.play_sound("wall_hit", volume)
            
            return True
        
        return False 