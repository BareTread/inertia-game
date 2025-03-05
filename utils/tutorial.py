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
        pulse = math.sin(pygame.time.get_ticks() * self.pulse_speed) * 0.15 + 0.85  # 0.7 to 1.0 scale factor
        thickness = int(max(2, 4 * pulse))
        
        # Create a smoother, more elegant arrow
        # Draw the main line with a gradient effect
        steps = 8
        for i in range(steps):
            progress = i / steps
            alpha = int(255 * (1 - progress) * pulse)
            current_color = (*color[:3], alpha)
            current_thickness = max(1, int(thickness * (1 - progress * 0.7)))
            
            # Draw line segment with decreasing thickness
            segment_start = (
                start_pos[0] + progress * (end_pos[0] - start_pos[0]) * 0.05,
                start_pos[1] + progress * (end_pos[1] - start_pos[1]) * 0.05
            )
            segment_end = (
                end_pos[0] - direction_x * 20 - (1 - progress) * (end_pos[0] - start_pos[0]) * 0.05,
                end_pos[1] - direction_y * 20 - (1 - progress) * (end_pos[1] - start_pos[1]) * 0.05
            )
            
            pygame.draw.line(
                surface, 
                current_color, 
                segment_start,
                segment_end,
                current_thickness
            )
        
        # Draw an improved arrowhead - larger and more visible
        arrow_size = 18 * pulse
        angle = math.atan2(direction_y, direction_x)
        
        # Calculate points for a better arrow shape
        arr_x1 = end_pos[0] - arrow_size * math.cos(angle - math.pi/7)
        arr_y1 = end_pos[1] - arrow_size * math.sin(angle - math.pi/7)
        arr_x2 = end_pos[0] - arrow_size * 0.7 * math.cos(angle)
        arr_y2 = end_pos[1] - arrow_size * 0.7 * math.sin(angle)
        arr_x3 = end_pos[0] - arrow_size * math.cos(angle + math.pi/7)
        arr_y3 = end_pos[1] - arrow_size * math.sin(angle + math.pi/7)
        
        # Draw arrowhead
        pygame.draw.polygon(
            surface,
            color,
            [(end_pos[0], end_pos[1]), (arr_x1, arr_y1), (arr_x2, arr_y2), (arr_x3, arr_y3)]
        )
        
        # Draw the text if present
        if text:
            # Calculate an appropriate position
            text_pos_x = (start_pos[0] + end_pos[0]) // 2
            text_pos_y = (start_pos[1] + end_pos[1]) // 2 - 25  # Position above the line
            
            # Create a better text style
            text_shadow = font.render(text, True, (0, 0, 0))
            text_surface = font.render(text, True, color)
            
            # Add a semi-transparent background panel
            text_width = text_surface.get_width()
            text_height = text_surface.get_height()
            padding = 8
            
            # Create panel with rounded corners
            panel = pygame.Surface((text_width + padding*2, text_height + padding*2), pygame.SRCALPHA)
            pygame.draw.rect(
                panel, 
                (0, 0, 0, 180),
                (0, 0, text_width + padding*2, text_height + padding*2),
                border_radius=10
            )
            
            # Add subtle border highlight
            pygame.draw.rect(
                panel, 
                (*color[:3], 100),
                (0, 0, text_width + padding*2, text_height + padding*2),
                width=2,
                border_radius=10
            )
            
            # Position everything
            panel_pos = (text_pos_x - text_width//2 - padding, text_pos_y - padding)
            text_shadow_pos = (text_pos_x - text_width//2 + 2, text_pos_y + 2)
            text_pos = (text_pos_x - text_width//2, text_pos_y)
            
            # Draw with a slight glow effect
            surface.blit(panel, panel_pos)
            surface.blit(text_shadow, text_shadow_pos)
            surface.blit(text_surface, text_pos) 