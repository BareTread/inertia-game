import pygame

class FloatingText:
    def __init__(self, text, x, y, color=(255, 255, 255), size=24, 
                 velocity=(0, -2), lifetime=1.0, fade=True):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.vel_x = velocity[0]
        self.vel_y = velocity[1]
        self.lifetime = lifetime
        self.age = 0
        self.fade = fade
        self.font = pygame.font.SysFont(None, size)
        
    def update(self, dt):
        """Update position and age"""
        self.age += dt
        self.x += self.vel_x * dt * 60
        self.y += self.vel_y * dt * 60
        
    def draw(self, surface, camera_offset=(0, 0)):
        """Draw the floating text"""
        if self.age >= self.lifetime:
            return
            
        # Calculate adjusted position
        adjusted_x = self.x - camera_offset[0]
        adjusted_y = self.y - camera_offset[1]
            
        # Calculate alpha based on remaining lifetime
        alpha = 255
        if self.fade:
            fade_time = 0.3
            if self.age > self.lifetime - fade_time:
                alpha = int(255 * (self.lifetime - self.age) / fade_time)
        
        # Render text with appropriate alpha
        color_with_alpha = (*self.color[:3], alpha)
        text_surface = self.font.render(self.text, True, color_with_alpha)
        
        # Create a surface with alpha
        text_surface_alpha = pygame.Surface(text_surface.get_rect().size, pygame.SRCALPHA)
        text_surface_alpha.fill((0, 0, 0, 0))
        text_surface_alpha.blit(text_surface, (0, 0))
        
        # Draw to main surface
        text_rect = text_surface.get_rect(center=(int(adjusted_x), int(adjusted_y)))
        surface.blit(text_surface_alpha, text_rect)
        
    @property
    def is_expired(self):
        """Check if the floating text has expired"""
        return self.age >= self.lifetime 