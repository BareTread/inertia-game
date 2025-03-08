import pygame
import math
from entities.target import Target
from utils.constants import GREEN

class EnhancedTarget(Target):
    def __init__(self, x, y, radius=20, points=100, required=True):
        super().__init__(x, y, radius)
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
        if not self.required:
            font = pygame.font.SysFont(None, 20)
            text = font.render(str(self.points), True, (0, 0, 0))
            text_rect = text.get_rect(center=(int(adjusted_x), int(adjusted_y)))
            surface.blit(text, text_rect)
    
    def check_collision(self, ball):
        """Check collision with enhanced feedback"""
        if self.hit:
            return False
            
        distance = math.sqrt((ball.x - self.x)**2 + (ball.y - self.y)**2)
        if distance < ball.radius + self.radius:
            self.hit = True
            
            # Add spectacular hit effect
            if self.game and hasattr(self.game, 'particle_system'):
                self.game.particle_system.add_explosion(
                    self.x, self.y,
                    self.color,
                    count=40,
                    speed_range=(3, 8),
                    size_range=(3, 7),
                    lifetime_range=(0.5, 1.2),
                    glow=True
                )
                
                # Add screen shake based on target importance
                shake_amount = 5 if self.required else 3
                self.game.particle_system.screen_shake(shake_amount)
            
            # Add floating score text
            if hasattr(self.game, 'add_floating_text'):
                self.game.add_floating_text(f"+{self.points}", self.x, self.y, (255, 255, 0))
            
            # Play sound
            from utils.sound import play_sound
            play_sound("target_hit", 1.0)
            
            return True
        return False 

    def get_position(self):
        """Return the current position of the target."""
        return (self.x, self.y)
    
    def set_position(self, position):
        """Set the position of the target."""
        self.x, self.y = position 