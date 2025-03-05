import pygame
import math
from typing import Tuple, Dict, Any, Optional

class TutorialElement:
    """A class representing tutorial elements like arrows, hints, and other UI guidance elements."""
    
    def __init__(self, element_type: str, data: Dict[str, Any]):
        """Initialize a tutorial element.
        
        Args:
            element_type: The type of tutorial element (e.g., 'arrow', 'hint')
            data: A dictionary containing element-specific data
        """
        self.type = element_type
        self.data = data
        self.animation_timer = 0
        
        # Set default values
        if element_type == "arrow":
            self.start = data.get("start", (0, 0))
            self.end = data.get("end", (100, 100))
            self.text = data.get("text", "")
            self.color = data.get("color", (255, 255, 0))
            self.pulse_speed = data.get("pulse_speed", 0.005)
        
    def update(self, dt: float) -> None:
        """Update the animation state.
        
        Args:
            dt: Delta time in seconds
        """
        self.animation_timer += dt
    
    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw the tutorial element on the given surface.
        
        Args:
            surface: The surface to draw on
            font: The font to use for text
        """
        if self.type == "arrow":
            self._draw_arrow(surface, font)
    
    def _draw_arrow(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw an arrow tutorial element.
        
        Args:
            surface: The surface to draw on
            font: The font to use for text
        """
        start_pos = self.start
        end_pos = self.end
        color = self.color
        text = self.text
        
        # Calculate arrow properties
        arrow_length = math.sqrt((end_pos[0] - start_pos[0])**2 + (end_pos[1] - start_pos[1])**2)
        direction_x = (end_pos[0] - start_pos[0]) / arrow_length if arrow_length > 0 else 0
        direction_y = (end_pos[1] - start_pos[1]) / arrow_length if arrow_length > 0 else 0
        
        # Add animation to make it pulsate
        pulse = math.sin(pygame.time.get_ticks() * self.pulse_speed) * 0.2 + 0.8  # 0.6 to 1.0 scale factor
        thickness = int(max(3, 5 * pulse))
        
        # Draw the line
        pygame.draw.line(
            surface, 
            color, 
            start_pos,
            (end_pos[0] - direction_x * 20, end_pos[1] - direction_y * 20),  # Cut short for arrowhead
            thickness
        )
        
        # Draw the arrowhead
        arrow_size = 15 * pulse
        angle = math.atan2(direction_y, direction_x)
        arr_x1 = end_pos[0] - arrow_size * math.cos(angle - math.pi/6)
        arr_y1 = end_pos[1] - arrow_size * math.sin(angle - math.pi/6)
        arr_x2 = end_pos[0] - arrow_size * math.cos(angle + math.pi/6)
        arr_y2 = end_pos[1] - arrow_size * math.sin(angle + math.pi/6)
        
        pygame.draw.polygon(
            surface,
            color,
            [(end_pos[0], end_pos[1]), (arr_x1, arr_y1), (arr_x2, arr_y2)]
        )
        
        # Draw the text if present
        if text:
            text_color = color
            text_surface = font.render(text, True, text_color)
            text_pos = (
                (start_pos[0] + end_pos[0]) // 2 - text_surface.get_width() // 2,
                (start_pos[1] + end_pos[1]) // 2 - 30  # Offset above the line
            )
            
            # Add a subtle background for better readability
            text_bg = pygame.Surface((text_surface.get_width() + 10, text_surface.get_height() + 10))
            text_bg.fill((30, 30, 30))
            text_bg.set_alpha(150)
            surface.blit(text_bg, (text_pos[0] - 5, text_pos[1] - 5))
            
            # Draw with a slight glow effect
            glow_surface = pygame.Surface((text_surface.get_width() + 8, text_surface.get_height() + 8), pygame.SRCALPHA)
            glow_text = font.render(text, True, (color[0]//2, color[1]//2, color[2]//2))
            for offset_x, offset_y in [(0,1), (1,0), (0,-1), (-1,0)]:
                glow_surface.blit(glow_text, (4 + offset_x, 4 + offset_y))
            
            surface.blit(glow_surface, (text_pos[0] - 4, text_pos[1] - 4))
            surface.blit(text_surface, text_pos) 