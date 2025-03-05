import pygame
import random
import math
from utils.constants import WIDTH, HEIGHT

class Particle:
    """A simple particle for visual effects."""
    
    def __init__(self, x, y, vel_x, vel_y, color, size, lifetime, gravity=0, fade_mode="linear", glow=False, rotation=0, rotation_speed=0):
        self.x = x
        self.y = y
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.color = color
        self.size = size
        self.original_size = size
        self.lifetime = lifetime
        self.age = 0
        self.gravity = gravity
        self.dead = False
        self.fade_mode = fade_mode  # "linear", "smooth", "late", "early"
        self.glow = glow  # Whether to render with a glow effect
        self.rotation = rotation  # For non-circular particles
        self.rotation_speed = rotation_speed
    
    def update(self, dt):
        """Update particle position and properties."""
        # Update position
        self.x += self.vel_x * dt
        self.y += self.vel_y * dt
        
        # Apply gravity
        self.vel_y += self.gravity * dt
        
        # Apply drag/friction to slow particles over time
        self.vel_x *= 0.99
        self.vel_y *= 0.99
        
        # Update rotation
        self.rotation += self.rotation_speed * dt
        
        # Update age
        self.age += dt
        
        # Check if particle is dead
        if self.age >= self.lifetime:
            self.dead = True
            return
        
        # Shrink particle as it ages based on fade mode
        life_ratio = 1 - (self.age / self.lifetime)
        
        if self.fade_mode == "linear":
            self.size = self.original_size * life_ratio
        elif self.fade_mode == "smooth":
            # Smoother fade using sine curve
            self.size = self.original_size * (math.sin(life_ratio * math.pi / 2))
        elif self.fade_mode == "late":
            # Stay large until the end
            self.size = self.original_size * (life_ratio ** 0.3)
        elif self.fade_mode == "early":
            # Shrink quickly at first
            self.size = self.original_size * (life_ratio ** 3)
    
    def draw(self, surface):
        """Draw the particle on the given surface."""
        # Calculate alpha based on remaining lifetime and fade mode
        life_ratio = 1 - (self.age / self.lifetime)
        
        if self.fade_mode == "linear":
            alpha = int(255 * life_ratio)
        elif self.fade_mode == "smooth":
            alpha = int(255 * (math.sin(life_ratio * math.pi / 2)))
        elif self.fade_mode == "late":
            alpha = int(255 * (life_ratio ** 0.3))
        elif self.fade_mode == "early":
            alpha = int(255 * (life_ratio ** 3))
        else:
            alpha = int(255 * life_ratio)
        
        # Create a surface with per-pixel alpha
        size_int = max(1, int(self.size * 2))
        particle_surf = pygame.Surface((size_int, size_int), pygame.SRCALPHA)
        
        # Draw the particle
        if self.glow:
            # Draw with a glow effect (multiple circles with decreasing alpha)
            for r in range(int(self.size), 0, -1):
                glow_alpha = int(alpha * (r / self.size))
                pygame.draw.circle(
                    particle_surf,
                    (*self.color[:3], glow_alpha),
                    (int(self.size), int(self.size)),
                    r
                )
        else:
            # Standard circle
            pygame.draw.circle(
                particle_surf,
                (*self.color[:3], alpha),
                (int(self.size), int(self.size)),
                int(self.size)
            )
        
        # Blit the particle surface onto the main surface
        surface.blit(
            particle_surf,
            (int(self.x - self.size), int(self.y - self.size))
        )

