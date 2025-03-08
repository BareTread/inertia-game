import pygame
import random
import math
from utils.constants import WIDTH, HEIGHT

class EnhancedParticleSystem:
    def __init__(self):
        self.particles = []
        self.screen_shake = 0
        
    def add_particle(self, x, y, vel_x, vel_y, color, size, lifetime, gravity=0, fade=True, glow=False):
        """Add a single particle with enhanced properties"""
        self.particles.append({
            "x": x, "y": y, 
            "vel_x": vel_x, "vel_y": vel_y,
            "color": color, "base_color": color,
            "size": size, "original_size": size,
            "lifetime": lifetime, "age": 0,
            "gravity": gravity, "fade": fade, "glow": glow
        })
    
    def add_explosion(self, x, y, color, count=20, speed_range=(1, 5), size_range=(2, 5), 
                      lifetime_range=(0.3, 1.0), gravity=0, glow=False):
        """Create an explosion of particles"""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(speed_range[0], speed_range[1])
            vel_x = math.cos(angle) * speed
            vel_y = math.sin(angle) * speed
            size = random.uniform(size_range[0], size_range[1])
            lifetime = random.uniform(lifetime_range[0], lifetime_range[1])
            
            # Slightly vary the color
            r, g, b = color
            r = min(255, max(0, r + random.randint(-20, 20)))
            g = min(255, max(0, g + random.randint(-20, 20)))
            b = min(255, max(0, b + random.randint(-20, 20)))
            
            self.add_particle(x, y, vel_x, vel_y, (r, g, b), size, lifetime, gravity, True, glow)
    
    def add_trail(self, x, y, vel_x, vel_y, color, count=5, speed_factor=0.3, lifetime=0.5, glow=True):
        """Add trail particles behind a moving object"""
        for _ in range(count):
            # Randomize the starting position slightly
            offset_x = random.uniform(-5, 5)
            offset_y = random.uniform(-5, 5)
            
            # Reverse velocity direction with some randomness for trail effect
            trail_vel_x = -vel_x * speed_factor * random.uniform(0.5, 1.5)
            trail_vel_y = -vel_y * speed_factor * random.uniform(0.5, 1.5)
            
            # Randomize size and lifetime
            size = random.uniform(2, 5)
            
            # Create the particle
            self.add_particle(
                x + offset_x, y + offset_y,
                trail_vel_x, trail_vel_y,
                color, size, lifetime, 0, True, glow
            )
    
    def update(self, dt):
        """Update all particles"""
        particles_to_keep = []
        
        for p in self.particles:
            # Update age
            p["age"] += dt
            
            # Remove if lifetime expired
            if p["age"] >= p["lifetime"]:
                continue
                
            # Apply gravity
            p["vel_y"] += p["gravity"] * dt
            
            # Update position
            p["x"] += p["vel_x"] * dt * 60  # Scale by 60 to normalize for frame rate
            p["y"] += p["vel_y"] * dt * 60
            
            # Update size if fading
            if p["fade"]:
                life_fraction = 1 - (p["age"] / p["lifetime"])
                p["size"] = p["original_size"] * life_fraction
                
                # Fade color too
                r, g, b = p["base_color"]
                alpha = int(255 * life_fraction)
                p["color"] = (r, g, b, alpha)
            
            particles_to_keep.append(p)
            
        self.particles = particles_to_keep
        
        # Update screen shake
        if self.screen_shake > 0:
            self.screen_shake -= dt * 15  # Decay rate
            if self.screen_shake < 0:
                self.screen_shake = 0
    
    def draw(self, surface, camera_offset=(0, 0)):
        """Draw all particles"""
        # Draw particles with glow effect
        for p in self.particles:
            # Calculate adjusted position with camera offset
            adjusted_x = p["x"] - camera_offset[0]
            adjusted_y = p["y"] - camera_offset[1]
            
            # Skip drawing if outside the visible area
            if 0 <= adjusted_x < WIDTH and 0 <= adjusted_y < HEIGHT:
                if p["glow"]:
                    # Create glow surface
                    glow_size = int(p["size"] * 3)
                    glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                    
                    # Calculate alpha based on remaining lifetime
                    alpha = int(255 * (1 - p["age"] / p["lifetime"]))
                    
                    # Get color with alpha
                    r, g, b = p["base_color"]
                    glow_color = (r, g, b, alpha // 3)  # More transparent for glow
                    
                    # Draw glow
                    pygame.draw.circle(glow_surf, glow_color, (glow_size, glow_size), glow_size)
                    
                    # Draw to surface with adjusted position
                    surface.blit(glow_surf, (int(adjusted_x) - glow_size, int(adjusted_y) - glow_size), 
                                special_flags=pygame.BLEND_ALPHA_SDL2)
                
                # Draw main particle with adjusted position
                pygame.draw.circle(
                    surface, 
                    p["color"] if len(p["color"]) == 4 else p["color"] + (255,), 
                    (int(adjusted_x), int(adjusted_y)), 
                    int(p["size"])
                )
    
    def add_screen_shake(self, amount):
        """Add screen shake effect"""
        self.screen_shake = max(self.screen_shake, amount)
        
    def get_screen_shake_offset(self):
        """Get current screen shake offset"""
        if self.screen_shake <= 0:
            return (0, 0)
            
        return (
            random.uniform(-self.screen_shake, self.screen_shake),
            random.uniform(-self.screen_shake, self.screen_shake)
        ) 