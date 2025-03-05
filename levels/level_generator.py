import random
from utils.constants import WIDTH, HEIGHT
from entities.wall import Wall
from entities.target import Target
from entities.surface import Surface
from entities.powerup import PowerUp
from entities.gravity_well import GravityWell
from entities.teleporter import Teleporter
from entities.bounce_pad import BouncePad

def generate_level(level_num):
    """Generate a complete level with all entities."""
    if level_num == 1:
        return generate_tutorial_level()
    elif level_num == 2:
        return generate_level_2()
    elif level_num == 3:
        return generate_level_3()
    elif level_num == 4:
        return generate_advanced_level_4()
    elif level_num == 5:
        return generate_teleporter_level_5()
    elif level_num <= 10:
        return generate_simple_level(level_num)
    else:
        return generate_procedural_level(level_num)

def generate_tutorial_level():
    """Generate the tutorial level."""
    walls = [
        Wall(400, 100, 600, 20),  # Top
        Wall(400, 500, 600, 20),  # Bottom
        Wall(100, 300, 20, 420),  # Left
        Wall(700, 300, 20, 420),  # Right
    ]
    
    targets = [
        Target(400, 300, 20, 100, True)
    ]
    
    surfaces = [
        Surface(250, 350, 100, 100, "ice")
    ]
    
    powerups = [
        PowerUp(550, 350, "energy", 50)
    ]
    
    # Add clear directional arrows for tutorial guidance
    tutorial_elements = []
    tutorial_elements.append({
        "type": "arrow",
        "start": (150, 250),
        "end": (400, 300),
        "text": "Hit the target!",
        "color": (255, 255, 0)
    })
    
    return {
        "walls": walls,
        "targets": targets,
        "surfaces": surfaces,
        "powerups": powerups,
        "start_pos": (150, 300),
        "background_color": (20, 20, 30),
        "time_limit": 60,
        "energy_drain": 0,
        "tutorial": True,
        "tutorial_elements": tutorial_elements,
        "hint": "Use arrow keys to apply force to the ball"
    }

def generate_level_2():
    """Generate level 2 - Ice World."""
    walls = [
        Wall(400, 50, 700, 20),   # Top
        Wall(400, 550, 700, 20),  # Bottom
        Wall(50, 300, 20, 520),   # Left
        Wall(750, 300, 20, 520),  # Right
        # Inner walls
        Wall(300, 200, 200, 20),
        Wall(500, 400, 200, 20),
    ]
    
    targets = [
        Target(700, 100, 20, 100, True),
        Target(100, 500, 20, 50, False)
    ]
    
    surfaces = [
        Surface(400, 300, 600, 200, "ice")
    ]
    
    powerups = [
        PowerUp(200, 200, "energy", 50),
        PowerUp(600, 400, "time", 10)
    ]
    
    return {
        "walls": walls,
        "targets": targets,
        "surfaces": surfaces,
        "powerups": powerups,
        "start_pos": (100, 100),
        "background_color": (20, 30, 50),
        "time_limit": 45,
        "energy_drain": 0.1,
        "tutorial": False
    }

def generate_level_3():
    """Generate level 3 - Rough Terrain."""
    walls = [
        Wall(400, 50, 700, 20),   # Top
        Wall(400, 550, 700, 20),  # Bottom
        Wall(50, 300, 20, 520),   # Left
        Wall(750, 300, 20, 520),  # Right
        # Inner walls
        Wall(200, 200, 20, 200),
        Wall(400, 400, 20, 200),
        Wall(600, 200, 20, 200),
    ]
    
    targets = [
        Target(700, 500, 20, 100, True),
        Target(400, 100, 20, 50, True),
        Target(100, 300, 20, 50, False)
    ]
    
    surfaces = [
        Surface(300, 300, 200, 200, "rough"),
        Surface(500, 300, 200, 200, "ice"),
        Surface(300, 500, 100, 50, "bouncy")
    ]
    
    powerups = [
        PowerUp(200, 500, "energy", 50),
        PowerUp(600, 100, "speed", 1.5)
    ]
    
    return {
        "walls": walls,
        "targets": targets,
        "surfaces": surfaces,
        "powerups": powerups,
        "start_pos": (100, 100),
        "background_color": (30, 20, 30),
        "time_limit": 60,
        "energy_drain": 0.15,
        "tutorial": False
    }