class ParticleSystem:
    """Manages multiple particles."""
    
    def __init__(self, max_particles=1000):
        self.particles = []
        self.max_particles = max_particles
    
    def update(self, dt):
        """Update all particles in the system."""
        # Update existing particles
        for particle in self.particles[:]:
            particle.update(dt)
            if particle.dead:
                self.particles.remove(particle)
    
    def draw(self, surface):
        """Draw all particles in the system."""
        for particle in self.particles:
            particle.draw(surface)
    
    def add_particle(self, x, y, vel_x, vel_y, color, size, lifetime, gravity=0, fade_mode="linear", glow=False, rotation=0, rotation_speed=0):
        """Add a new particle to the system."""
        # Check if we've reached the maximum number of particles
        if len(self.particles) >= self.max_particles:
            # Remove the oldest particle
            self.particles.pop(0)
        
        # Add the new particle
        self.particles.append(Particle(x, y, vel_x, vel_y, color, size, lifetime, gravity, fade_mode, glow, rotation, rotation_speed))
    
    def add_explosion(self, x, y, color, count=20, speed=100, size_range=(2, 5), lifetime_range=(0.5, 1.5), glow=False):
        """Add an explosion of particles at the given position."""
        # Add a central glow flash
        if glow:
            flash_size = max(size_range) * 3
            self.add_particle(
                x, y, 0, 0, color, flash_size, 
                lifetime_range[0] * 0.5, 0, "early", True
            )
        
        for _ in range(count):
            # Random angle
            angle = random.uniform(0, math.pi * 2)
            # Random speed
            speed_val = random.uniform(speed * 0.5, speed * 1.5)
            # Calculate velocity components
            vel_x = math.cos(angle) * speed_val
            vel_y = math.sin(angle) * speed_val
            # Random size
            size = random.uniform(size_range[0], size_range[1])
            # Random lifetime
            lifetime = random.uniform(lifetime_range[0], lifetime_range[1])
            # Random fade mode
            fade_mode = random.choice(["linear", "smooth", "late"])
            
            # Add the particle
            self.add_particle(
                x, y, vel_x, vel_y, color, size, lifetime, 
                gravity=random.uniform(0, 50), 
                fade_mode=fade_mode,
                glow=glow and random.random() < 0.3
            )
    
    def add_trail(self, x, y, color, direction=(0, 1), count=5, speed=50, size_range=(1, 3), lifetime_range=(0.2, 0.8), glow=False):
        """Add a trail of particles at the given position."""
        dir_x, dir_y = direction
        
        for _ in range(count):
            # Random angle variation
            angle_var = random.uniform(-math.pi/4, math.pi/4)
            base_angle = math.atan2(dir_y, dir_x)
            angle = base_angle + angle_var
            
            # Random speed
            speed_val = random.uniform(speed * 0.5, speed)
            
            # Calculate velocity components
            vel_x = math.cos(angle) * speed_val
            vel_y = math.sin(angle) * speed_val
            
            # Random position variation
            pos_var = 5
            pos_x = x + random.uniform(-pos_var, pos_var)
            pos_y = y + random.uniform(-pos_var, pos_var)
            
            # Random size
            size = random.uniform(size_range[0], size_range[1])
            
            # Random lifetime
            lifetime = random.uniform(lifetime_range[0], lifetime_range[1])
            
            # Add the particle
            self.add_particle(
                pos_x, pos_y, vel_x, vel_y, color, size, lifetime,
                gravity=random.uniform(0, 20),
                glow=glow and random.random() < 0.5
            )
    
    def add_energy_burst(self, x, y, color=(255, 255, 100), count=30, speed=150):
        """Add an energy burst effect (for powerups, etc.)"""
        # Add a central glow
        self.add_particle(
            x, y, 0, 0, color, 20, 0.5, 0, "smooth", True
        )
        
        # Add radiating particles
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed_val = random.uniform(speed * 0.7, speed * 1.3)
            vel_x = math.cos(angle) * speed_val
            vel_y = math.sin(angle) * speed_val
            
            self.add_particle(
                x, y, vel_x, vel_y, color, 
                random.uniform(2, 6), 
                random.uniform(0.5, 1.0),
                0, "late", True
            )
    
    def add_screen_shake_particles(self, intensity=10):
        """Add particles around the screen edges for screen shake effect."""
        count = int(intensity * 5)
        
        for _ in range(count):
            # Determine which edge to spawn from
            edge = random.randint(0, 3)  # 0=top, 1=right, 2=bottom, 3=left
            
            if edge == 0:  # Top
                x = random.randint(0, WIDTH)
                y = 0
                vel_y = random.uniform(50, 150)
                vel_x = random.uniform(-20, 20)
            elif edge == 1:  # Right
                x = WIDTH
                y = random.randint(0, HEIGHT)
                vel_x = random.uniform(-150, -50)
                vel_y = random.uniform(-20, 20)
            elif edge == 2:  # Bottom
                x = random.randint(0, WIDTH)
                y = HEIGHT
                vel_y = random.uniform(-150, -50)
                vel_x = random.uniform(-20, 20)
            else:  # Left
                x = 0
                y = random.randint(0, HEIGHT)
                vel_x = random.uniform(50, 150)
                vel_y = random.uniform(-20, 20)
            
            # Random color
            color = (
                random.randint(200, 255),
                random.randint(200, 255),
                random.randint(200, 255)
            )
            
            self.add_particle(
                x, y, vel_x, vel_y, color,
                random.uniform(1, 3),
                random.uniform(0.3, 0.8),
                0, "smooth"
            )
    
    def clear(self):
        """Clear all particles from the system."""
        self.particles = [] 