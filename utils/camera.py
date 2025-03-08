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
        self.deadzone = 0  # Area around target where camera won't move
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
    
    def update(self, dt: float) -> None:
        """
        Update camera position based on target position.
        
        Args:
            dt: Delta time in seconds
        """
        # Calculate center position of the screen
        half_width = self.screen_width // 2
        half_height = self.screen_height // 2
        
        # Calculate desired camera position (centered on target)
        desired_x = self.target_position[0] - half_width
        desired_y = self.target_position[1] - half_height
        
        # Apply deadzone if set
        if self.deadzone > 0:
            current_x, current_y = self.position
            
            # Calculate distance from current to desired
            dx = desired_x - current_x
            dy = desired_y - current_y
            
            # Apply deadzone
            if abs(dx) < self.deadzone:
                desired_x = current_x
            if abs(dy) < self.deadzone:
                desired_y = current_y
        
        # Apply smooth movement using linear interpolation
        current_x, current_y = self.position
        new_x = current_x + (desired_x - current_x) * self.lerp_factor * dt
        new_y = current_y + (desired_y - current_y) * self.lerp_factor * dt
        
        # Apply boundaries if set
        if self.bounds:
            min_x, min_y, max_x, max_y = self.bounds
            new_x = max(min_x, min(new_x, max_x - self.screen_width))
            new_y = max(min_y, min(new_y, max_y - self.screen_height))
        
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