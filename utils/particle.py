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
        """Draw the particle."""
        # Calculate opacity based on age and fade mode
        if self.fade_mode == "linear":
            # Simple linear fade from 1.0 to 0.0
            alpha = 255 * (1 - (self.age / self.lifetime))
        elif self.fade_mode == "smooth":
            # Smoother fade that holds stronger in the middle
            progress = self.age / self.lifetime
            alpha = 255 * (1 - progress * progress)
        elif self.fade_mode == "late":
            # Maintain opacity and fade quickly at the end
            progress = self.age / self.lifetime
            alpha = 255 * (1 - (progress * progress * progress))
        elif self.fade_mode == "early":
            # Fade quickly at the start
            progress = self.age / self.lifetime
            alpha = 255 * (1 - math.sqrt(progress))
        else:
            alpha = 255
            
        alpha = max(0, min(255, int(alpha)))
        
        # Calculate current size (may shrink over time)
        current_size = self.original_size * (1 - 0.5 * (self.age / self.lifetime))
        
        # Enhanced glow effect for particles
        if self.glow:
            # Create a larger surface for the glow with per-pixel alpha
            glow_size = current_size * 2.1  # Reduced from 3.0 for more subtle effect
            glow_surf = pygame.Surface((int(glow_size * 2), int(glow_size * 2)), pygame.SRCALPHA)
            
            # Create a more dynamic glow using multiple circles with decreasing alpha
            for r in range(int(glow_size), 0, -2):
                # Calculate alpha based on radius and particle age - reduced by 30%
                glow_alpha = int(alpha * 0.5 * (r / glow_size))  # Reduced from 0.7
                
                # Create a slight color shift for outer glow
                glow_color = list(self.color)
                if len(glow_color) == 3:
                    glow_color.append(0)  # Add alpha channel if needed
                
                # Make outer glow slightly different color for a nicer effect
                if r > glow_size * 0.7:
                    glow_color[0] = min(255, int(glow_color[0] * 0.8))
                    glow_color[1] = min(255, int(glow_color[1] * 0.8))
                    glow_color[2] = min(255, int(glow_color[2] * 1.2))
                
                glow_color[3] = glow_alpha
                
                pygame.draw.circle(
                    glow_surf, 
                    tuple(glow_color), 
                    (int(glow_size), int(glow_size)), 
                    r
                )
            
            # Blit the glow surface
            surface.blit(
                glow_surf, 
                (int(self.x - glow_size), int(self.y - glow_size)), 
                special_flags=pygame.BLEND_ADD
            )
        
        # Draw the main particle
        # Create a surface with per-pixel alpha
        size_int = max(1, int(current_size * 2))
        particle_surf = pygame.Surface((size_int, size_int), pygame.SRCALPHA)
        
        # Draw the particle
        pygame.draw.circle(
            particle_surf,
            (*self.color[:3], alpha),
            (int(current_size), int(current_size)),
            int(current_size)
        )
        
        # Blit the particle surface onto the main surface
        surface.blit(
            particle_surf,
            (int(self.x - current_size), int(self.y - current_size))
        )