def generate_advanced_level_4():
    """Generate level 4 - Gravity Wells."""
    walls = [
        Wall(400, 50, 700, 20),   # Top
        Wall(400, 550, 700, 20),  # Bottom
        Wall(50, 300, 20, 520),   # Left
        Wall(750, 300, 20, 520),  # Right
    ]
    
    targets = [
        Target(650, 450, 20, 100, True),
        Target(150, 150, 20, 50, True)
    ]
    
    surfaces = [
        Surface(400, 300, 200, 100, "ice")
    ]
    
    powerups = [
        PowerUp(200, 400, "energy", 50)
    ]
    
    gravity_wells = [
        GravityWell(400, 300, 150, 20.0, False),  # Attractor in center
        GravityWell(600, 150, 80, 15.0, True)    # Repeller in top-right
    ]
    
    bounce_pads = [
        BouncePad(150, 450, 80, 30, (1, -1), 2.0)  # Diagonal bounce pad in bottom-left
    ]
    
    return {
        "walls": walls,
        "targets": targets,
        "surfaces": surfaces,
        "powerups": powerups,
        "gravity_wells": gravity_wells,
        "bounce_pads": bounce_pads,
        "teleporters": [],
        "start_pos": (100, 500),
        "background_color": (15, 15, 35),
        "time_limit": 60,
        "energy_drain": 0.1,
        "tutorial": False
    }

def generate_teleporter_level_5():
    """Generate level 5 - Teleporter Maze."""
    walls = [
        Wall(400, 50, 700, 20),   # Top
        Wall(400, 550, 700, 20),  # Bottom
        Wall(50, 300, 20, 520),   # Left
        Wall(750, 300, 20, 520),  # Right
        # Maze walls
        Wall(200, 200, 20, 300),
        Wall(400, 400, 300, 20),
        Wall(600, 200, 20, 300),
    ]
    
    targets = [
        Target(700, 500, 20, 100, True),
        Target(400, 100, 15, 50, False)
    ]
    
    surfaces = [
        Surface(300, 150, 150, 80, "ice"),
        Surface(500, 500, 150, 80, "rough")
    ]
    
    powerups = [
        PowerUp(300, 500, "energy", 50),
        PowerUp(500, 150, "time", 15)
    ]
    
    # Create teleporter pairs
    teleporter1_a = Teleporter(150, 150, 1)
    teleporter1_b = Teleporter(650, 450, 1)
    teleporter1_a.target_teleporter = teleporter1_b
    teleporter1_b.target_teleporter = teleporter1_a
    
    teleporter2_a = Teleporter(150, 450, 2)
    teleporter2_b = Teleporter(650, 150, 2)
    teleporter2_a.target_teleporter = teleporter2_b
    teleporter2_b.target_teleporter = teleporter2_a
    
    teleporters = [teleporter1_a, teleporter1_b, teleporter2_a, teleporter2_b]
    
    bounce_pads = [
        BouncePad(400, 300, 80, 30, (0, -1), 2.0)  # Upward bounce pad in center
    ]
    
    gravity_wells = [
        GravityWell(400, 200, 100, 10.0, False)  # Attractor above center
    ]
    
    return {
        "walls": walls,
        "targets": targets,
        "surfaces": surfaces,
        "powerups": powerups,
        "teleporters": teleporters,
        "bounce_pads": bounce_pads,
        "gravity_wells": gravity_wells,
        "start_pos": (100, 300),
        "background_color": (20, 10, 40),
        "time_limit": 75,
        "energy_drain": 0.05,
        "tutorial": False
    }

