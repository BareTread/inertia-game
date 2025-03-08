from entities.wall import Wall
from entities.target import Target
from entities.surface import Surface
from entities.powerup import PowerUp
from entities.teleporter import Teleporter
from entities.gravity_well import GravityWell
from entities.bounce_pad import BouncePad
from utils.floating_text import FloatingText

class CollisionManager:
    def __init__(self):
        """Initialize the collision manager without game reference."""
        self.game = None  # Will be set later via set_game
    
    def set_game(self, game):
        """Set the game reference after initialization."""
        self.game = game
    
    def check_collisions(self, ball, entities, check_completion=True):
        """Check and handle collisions between the ball and entities."""
        if not ball:
            return {"collision_occurred": False}
            
        collision_occurred = False
        level_complete = False
        
        # First check if all targets are hit to determine level completion
        if check_completion:
            # Count required targets and hit targets
            required_targets = 0
            hit_required_targets = 0
            
            for entity in entities:
                if isinstance(entity, Target) and hasattr(entity, 'required') and entity.required:
                    required_targets += 1
                    if hasattr(entity, 'hit') and entity.hit:
                        hit_required_targets += 1
            
            # Only consider level complete if there are required targets and all are hit
            if required_targets > 0 and hit_required_targets == required_targets:
                print(f"Level complete! All {required_targets} targets hit.")
                return {"level_complete": True}
        
        # Process each entity for collisions
        for entity in entities:
            # Skip entities without collision checking
            if not hasattr(entity, 'check_collision'):
                continue
                
            # Check collision with this entity
            collision = entity.check_collision(ball)
            
            if collision:
                collision_occurred = True
                
                # Handle special entity types
                if isinstance(entity, PowerUp):
                    # Power-up collection
                    if hasattr(entity, 'collected') and not entity.collected:
                        entity.collected = True
                        # Add points or other effects
                        if hasattr(self.game, 'score'):
                            self.game.score += 100
                
                # Check if this collision completes the level
                if isinstance(entity, Target) and entity.required:
                    # Check if all required targets are now hit
                    all_targets_hit = True
                    for target in entities:
                        if (isinstance(target, Target) and hasattr(target, 'required') and target.required
                            and hasattr(target, 'hit') and not target.hit):
                            all_targets_hit = False
                            break
                    
                    if all_targets_hit and check_completion:
                        level_complete = True
        
        return {
            "collision_occurred": collision_occurred,
            "level_complete": level_complete
        }
    
    def check_circle_rect_collision(self, circle_x, circle_y, circle_radius, rect_x, rect_y, rect_width, rect_height):
        """
        Check collision between a circle and a rectangle.
        Returns (collision, normal_x, normal_y) where normal is the collision normal vector.
        """
        import math
        
        # Find the closest point on the rectangle to the circle
        closest_x = max(rect_x - rect_width/2, min(circle_x, rect_x + rect_width/2))
        closest_y = max(rect_y - rect_height/2, min(circle_y, rect_y + rect_height/2))
        
        # Calculate the distance between the circle's center and the closest point
        distance_x = circle_x - closest_x
        distance_y = circle_y - closest_y
        
        # If the distance is less than the circle's radius, there is a collision
        distance_squared = distance_x**2 + distance_y**2
        
        if distance_squared < circle_radius**2:
            # Calculate the collision normal
            if distance_squared == 0:  # Circle is exactly at the closest point
                # Default to a reasonable normal
                normal_x, normal_y = 0, -1
            else:
                # Normalize the distance vector to get the collision normal
                distance_total = math.sqrt(distance_squared)
                normal_x = distance_x / distance_total
                normal_y = distance_y / distance_total
                
            return True, normal_x, normal_y
        
        return False, 0, 0
    
    def check_circle_circle_collision(self, x1, y1, r1, x2, y2, r2):
        """
        Check collision between two circles.
        Returns (collision, normal_x, normal_y) where normal is the collision normal vector.
        """
        import math
        
        # Calculate distance between circle centers
        dx = x2 - x1
        dy = y2 - y1
        distance_squared = dx**2 + dy**2
        
        # Check if circles are colliding
        if distance_squared < (r1 + r2)**2:
            # Calculate collision normal
            if distance_squared == 0:  # Circles are at the same position
                # Default to a reasonable normal
                normal_x, normal_y = 0, -1
            else:
                # Normalize the distance vector to get the collision normal
                distance_total = math.sqrt(distance_squared)
                normal_x = dx / distance_total
                normal_y = dy / distance_total
                
            return True, normal_x, normal_y
        
        return False, 0, 0 