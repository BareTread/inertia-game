import math

def distance(x1, y1, x2, y2):
    """Calculate the Euclidean distance between two points."""
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def normalize_vector(x, y):
    """Normalize a vector to unit length."""
    length = distance(0, 0, x, y)
    if length == 0:
        return 0, 0
    return x / length, y / length

def clamp(value, min_value, max_value):
    """Clamp a value between min and max values."""
    return max(min_value, min(value, max_value))

def lerp(a, b, t):
    """Linear interpolation between a and b by t (0.0 to 1.0)."""
    return a + (b - a) * t

def map_range(value, from_min, from_max, to_min, to_max):
    """Maps a value from one range to another."""
    return (value - from_min) * (to_max - to_min) / (from_max - from_min) + to_min

def circle_rect_collision(circle_x, circle_y, circle_radius, rect_x, rect_y, rect_width, rect_height):
    """
    Check collision between a circle and a rectangle.
    Returns (collision, normal_x, normal_y) where normal is the collision normal vector.
    """
    # Find the closest point on the rectangle to the circle
    closest_x = clamp(circle_x, rect_x - rect_width/2, rect_x + rect_width/2)
    closest_y = clamp(circle_y, rect_y - rect_height/2, rect_y + rect_height/2)
    
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

def circle_circle_collision(x1, y1, r1, x2, y2, r2):
    """
    Check collision between two circles.
    Returns (collision, normal_x, normal_y) where normal is the collision normal vector.
    """
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