class ParticleSystem:
    """Manages multiple particles."""
    
    def __init__(self, max_particles=1000):
        self.particles = []
        self.max_particles = max_particles
        self.shake_amount = 0
        self.shake_duration = 0
    
    def update(self, dt):
        """Update all particles in the system."""
        # Cap maximum particles to ensure performance
        MAX_PARTICLES = 500
        if len(self.particles) > MAX_PARTICLES:
            # Remove oldest particles when we exceed the limit
            self.particles = self.particles[-MAX_PARTICLES:]
        
        # Update particles with batch processing
        particles_to_keep = []
        for particle in self.particles:
            particle.update(dt)
            if not particle.dead:
                particles_to_keep.append(particle)
        
        self.particles = particles_to_keep
        
        # Update screen shake effect
        if self.shake_duration > 0:
            self.shake_duration -= dt
            if self.shake_duration <= 0:
                self.shake_amount = 0
            else:
                # Gradually reduce shake intensity
                self.shake_amount *= 0.9
    
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
    
    def add_spiral_burst(self, x, y, color=(255, 150, 50), spiral_count=3, particles_per_spiral=12, 
                      radius=100, rotation_speed=10, lifetime=1.5):
        """Add a spiral burst of particles emanating from a point."""
        for spiral in range(spiral_count):
            # Each spiral starts at a different angle
            start_angle = (2 * math.pi / spiral_count) * spiral
            
            for i in range(particles_per_spiral):
                # Calculate delay based on position in spiral
                delay_factor = i / particles_per_spiral
                
                # Calculate spiral parameters
                angle = start_angle + (delay_factor * 2 * math.pi)
                distance = radius * delay_factor
                
                # Position along the spiral
                px = x + math.cos(angle) * distance
                py = y + math.sin(angle) * distance
                
                # Velocity - tangential to the spiral - reduced by ~30%
                tangent_angle = angle + math.pi/2
                speed = 35 + (105 * (1 - delay_factor))  # Reduced from 50 + 150
                vel_x = math.cos(tangent_angle) * speed
                vel_y = math.sin(tangent_angle) * speed
                
                # Make color unique for each spiral
                hue_shift = spiral * 0.3  # Shift hue for each spiral
                r = min(255, int(color[0] * (1 - hue_shift) + 50 * hue_shift))
                g = min(255, int(color[1] * (1 - hue_shift) + 100 * hue_shift))
                b = min(255, int(color[2] * (1 - hue_shift) + 200 * hue_shift))
                
                # Create the particle - smaller size for subtlety
                size = 2 + (1.5 * (1 - delay_factor))  # Reduced from 3 + 2
                self.add_particle(
                    px, py, vel_x, vel_y, 
                    (r, g, b), size, 
                    lifetime * (0.5 + (0.5 * delay_factor)),
                    0, "smooth", True, 
                    random.uniform(0, math.pi * 2),
                    rotation_speed * (1 - delay_factor) * 0.7  # Reduced rotation speed by 30%
                )
    
    def create_force_trail(self, position, direction, magnitude):
        """Creates particles showing the direction of force application.
        
        Args:
            position: (x, y) tuple of the starting position
            direction: Normalized [dx, dy] direction vector
            magnitude: Strength of the force
        """
        # Determine number of particles based on force magnitude
        num_particles = int(min(magnitude * 5, 20))  # Cap at 20 particles
        
        # Generate appropriate color based on force magnitude
        if magnitude < 1.0:
            color = (200, 200, 255)  # Light blue for low force
        elif magnitude < 2.0:
            color = (100, 100, 255)  # Medium blue for medium force
        elif magnitude < 3.0:
            color = (50, 50, 255)    # Deep blue for strong force
        else:
            color = (50, 50, 255)    # Deep blue with white trail for very strong force
            
        for _ in range(num_particles):
            # Create particles along the force direction
            offset_x = random.uniform(-2, 2) + (direction[0] * random.uniform(0, 10))
            offset_y = random.uniform(-2, 2) + (direction[1] * random.uniform(0, 10))
            
            # Randomize velocity slightly
            vel_x = direction[0] * random.uniform(20, 50) * (magnitude / 2)
            vel_y = direction[1] * random.uniform(20, 50) * (magnitude / 2)
            
            # Create particle with appropriate lifetime
            lifetime = random.uniform(0.2, 0.5)
            
            # Add some glow for stronger forces
            glow = magnitude > 2.0
            
            self.add_particle(
                position[0] + offset_x, 
                position[1] + offset_y,
                vel_x, vel_y,
                color,
                random.uniform(2, 4),
                lifetime,
                gravity=0,
                fade_mode="late",
                glow=glow
            )
            
    def screen_shake(self, amount):
        """Add screen shake effect.
        
        Args:
            amount: Intensity of the screen shake (0.0 to 1.0)
        """
        # Only add shake if it's stronger than current
        if amount > self.shake_amount:
            self.shake_amount = amount
            self.shake_duration = 0.3  # 300ms of shake
            
            # Add particles around the edges for stronger shakes
            if amount > 0.3:
                self.add_screen_shake_particles(int(amount * 10))
    
    def create_force_indicator(self, start_pos, direction, magnitude):
        """Create visual indicator when applying force."""
        from utils.helpers import map_range
        
        # Calculate end position
        end_x = start_pos[0] + direction[0] * magnitude * 5  # Scale for visibility
        end_y = start_pos[1] + direction[1] * magnitude * 5
        
        # Create particles along the line
        steps = max(5, int(magnitude * 2))
        for i in range(steps):
            # Position along the line
            t = i / (steps - 1)
            x = start_pos[0] + (end_x - start_pos[0]) * t
            y = start_pos[1] + (end_y - start_pos[1]) * t
            
            # Create particle
            size = map_range(i, 0, steps-1, 4, 1)  # Larger at the start
            lifetime = map_range(i, 0, steps-1, 0.5, 0.2)  # Longer at the start
            
            self.add_particle(
                x, y,
                direction[0] * -0.5, direction[1] * -0.5,
                (255, 255, 255),
                size,
                lifetime,
                fade_mode="smooth"
            )
    
    def create_impact(self, x, y, num_particles=10, color=(255, 255, 255), 
                     velocity=None, size_range=(1, 3), lifetime_range=(0.2, 0.8)):
        """Create impact particles from collision."""
        import random
        import math
        
        for _ in range(num_particles):
            # Random angle for particle direction
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(50, 150)
            
            # Calculate velocity
            vel_x = math.cos(angle) * speed
            vel_y = math.sin(angle) * speed
            
            # Apply base velocity if provided
            if velocity:
                vel_x += velocity[0] * random.uniform(0.5, 1.5)
                vel_y += velocity[1] * random.uniform(0.5, 1.5)
            
            # Random size and lifetime
            size = random.uniform(size_range[0], size_range[1])
            lifetime = random.uniform(lifetime_range[0], lifetime_range[1])
            
            # Randomize color slightly
            r = min(255, max(0, color[0] + random.randint(-20, 20)))
            g = min(255, max(0, color[1] + random.randint(-20, 20)))
            b = min(255, max(0, color[2] + random.randint(-20, 20)))
            
            # Create the particle
            self.add_particle(
                x, y,
                vel_x, vel_y,
                (r, g, b),
                size,
                lifetime,
                gravity=100,
                fade_mode="smooth"
            ) 
    
    def create_particles(self, x, y, count, color, min_speed=50, max_speed=150, min_lifetime=0.3, max_lifetime=1.0, direction=None, spread=2*math.pi):
        """Create a burst of particles at the given position.
        
        Args:
            x, y: Position to create particles
            count: Number of particles to create
            color: Color of particles
            min_speed, max_speed: Speed range for particles
            min_lifetime, max_lifetime: Lifetime range for particles
            direction: Optional direction vector (normalized). If None, particles go in all directions
            spread: Angle spread in radians (only used if direction is provided)
        """
        for _ in range(count):
            # Calculate random velocity
            if direction is None:
                # Random direction if no specific direction given
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(min_speed, max_speed)
                vel_x = math.cos(angle) * speed
                vel_y = math.sin(angle) * speed
            else:
                # Use provided direction with spread
                base_angle = math.atan2(direction[1], direction[0])
                angle = base_angle + random.uniform(-spread/2, spread/2)
                speed = random.uniform(min_speed, max_speed)
                vel_x = math.cos(angle) * speed
                vel_y = math.sin(angle) * speed
            
            # Random size and lifetime
            size = random.uniform(2, 5)
            lifetime = random.uniform(min_lifetime, max_lifetime)
            
            # Create particle
            self.add_particle(
                x, y, vel_x, vel_y, color, size, lifetime,
                gravity=0, fade_mode="smooth", glow=True
            ) 