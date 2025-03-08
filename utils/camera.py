import pygame
import math
from typing import Tuple, Optional

class Camera:
    def __init__(self, screen_width: int, screen_height: int):
        """
        Initialize the camera.
        
        Args:
            screen_width: Width of the screen
            screen_height: Height of the screen
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.position = (0, 0)  # Camera position (offset applied to entities)
        self.target_position = (0, 0)  # Position camera is moving towards
        self.lerp_factor = 5.0  # Higher values = faster camera movement (less smooth)
        
        # Deadzone settings (rectangular area in the center where camera won't move)
        self.deadzone_width = int(screen_width * 0.3)  # 30% of screen width
        self.deadzone_height = int(screen_height * 0.3)  # 30% of screen height
        
        # World boundaries (min_x, min_y, max_x, max_y)
        self.bounds = None  # Optional camera movement boundaries
    
    def set_target_position(self, target_position: Tuple[float, float]) -> None:
        """
        Set the position the camera should follow.
        
        Args:
            target_position: (x, y) position to follow
        """
        self.target_position = target_position
    
    def set_bounds(self, bounds: Tuple[float, float, float, float]) -> None:
        """
        Set camera movement boundaries.
        
        Args:
            bounds: (min_x, min_y, max_x, max_y) bounds
        """
        self.bounds = bounds
        
    def set_deadzone(self, width_percent: float, height_percent: float) -> None:
        """
        Set the camera deadzone as percentage of screen dimensions.
        
        Args:
            width_percent: Width of deadzone as percentage of screen width (0.0-1.0)
            height_percent: Height of deadzone as percentage of screen height (0.0-1.0)
        """
        self.deadzone_width = int(self.screen_width * max(0.0, min(1.0, width_percent)))
        self.deadzone_height = int(self.screen_height * max(0.0, min(1.0, height_percent)))
    
    def update(self, dt: float) -> None:
        """
        Update camera position based on target position.
        
        Args:
            dt: Delta time in seconds
        """
        # Calculate desired camera position (centered on target)
        target_x = self.target_position[0]
        target_y = self.target_position[1]
        
        # Apply deadzone
        if self.deadzone_width > 0 and self.deadzone_height > 0:
            # Calculate center position of the screen in world coordinates
            half_width = self.screen_width // 2
            half_height = self.screen_height // 2
            screen_center_x = self.position[0] + half_width
            screen_center_y = self.position[1] + half_height
            
            # Calculate deadzone rectangle in world coordinates
            deadzone_half_width = self.deadzone_width // 2
            deadzone_half_height = self.deadzone_height // 2
            
            deadzone_left = screen_center_x - deadzone_half_width
            deadzone_right = screen_center_x + deadzone_half_width
            deadzone_top = screen_center_y - deadzone_half_height
            deadzone_bottom = screen_center_y + deadzone_half_height
            
            # Determine desired camera position
            desired_x = self.position[0]
            desired_y = self.position[1]
            
            # Move camera horizontally if target is outside deadzone
            if target_x < deadzone_left:
                desired_x += target_x - deadzone_left
            elif target_x > deadzone_right:
                desired_x += target_x - deadzone_right
                
            # Move camera vertically if target is outside deadzone
            if target_y < deadzone_top:
                desired_y += target_y - deadzone_top
            elif target_y > deadzone_bottom:
                desired_y += target_y - deadzone_bottom
                
            target_x = desired_x
            target_y = desired_y
        
        # Use variable lerp factor based on distance
        distance = math.sqrt((target_x - self.position[0])**2 + (target_y - self.position[1])**2)
        lerp_factor = min(10.0, max(3.0, distance / 100.0)) * dt
        
        # Apply smooth movement using lerp
        new_x = self.position[0] + (target_x - self.position[0]) * lerp_factor
        new_y = self.position[1] + (target_y - self.position[1]) * lerp_factor
        
        # Apply boundaries if set
        if self.bounds:
            min_x, min_y, max_x, max_y = self.bounds
            new_x = max(min_x, min(new_x, max_x - self.screen_width))
            new_y = max(min_y, min(new_y, max_y - self.screen_height))
        else:
            # Apply minimum boundary of 0,0 by default
            new_x = max(0, new_x)
            new_y = max(0, new_y)
        
        # Update camera position
        self.position = (new_x, new_y)
    
    def to_screen_coordinates(self, world_position: Tuple[float, float]) -> Tuple[float, float]:
        """
        Convert world coordinates to screen coordinates.
        
        Args:
            world_position: (x, y) position in world space
            
        Returns:
            (x, y) position in screen space
        """
        return (
            world_position[0] - self.position[0],
            world_position[1] - self.position[1]
        )
    
    def to_world_coordinates(self, screen_position: Tuple[float, float]) -> Tuple[float, float]:
        """
        Convert screen coordinates to world coordinates.
        
        Args:
            screen_position: (x, y) position in screen space
            
        Returns:
            (x, y) position in world space
        """
        return (
            screen_position[0] + self.position[0],
            screen_position[1] + self.position[1]
        )
    
    def reset(self):
        """Reset camera to initial position."""
        self.position = (0, 0)
        self.target_position = (0, 0) 