def generate_simple_level(level_num):
    """Generate a simple level based on the level number."""
    # Increase difficulty with level number
    num_walls = 4 + level_num
    num_targets = 1 + level_num // 2
    num_surfaces = level_num // 2
    num_powerups = 1 + level_num // 3
    
    # Create outer walls
    walls = [
        Wall(WIDTH/2, 20, WIDTH - 40, 20),         # Top
        Wall(WIDTH/2, HEIGHT - 20, WIDTH - 40, 20), # Bottom
        Wall(20, HEIGHT/2, 20, HEIGHT - 40),       # Left
        Wall(WIDTH - 20, HEIGHT/2, 20, HEIGHT - 40) # Right
    ]
    
    # Add some inner walls
    for _ in range(num_walls - 4):
        x = random.randint(100, WIDTH - 100)
        y = random.randint(100, HEIGHT - 100)
        width = random.randint(50, 200)
        height = random.randint(20, 40) if random.random() < 0.7 else random.randint(20, 200)
        walls.append(Wall(x, y, width, height))
    
    # Add targets
    targets = []
    for i in range(num_targets):
        while True:
            x = random.randint(50, WIDTH - 50)
            y = random.randint(50, HEIGHT - 50)
            radius = random.randint(15, 25)
            
            # Check if the target is not too close to walls
            valid_position = True
            for wall in walls:
                if (abs(x - wall.x) < wall.width/2 + radius + 10 and 
                    abs(y - wall.y) < wall.height/2 + radius + 10):
                    valid_position = False
                    break
            
            if valid_position:
                required = i < num_targets // 2 + 1
                targets.append(Target(x, y, radius, 100 if required else 50, required))
                break
    
    # Add surfaces
    surfaces = []
    surface_types = ["ice", "rough", "bouncy", "sticky"]
    for _ in range(num_surfaces):
        x = random.randint(100, WIDTH - 100)
        y = random.randint(100, HEIGHT - 100)
        width = random.randint(100, 200)
        height = random.randint(100, 200)
        surface_type = random.choice(surface_types)
        surfaces.append(Surface(x, y, width, height, surface_type))
    
    # Add powerups
    powerups = []
    powerup_types = ["energy", "speed", "time"]
    for _ in range(num_powerups):
        x = random.randint(50, WIDTH - 50)
        y = random.randint(50, HEIGHT - 50)
        powerup_type = random.choice(powerup_types)
        value = 50 if powerup_type == "energy" else 1.5 if powerup_type == "speed" else 10
        powerups.append(PowerUp(x, y, powerup_type, value))
    
    # Add special gameplay elements for higher levels
    gravity_wells = []
    bounce_pads = []
    teleporters = []
    
    # Add gravity wells for levels 6+
    if level_num >= 6:
        num_wells = (level_num - 5) // 2
        for i in range(min(num_wells, 3)):  # Cap at 3 gravity wells
            x = random.randint(100, WIDTH - 100)
            y = random.randint(100, HEIGHT - 100)
            radius = random.randint(80, 150)
            strength = random.uniform(5.0, 25.0)
            repel = random.random() > 0.7  # 30% chance to be a repeller
            gravity_wells.append(GravityWell(x, y, radius, strength, repel))
    
    # Add bounce pads for levels 7+
    if level_num >= 7:
        num_pads = (level_num - 6) // 2
        for i in range(min(num_pads, 4)):  # Cap at 4 bounce pads
            x = random.randint(100, WIDTH - 100)
            y = random.randint(100, HEIGHT - 100)
            width = random.randint(60, 100)
            height = random.randint(20, 40)
            direction = (random.uniform(-1, 1), random.uniform(-1, 1))
            strength = random.uniform(1.5, 2.5)
            bounce_pads.append(BouncePad(x, y, width, height, direction, strength))
    
    # Add teleporters for levels 9+
    if level_num >= 9:
        num_pairs = (level_num - 8) // 2
        for i in range(min(num_pairs, 2)):  # Cap at 2 teleporter pairs
            # Create a pair of teleporters
            x1 = random.randint(80, WIDTH - 80)
            y1 = random.randint(80, HEIGHT - 80)
            x2 = random.randint(80, WIDTH - 80)
            y2 = random.randint(80, HEIGHT - 80)
            
            # Ensure they're not too close to each other
            while (abs(x1 - x2) < 200 and abs(y1 - y2) < 200):
                x2 = random.randint(80, WIDTH - 80)
                y2 = random.randint(80, HEIGHT - 80)
            
            teleporter1 = Teleporter(x1, y1, i+1)
            teleporter2 = Teleporter(x2, y2, i+1)
            teleporter1.target_teleporter = teleporter2
            teleporter2.target_teleporter = teleporter1
            
            teleporters.extend([teleporter1, teleporter2])
    
    # Set start position away from walls
    start_x, start_y = 100, 100
    
    # Increase time limit and energy drain with level
    time_limit = 30 + level_num * 5
    energy_drain = 0.05 + level_num * 0.02
    
    return {
        "walls": walls,
        "targets": targets,
        "surfaces": surfaces,
        "powerups": powerups,
        "gravity_wells": gravity_wells,
        "bounce_pads": bounce_pads,
        "teleporters": teleporters,
        "start_pos": (start_x, start_y),
        "background_color": (20 + level_num * 2, 20, 30 + level_num * 2),
        "time_limit": time_limit,
        "energy_drain": energy_drain,
        "tutorial": False
    }

def generate_procedural_level(level_num):
    """Generate a more complex procedural level."""
    # This is similar to generate_simple_level but with more complexity
    # For MVP, we'll just use the simple level generator with increased difficulty
    return generate_simple_level(level_num) 