import pygame
import sys
import math
import random
import json
import os
import time
from enum import Enum

# Initialize pygame
pygame.init()
pygame.mixer.init()  # Initialize the mixer for sound

# Game Constants
WIDTH, HEIGHT = 800, 600
FPS = 60
FRICTION = 0.98
ENERGY_MAX = 100
ENERGY_REGEN = 0.2
FORCE_COST = 0.5
HIGHSCORE_FILE = "highscores.json"
MAX_LEVELS = 30  # Total number of levels in the game
REQUIRED_STARS_TO_UNLOCK = 2  # Stars needed to unlock next level

# Game State Enum
class GameState(Enum):
    MAIN_MENU = 0
    LEVEL_SELECT = 1
    PLAYING = 2
    PAUSED = 3
    LEVEL_COMPLETE = 4
    GAME_OVER = 5
    SETTINGS = 6
    CREDITS = 7
    TUTORIAL = 8

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (148, 0, 211)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
TRANSPARENT_BLACK = (0, 0, 0, 128)

# Surface types and their friction coefficients
SURFACES = {
    "normal": {"color": (200, 200, 200), "friction": FRICTION},
    "ice": {"color": (200, 230, 255), "friction": 0.995},
    "mud": {"color": (139, 69, 19), "friction": 0.9},
    "bouncy": {"color": (255, 105, 180), "friction": 1.01},  # Increases velocity
    "sticky": {"color": (255, 240, 150), "friction": 0.8},   # Very high friction
    "speed": {"color": (100, 255, 150), "friction": 0.995, "boost": 1.5}  # Speed boost
}

# Set up display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Inertia: Deluxe Edition")
icon = pygame.Surface((32, 32))
icon.fill(BLUE)
pygame.draw.circle(icon, WHITE, (16, 16), 10)
pygame.display.set_icon(icon)
clock = pygame.time.Clock()

# Load fonts
try:
    title_font = pygame.font.Font(None, 72)
    heading_font = pygame.font.Font(None, 48)
    medium_font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 24)
    tiny_font = pygame.font.Font(None, 18)
except:
    print("Error loading custom fonts, using system fonts instead")
    title_font = pygame.font.SysFont(None, 72)
    heading_font = pygame.font.SysFont(None, 48)
    medium_font = pygame.font.SysFont(None, 36)
    small_font = pygame.font.SysFont(None, 24)
    tiny_font = pygame.font.SysFont(None, 18)

# Sound and Music
SOUNDS = {
    "collision": None,
    "powerup": None,
    "teleport": None,
    "level_complete": None,
    "energy_low": None,
    "button_click": None,
    "error": None,
    "star": None,
    "bounce": None,
    "shield_break": None,
    "menu_navigate": None
}

MUSIC = {
    "menu": None,
    "gameplay": None,
    "level_complete": None
}

# Load sounds
def load_sounds():
    # Create sounds directory if it doesn't exist
    sounds_dir = os.path.join(os.path.dirname(__file__), "sounds")
    if not os.path.exists(sounds_dir):
        os.makedirs(sounds_dir)
        print(f"Created sounds directory at {sounds_dir}")
        print("Please add sound files to this directory.")
        return
        
    # Try to load available sound effects
    try:
        for sound_name in SOUNDS.keys():
            sound_path = os.path.join(sounds_dir, f"{sound_name}.wav")
            if os.path.exists(sound_path):
                SOUNDS[sound_name] = pygame.mixer.Sound(sound_path)
                print(f"Loaded sound: {sound_name}")
            else:
                print(f"Sound file not found: {sound_path}")
        
        # Load music
        music_dir = os.path.join(os.path.dirname(__file__), "music")
        if os.path.exists(music_dir):
            for music_name in MUSIC.keys():
                music_path = os.path.join(music_dir, f"{music_name}.mp3")
                if os.path.exists(music_path):
                    MUSIC[music_name] = music_path
                    print(f"Found music: {music_name}")
    except Exception as e:
        print(f"Error loading audio: {e}")

# Function to play a sound if it exists
def play_sound(sound_name, volume=1.0):
    if SOUNDS[sound_name]:
        SOUNDS[sound_name].set_volume(volume)
        SOUNDS[sound_name].play()

# Function to play music
def play_music(music_name, loop=True):
    if MUSIC[music_name]:
        try:
            pygame.mixer.music.load(MUSIC[music_name])
            # Use the volume from settings
            volume = game.settings["music_volume"] if 'game' in globals() else 0.5
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(-1 if loop else 0)
        except Exception as e:
            print(f"Error playing music {music_name}: {e}")

# Call load_sounds at startup
load_sounds()

# Utility Functions
def distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def normalize_vector(x, y):
    magnitude = math.sqrt(x * x + y * y)
    if magnitude == 0:
        return 0, 0
    return x / magnitude, y / magnitude

def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))

# UI Elements
class Button:
    def __init__(self, x, y, width, height, text, action=None, color=BLUE, hover_color=CYAN, text_color=WHITE, border_radius=10):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.border_radius = border_radius
        self.hovered = False
        self.alpha = 255
        self.pulsing = False
        self.pulse_value = 0
        self.disabled = False
        self.icon = None
        self.icon_rect = None
        
    def set_icon(self, icon):
        self.icon = icon
        if self.icon:
            self.icon_rect = self.icon.get_rect(midleft=(self.rect.left + 10, self.rect.centery))
    
    def update(self, mouse_pos, mouse_clicked):
        if self.disabled:
            return False
            
        self.hovered = self.rect.collidepoint(mouse_pos)
        
        if self.pulsing:
            self.pulse_value = (self.pulse_value + 0.05) % (2 * math.pi)
            pulse_factor = (math.sin(self.pulse_value) + 1) / 2
            self.alpha = int(200 + 55 * pulse_factor)
        
        clicked = False
        if self.hovered and mouse_clicked:
            if self.action:
                play_sound("button_click", 0.5)
                clicked = True
                
        return clicked
    
    def draw(self, surface):
        if self.disabled:
            color = tuple(max(0, c - 100) for c in self.color)
        else:
            color = self.hover_color if self.hovered else self.color
        
        # Create a transparent surface for the button
        button_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
        # Draw button with alpha
        button_color_with_alpha = color + (self.alpha,) if len(color) == 3 else color
        pygame.draw.rect(button_surface, button_color_with_alpha, 
                        (0, 0, self.rect.width, self.rect.height), 
                        border_radius=self.border_radius)
        
        # Draw button text
        font = small_font
        if len(self.text) < 10:
            font = medium_font
            
        text_surf = font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=button_surface.get_rect().center)
        
        # Adjust text position if icon exists
        if self.icon:
            text_rect.centerx += 15
            button_surface.blit(self.icon, (10, button_surface.get_height() // 2 - self.icon.get_height() // 2))
            
        button_surface.blit(text_surf, text_rect)
        
        # Draw the button
        surface.blit(button_surface, self.rect)
        
        # Draw border
        if self.hovered and not self.disabled:
            pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=self.border_radius)

class ProgressBar:
    def __init__(self, x, y, width, height, max_value, current_value=0, color=GREEN, background_color=(50, 50, 50), border_color=WHITE):
        self.rect = pygame.Rect(x, y, width, height)
        self.max_value = max_value
        self.current_value = current_value
        self.color = color
        self.background_color = background_color
        self.border_color = border_color
        self.target_value = current_value
        self.animation_speed = 0.1
        
    def update(self, dt):
        # Smoothly animate the current value towards the target value
        if self.current_value < self.target_value:
            self.current_value = min(self.current_value + (self.target_value - self.current_value) * self.animation_speed * dt * 60, self.target_value)
        elif self.current_value > self.target_value:
            self.current_value = max(self.current_value - (self.current_value - self.target_value) * self.animation_speed * dt * 60, self.target_value)
            
    def set_value(self, value):
        self.target_value = clamp(value, 0, self.max_value)
    
    def draw(self, surface):
        # Draw background
        pygame.draw.rect(surface, self.background_color, self.rect)
        
        # Draw fill
        fill_width = int((self.current_value / self.max_value) * self.rect.width)
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
        
        # Determine color based on percentage
        percentage = self.current_value / self.max_value
        if isinstance(self.color, tuple):
            display_color = self.color
        else:
            # Gradient from red to yellow to green
            if percentage < 0.5:
                r = 255
                g = int(255 * (percentage * 2))
                display_color = (r, g, 0)
            else:
                r = int(255 * (1 - (percentage - 0.5) * 2))
                g = 255
                display_color = (r, g, 0)
                
        pygame.draw.rect(surface, display_color, fill_rect)
        
        # Draw border
        pygame.draw.rect(surface, self.border_color, self.rect, 1)

class Toast:
    def __init__(self, text, duration=2.0, color=WHITE, background=None):
        self.text = text
        self.duration = duration
        self.color = color
        self.background = background or TRANSPARENT_BLACK
        self.alpha = 255
        self.start_time = time.time()
        self.font = small_font
        self.text_surface = self.font.render(self.text, True, self.color)
        self.rect = self.text_surface.get_rect(center=(WIDTH//2, HEIGHT - 50))
        self.active = True
        
    def update(self):
        elapsed = time.time() - self.start_time
        if elapsed > self.duration:
            self.active = False
            return
            
        # Fade in and out
        if elapsed < 0.3:
            self.alpha = int(255 * (elapsed / 0.3))
        elif elapsed > self.duration - 0.3:
            self.alpha = int(255 * ((self.duration - elapsed) / 0.3))
        else:
            self.alpha = 255
            
    def draw(self, surface):
        if not self.active:
            return
            
        # Create background surface with padding
        padding = 10
        bg_rect = pygame.Rect(self.rect.x - padding, self.rect.y - padding, 
                            self.rect.width + padding*2, self.rect.height + padding*2)
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_color = self.background[:3] + (min(self.background[3], self.alpha),) if len(self.background) == 4 else self.background + (self.alpha,)
        pygame.draw.rect(bg_surface, bg_color, (0, 0, bg_rect.width, bg_rect.height), border_radius=5)
        
        # Create text surface with alpha
        text_surface = self.font.render(self.text, True, self.color)
        text_surface.set_alpha(self.alpha)
        
        # Draw both surfaces
        surface.blit(bg_surface, bg_rect)
        surface.blit(text_surface, self.rect)

class Slider:
    def __init__(self, x, y, width, height, min_value, max_value, current_value, text="", color=BLUE, show_as_percent=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_value = min_value
        self.max_value = max_value
        self.current_value = current_value
        self.handle_radius = height * 1.2
        self.color = color
        self.text = text
        self.dragging = False
        self.show_as_percent = show_as_percent
        
    def get_handle_pos(self):
        value_range = self.max_value - self.min_value
        value_percent = (self.current_value - self.min_value) / value_range
        x_pos = self.rect.x + int(value_percent * self.rect.width)
        return (x_pos, self.rect.centery)
        
    def update(self, mouse_pos, mouse_pressed):
        mouse_x, mouse_y = mouse_pos
        handle_pos = self.get_handle_pos()
        
        # Check if mouse is over handle
        if distance(mouse_x, mouse_y, handle_pos[0], handle_pos[1]) <= self.handle_radius:
            if mouse_pressed[0]:
                self.dragging = True
                
        # If handle is being dragged, update position
        if self.dragging:
            if mouse_pressed[0]:
                # Calculate new value based on mouse position
                value_range = self.max_value - self.min_value
                x_percent = clamp((mouse_x - self.rect.x) / self.rect.width, 0, 1)
                self.current_value = self.min_value + x_percent * value_range
            else:
                self.dragging = False
                play_sound("button_click", 0.3)
                
    def draw(self, surface):
        # Draw slider track
        pygame.draw.rect(surface, (100, 100, 100), self.rect, border_radius=self.rect.height//2)
        
        # Draw filled portion
        fill_width = int(((self.current_value - self.min_value) / (self.max_value - self.min_value)) * self.rect.width)
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
        pygame.draw.rect(surface, self.color, fill_rect, border_radius=self.rect.height//2)
        
        # Draw handle
        handle_pos = self.get_handle_pos()
        pygame.draw.circle(surface, WHITE, handle_pos, self.handle_radius)
        pygame.draw.circle(surface, self.color, handle_pos, self.handle_radius - 2)
        
        # Draw value text
        if self.text:
            if self.show_as_percent:
                value_text = f"{self.text}: {int(self.current_value * 100)}%"
            else:
                value_text = f"{self.text}: {int(self.current_value)}"
            text_surf = small_font.render(value_text, True, WHITE)
            text_rect = text_surf.get_rect(midleft=(self.rect.right + 20, self.rect.centery))
            surface.blit(text_surf, text_rect)

# Ball
class Ball:
    def __init__(self, x, y, radius=15):
        self.x = x
        self.y = y
        self.radius = radius
        self.vel_x = 0
        self.vel_y = 0
        self.color = BLUE
        self.has_shield = False
        self.shield_pulse = 0
        self.trail_points = []
        self.trail_max_length = 20
        self.trail_color = (100, 100, 255, 150)
        self.pulse = 0
        
    def apply_force(self, force_x, force_y):
        self.vel_x += force_x
        self.vel_y += force_y
        
    def update(self, dt, friction=FRICTION):
        # Update pulse animation
        self.pulse = (self.pulse + 0.1 * dt * 60) % (2 * math.pi)
        
        # Update shield pulse if shield is active
        if self.has_shield:
            self.shield_pulse = (self.shield_pulse + 0.15 * dt * 60) % (2 * math.pi)
        
        # Update position based on velocity
        self.x += self.vel_x * dt * 60
        self.y += self.vel_y * dt * 60
        
        # Store position for trail effect (only if moving)
        if abs(self.vel_x) > 0.1 or abs(self.vel_y) > 0.1:
            # Only add points periodically to avoid too dense trail
            if len(self.trail_points) == 0 or distance(self.x, self.y, self.trail_points[-1][0], self.trail_points[-1][1]) > 5:
                speed = math.sqrt(self.vel_x**2 + self.vel_y**2)
                alpha = min(200, int(speed * 10))
                self.trail_points.append((self.x, self.y, alpha))
        
        # Limit trail length
        while len(self.trail_points) > self.trail_max_length:
            self.trail_points.pop(0)
            
        # Fade trail points
        for i in range(len(self.trail_points)):
            x, y, alpha = self.trail_points[i]
            fade_speed = 3 * dt * 60
            self.trail_points[i] = (x, y, max(0, alpha - fade_speed))
        
        # Apply friction
        self.vel_x *= friction ** (dt * 60)
        self.vel_y *= friction ** (dt * 60)
        
        # If velocity is very small, stop completely (prevents endless sliding)
        if abs(self.vel_x) < 0.05 and abs(self.vel_y) < 0.05:
            self.vel_x = 0
            self.vel_y = 0
            
    def draw(self, surface):
        # Draw trail
        for i, (pos_x, pos_y, alpha) in enumerate(self.trail_points):
            if alpha <= 0:
                continue
                
            radius = int(self.radius * (0.3 + 0.7 * i/len(self.trail_points)))
            color = self.trail_color[:3] + (int(alpha * i/len(self.trail_points)),)
            
            # Create a surface with per-pixel alpha
            trail_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, color, (radius, radius), radius)
            surface.blit(trail_surf, (int(pos_x-radius), int(pos_y-radius)))
        
        # Draw the ball with pulsing effect
        pulse_radius = self.radius * (1 + 0.1 * math.sin(self.pulse))
        
        # Draw a slight glow effect
        glow_surf = pygame.Surface((int(pulse_radius*3), int(pulse_radius*3)), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, self.color[:3] + (50,), (int(pulse_radius*1.5), int(pulse_radius*1.5)), int(pulse_radius*1.5))
        surface.blit(glow_surf, (int(self.x - pulse_radius*1.5), int(self.y - pulse_radius*1.5)))
        
        # Draw the main ball
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(pulse_radius))
        
        # Add a white highlight
        highlight_offset = pulse_radius * 0.3
        highlight_radius = pulse_radius * 0.3
        pygame.draw.circle(surface, (255, 255, 255, 150), 
                           (int(self.x - highlight_offset), int(self.y - highlight_offset)), 
                           int(highlight_radius))
        
        # Draw shield if active
        if self.has_shield:
            shield_radius = self.radius + 8 + 4 * math.sin(self.shield_pulse)
            shield_surf = pygame.Surface((int(shield_radius*2), int(shield_radius*2)), pygame.SRCALPHA)
            
            # Draw two-layered shield with animation
            shield_color1 = (220, 220, 220, 100)
            shield_color2 = (180, 180, 255, 150)
            pygame.draw.circle(shield_surf, shield_color1, (int(shield_radius), int(shield_radius)), int(shield_radius))
            pygame.draw.circle(shield_surf, shield_color2, (int(shield_radius), int(shield_radius)), int(shield_radius), 3)
            
            # Add some shield "energy" effects
            for i in range(8):
                angle = i * math.pi/4 + self.shield_pulse
                energy_x = shield_radius + math.cos(angle) * shield_radius * 0.8
                energy_y = shield_radius + math.sin(angle) * shield_radius * 0.8
                energy_size = 3 + 2 * math.sin(self.shield_pulse + i)
                pygame.draw.circle(shield_surf, WHITE, (int(energy_x), int(energy_y)), int(energy_size))
                
            surface.blit(shield_surf, (int(self.x-shield_radius), int(self.y-shield_radius)))
        
        # Draw direction indicator if moving
        if abs(self.vel_x) > 0.1 or abs(self.vel_y) > 0.1:
            speed = math.sqrt(self.vel_x**2 + self.vel_y**2)
            norm_x = self.vel_x / speed
            norm_y = self.vel_y / speed
            pygame.draw.line(surface, WHITE, 
                            (int(self.x), int(self.y)), 
                            (int(self.x + norm_x * pulse_radius), int(self.y + norm_y * pulse_radius)), 
                            3)

# Wall
class Wall:
    def __init__(self, x, y, width, height, movable=False, move_path=None, move_speed=1.0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)
        self.color = BLACK
        self.movable = movable
        self.move_path = move_path or []  # List of (x, y) points to move between
        self.move_speed = move_speed
        self.current_path_index = 0
        self.move_progress = 0
        self.bounce_time = 0
        self.bounce_intensity = 0
        
    def update(self, dt):
        self.bounce_intensity = max(0, self.bounce_intensity - dt * 60 * 0.1)
        
        if not self.movable or not self.move_path or len(self.move_path) < 2:
            return
            
        # Update movement along path
        current_point = self.move_path[self.current_path_index]
        next_index = (self.current_path_index + 1) % len(self.move_path)
        next_point = self.move_path[next_index]
        
        # Update progress along current path segment
        self.move_progress += self.move_speed * dt
        
        # If we've reached the next point, update indices
        if self.move_progress >= 1.0:
            self.current_path_index = next_index
            self.move_progress = 0
            current_point = self.move_path[self.current_path_index]
            next_index = (self.current_path_index + 1) % len(self.move_path)
            next_point = self.move_path[next_index]
            
        # Calculate new position
        self.x = current_point[0] + (next_point[0] - current_point[0]) * self.move_progress
        self.y = current_point[1] + (next_point[1] - current_point[1]) * self.move_progress
        
        # Update rect
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        
    def draw(self, surface):
        # Apply bounce effect if wall was recently hit
        draw_rect = self.rect.copy()
        if self.bounce_intensity > 0:
            # Make the wall appear to "bounce" by slightly changing its size
            bounce_offset = int(self.bounce_intensity * 3)
            draw_rect.inflate_ip(-bounce_offset, -bounce_offset)
            
            # Draw impact "flash"
            flash_alpha = int(self.bounce_intensity * 150)
            flash_surf = pygame.Surface((self.width + 10, self.height + 10), pygame.SRCALPHA)
            flash_surf.fill((255, 255, 255, flash_alpha))
            surface.blit(flash_surf, (self.rect.x - 5, self.rect.y - 5))
            
        # Draw the wall
        pygame.draw.rect(surface, self.color, draw_rect)
        
        # Draw subtle pattern for movable walls
        if self.movable:
            pattern_color = (50, 50, 50)
            for i in range(0, self.width, 10):
                for j in range(0, self.height, 10):
                    pygame.draw.rect(surface, pattern_color,
                                    (self.rect.x + i, self.rect.y + j, 5, 5))
        
    def check_collision(self, ball):
        # Find the closest point on the rect to the ball
        closest_x = max(self.rect.left, min(ball.x, self.rect.right))
        closest_y = max(self.rect.top, min(ball.y, self.rect.bottom))
        
        # Calculate distance from closest point to circle center
        distance_x = ball.x - closest_x
        distance_y = ball.y - closest_y
        distance_squared = distance_x**2 + distance_y**2
        
        # Check collision
        if distance_squared < ball.radius**2:
            # Handle collision
            overlap = ball.radius - math.sqrt(distance_squared)
            
            # Normalize direction
            if distance_squared > 0:
                norm_x = distance_x / math.sqrt(distance_squared)
                norm_y = distance_y / math.sqrt(distance_squared)
            else:
                # Ball is exactly at the closest point, push in arbitrary direction
                norm_x, norm_y = 1, 0
                
            # Move ball out of collision
            ball.x += norm_x * overlap
            ball.y += norm_y * overlap
            
            # Bounce (with some energy loss)
            dot_product = ball.vel_x * norm_x + ball.vel_y * norm_y
            ball.vel_x -= 1.8 * dot_product * norm_x  # 1.8 makes it bouncy
            ball.vel_y -= 1.8 * dot_product * norm_y
            
            # Add bounce effect
            self.bounce_intensity = 1.0
            self.bounce_time = time.time()
            
            # Determine collision side
            if abs(distance_x) > abs(distance_y):
                if distance_x > 0:
                    collision_side = "right"
                else:
                    collision_side = "left"
            else:
                if distance_y > 0:
                    collision_side = "bottom"
                else:
                    collision_side = "top"
                    
            return collision_side
        return False

# Surface
class Surface:
    def __init__(self, x, y, width, height, surface_type="normal"):
        self.rect = pygame.Rect(x, y, width, height)
        self.type = surface_type
        self.color = SURFACES[surface_type]["color"]
        self.friction = SURFACES[surface_type]["friction"]
        self.boost = SURFACES[surface_type].get("boost", 1.0)
        self.particles = []
        self.animation_timer = 0
        
    def update(self, dt):
        self.animation_timer += dt
        
        # Update particles
        for i in range(len(self.particles) - 1, -1, -1):
            x, y, vx, vy, size, life = self.particles[i]
            life -= dt
            if life <= 0:
                self.particles.pop(i)
                continue
                
            x += vx * dt * 60
            y += vy * dt * 60
            self.particles[i] = (x, y, vx, vy, size, life)
        
    def add_particle(self, x, y, ball_vel_x=0, ball_vel_y=0):
        if len(self.particles) > 20:
            return
            
        # Create particle based on surface type
        if self.type == "ice":
            color = (200, 240, 255)
            size = random.uniform(1, 3)
            life = random.uniform(0.1, 0.4)
            vx = random.uniform(-1, 1) - ball_vel_x * 0.2
            vy = random.uniform(-1, 1) - ball_vel_y * 0.2
            self.particles.append((x, y, vx, vy, size, life))
            
        elif self.type == "mud":
            color = (139, 69, 19)
            size = random.uniform(2, 4)
            life = random.uniform(0.2, 0.6)
            vx = random.uniform(-0.5, 0.5) - ball_vel_x * 0.1
            vy = random.uniform(-0.5, 0.5) - ball_vel_y * 0.1
            self.particles.append((x, y, vx, vy, size, life))
            
        elif self.type == "bouncy":
            color = (255, 105, 180)
            size = random.uniform(2, 5)
            life = random.uniform(0.2, 0.4)
            vx = random.uniform(-2, 2)
            vy = random.uniform(-2, 2)
            self.particles.append((x, y, vx, vy, size, life))
            
        elif self.type == "speed":
            color = (100, 255, 150)
            size = random.uniform(1, 3)
            life = random.uniform(0.1, 0.3)
            # Particles should flow in direction of movement
            vx = ball_vel_x * -0.5 + random.uniform(-1, 1)
            vy = ball_vel_y * -0.5 + random.uniform(-1, 1)
            self.particles.append((x, y, vx, vy, size, life))
        
    def draw(self, surface):
        # Draw the base surface
        pygame.draw.rect(surface, self.color, self.rect)
        
        # Add visual effects based on surface type
        if self.type == "ice":
            # Add shine/sparkle effect
            for i in range(10):
                x = self.rect.x + random.randint(0, self.rect.width)
                y = self.rect.y + random.randint(0, self.rect.height)
                size = random.randint(1, 3)
                alpha = int(100 + 100 * math.sin(self.animation_timer * 2 + i))
                pygame.draw.circle(surface, (255, 255, 255, alpha), (x, y), size)
                
        elif self.type == "bouncy":
            # Add pulsing pattern
            pattern_color = (255, 200, 230)
            pattern_spacing = 20
            pattern_size = 5 + int(3 * math.sin(self.animation_timer * 3))
            for x in range(self.rect.left + pattern_spacing, self.rect.right, pattern_spacing):
                for y in range(self.rect.top + pattern_spacing, self.rect.bottom, pattern_spacing):
                    pygame.draw.circle(surface, pattern_color, (x, y), pattern_size)
                    
        elif self.type == "speed":
            # Add speed lines
            for i in range(0, self.rect.width, 15):
                line_length = 10 + 5 * math.sin(self.animation_timer * 5 + i)
                pygame.draw.line(surface, (50, 200, 100), 
                                (self.rect.x + i, self.rect.y + 5),
                                (self.rect.x + i + line_length, self.rect.y + 5), 2)
                pygame.draw.line(surface, (50, 200, 100), 
                                (self.rect.x + i, self.rect.bottom - 5),
                                (self.rect.x + i + line_length, self.rect.bottom - 5), 2)
        
        # Draw particles
        for x, y, _, _, size, life in self.particles:
            alpha = int(255 * min(1, life * 5))
            color = self.color
            pygame.draw.circle(surface, color + (alpha,) if len(color) == 3 else color, 
                              (int(x), int(y)), int(size))
        
        # Draw border
        pygame.draw.rect(surface, (100, 100, 100), self.rect, 1)
        
    def is_ball_on_surface(self, ball):
        return (self.rect.left < ball.x < self.rect.right and 
                self.rect.top < ball.y < self.rect.bottom)
    
    def apply_effect(self, ball):
        # Apply special effects based on surface type
        if self.type == "speed":
            # Boost in the current direction of travel
            if ball.vel_x != 0 or ball.vel_y != 0:
                speed = math.sqrt(ball.vel_x**2 + ball.vel_y**2)
                if speed > 0:
                    normalized_x, normalized_y = ball.vel_x / speed, ball.vel_y / speed
                    ball.vel_x = normalized_x * speed * self.boost
                    ball.vel_y = normalized_y * speed * self.boost

# Target
class Target:
    def __init__(self, x, y, radius=20, points=100, required=True):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = GREEN
        self.active = True
        self.required = required  # If True, this target must be collected to complete level
        self.points = points
        self.pulse = 0
        self.collected_time = 0
        self.collection_particles = []
        
    def update(self, dt):
        self.pulse = (self.pulse + dt * 3) % (2 * math.pi)
        
        # Update collection particles
        for i in range(len(self.collection_particles) - 1, -1, -1):
            x, y, vx, vy, size, life = self.collection_particles[i]
            life -= dt
            if life <= 0:
                self.collection_particles.pop(i)
                continue
                
            x += vx * dt * 60
            y += vy * dt * 60
            size = max(0.5, size - dt * 2)
            self.collection_particles[i] = (x, y, vx, vy, size, life)
        
    def draw(self, surface):
        if not self.active:
            # Draw collection particle effects
            for x, y, _, _, size, life in self.collection_particles:
                alpha = int(255 * min(1, life * 4))
                pygame.draw.circle(surface, self.color + (alpha,) if len(self.color) == 3 else self.color, 
                                  (int(x), int(y)), int(size))
            return
            
        # Calculate pulse effect
        pulse_effect = 1 + 0.1 * math.sin(self.pulse)
        
        # Draw target base with subtle glow
        glow_radius = int(self.radius * 1.5)
        glow_surf = pygame.Surface((glow_radius*2, glow_radius*2), pygame.SRCALPHA)
        for r in range(glow_radius, 0, -3):
            alpha = max(0, int(150 * (1 - r/glow_radius)))
            pygame.draw.circle(glow_surf, self.color[:3] + (alpha,), (glow_radius, glow_radius), r)
        surface.blit(glow_surf, (int(self.x - glow_radius), int(self.y - glow_radius)))
        
        # Draw main target
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.radius * pulse_effect))
        
        # Draw target rings with animation
        ring_width = 2
        pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y)), int(self.radius * pulse_effect), ring_width)
        pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y)), int(self.radius * 2/3 * pulse_effect), ring_width)
        pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y)), int(self.radius * 1/3 * pulse_effect), ring_width)
        
        # Draw a white highlight
        highlight_offset = self.radius * 0.3
        highlight_radius = self.radius * 0.2
        pygame.draw.circle(surface, (255, 255, 255, 150), 
                           (int(self.x - highlight_offset), int(self.y - highlight_offset)), 
                           int(highlight_radius))
        
        # If this is an optional (star) target, draw a star icon
        if not self.required:
            star_size = self.radius * 0.6
            pygame.draw.polygon(surface, YELLOW, [
                (self.x, self.y - star_size),
                (self.x + star_size * 0.2, self.y - star_size * 0.3),
                (self.x + star_size, self.y - star_size * 0.3),
                (self.x + star_size * 0.4, self.y + star_size * 0.1),
                (self.x + star_size * 0.6, self.y + star_size),
                (self.x, self.y + star_size * 0.5),
                (self.x - star_size * 0.6, self.y + star_size),
                (self.x - star_size * 0.4, self.y + star_size * 0.1),
                (self.x - star_size, self.y - star_size * 0.3),
                (self.x - star_size * 0.2, self.y - star_size * 0.3),
            ])
    
    def check_collision(self, ball):
        if not self.active:
            return False
            
        distance_squared = (ball.x - self.x)**2 + (ball.y - self.y)**2
        if distance_squared < (ball.radius + self.radius)**2:
            self.active = False
            self.collected_time = time.time()
            
            # Create collection particles
            num_particles = 20
            for _ in range(num_particles):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(2, 5)
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                size = random.uniform(2, 4)
                life = random.uniform(0.5, 1.0)
                self.collection_particles.append((self.x, self.y, vx, vy, size, life))
                
            return True
        return False

# PowerUp
class PowerUp:
    def __init__(self, x, y, power_type):
        self.x = x
        self.y = y
        self.radius = 15
        self.type = power_type
        self.active = True
        self.colors = {
            "energy": (255, 215, 0),  # Gold
            "speed": (0, 191, 255),   # Deep sky blue
            "gravity": (148, 0, 211), # Dark violet
            "shield": (220, 220, 220), # Silver
            "time": (255, 105, 180),  # Pink
            "magnet": (255, 69, 0)    # Red-orange
        }
        self.color = self.colors.get(power_type, (255, 255, 255))
        self.effect_duration = {
            "energy": 0,       # One-time effect
            "speed": 5.0,      # 5 seconds
            "gravity": 8.0,    # 8 seconds
            "shield": 10.0,    # 10 seconds
            "time": 5.0,       # 5 seconds
            "magnet": 7.0      # 7 seconds
        }.get(power_type, 5.0)
        self.effect_start_time = 0
        self.collected = False
        self.pulse = 0
        self.float_offset = 0
        self.collection_particles = []
        
    def update(self, dt):
        self.pulse = (self.pulse + dt * 5) % (2 * math.pi)
        self.float_offset = 3 * math.sin(self.pulse * 0.5)
        
        # Update collection particles
        for i in range(len(self.collection_particles) - 1, -1, -1):
            x, y, vx, vy, size, life = self.collection_particles[i]
            life -= dt
            if life <= 0:
                self.collection_particles.pop(i)
                continue
                
            x += vx * dt * 60
            y += vy * dt * 60
            size = max(0.5, size - dt * 2)
            self.collection_particles[i] = (x, y, vx, vy, size, life)
        
    def draw(self, surface):
        if not self.active:
            # Draw collection particle effects
            for x, y, _, _, size, life in self.collection_particles:
                alpha = int(255 * min(1, life * 4))
                pygame.draw.circle(surface, self.color + (alpha,) if len(self.color) == 3 else self.color, 
                                  (int(x), int(y)), int(size))
            return
            
        # Draw glow effect
        glow_radius = self.radius * 2
        glow_surf = pygame.Surface((int(glow_radius*2), int(glow_radius*2)), pygame.SRCALPHA)
        for r in range(int(glow_radius), 0, -3):
            alpha = max(0, int(100 * (1 - r/glow_radius)))
            pygame.draw.circle(glow_surf, self.color[:3] + (alpha,), (int(glow_radius), int(glow_radius)), r)
        surface.blit(glow_surf, (int(self.x - glow_radius), int(self.y - glow_radius + self.float_offset)))
            
        # Draw the power-up
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y + self.float_offset)), self.radius)
        
        # Draw a pulsing effect (inner circle)
        pulse = math.sin(self.pulse) * 0.5 + 0.5
        inner_radius = int(self.radius * 0.7 * pulse)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y + self.float_offset)), inner_radius)
        
        # Draw icon based on type
        font = small_font
        
        if self.type == "energy":
            # Draw lightning bolt icon
            bolt_points = [
                (self.x - 5, self.y - 7 + self.float_offset),
                (self.x + 3, self.y - 2 + self.float_offset),
                (self.x - 2, self.y - 2 + self.float_offset),
                (self.x + 5, self.y + 7 + self.float_offset),
                (self.x - 3, self.y + 2 + self.float_offset),
                (self.x + 2, self.y + 2 + self.float_offset)
            ]
            pygame.draw.polygon(surface, BLACK, bolt_points)
        elif self.type == "speed":
            # Draw speed icon (> shape)
            pygame.draw.polygon(surface, BLACK, [
                (self.x - 5, self.y - 7 + self.float_offset),
                (self.x + 5, self.y + self.float_offset),
                (self.x - 5, self.y + 7 + self.float_offset)
            ])
        elif self.type == "gravity":
            # Draw gravity icon (circle with arrows)
            pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y + self.float_offset)), 5, 2)
            # Draw arrows
            arrow_length = 8
            pygame.draw.line(surface, BLACK, 
                           (int(self.x), int(self.y - 5 + self.float_offset)),
                           (int(self.x), int(self.y - arrow_length + self.float_offset)), 2)
            pygame.draw.line(surface, BLACK, 
                           (int(self.x - 3), int(self.y - arrow_length + 3 + self.float_offset)),
                           (int(self.x), int(self.y - arrow_length + self.float_offset)), 2)
            pygame.draw.line(surface, BLACK, 
                           (int(self.x + 3), int(self.y - arrow_length + 3 + self.float_offset)),
                           (int(self.x), int(self.y - arrow_length + self.float_offset)), 2)
        elif self.type == "shield":
            # Draw shield icon
            pygame.draw.arc(surface, BLACK, 
                           (int(self.x - 5), int(self.y - 5 + self.float_offset), 10, 10),
                           math.pi * 0.2, math.pi * 0.8, 2)
            pygame.draw.line(surface, BLACK, 
                           (int(self.x - 3), int(self.y + 0 + self.float_offset)),
                           (int(self.x + 3), int(self.y + 0 + self.float_offset)), 2)
        elif self.type == "time":
            # Draw clock icon
            pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y + self.float_offset)), 5, 1)
            # Draw clock hands
            hand_length = 4
            pygame.draw.line(surface, BLACK, 
                           (int(self.x), int(self.y + self.float_offset)),
                           (int(self.x), int(self.y - hand_length + self.float_offset)), 2)
            pygame.draw.line(surface, BLACK, 
                           (int(self.x), int(self.y + self.float_offset)),
                           (int(self.x + hand_length - 1), int(self.y + self.float_offset)), 1)
        elif self.type == "magnet":
            # Draw magnet icon
            pygame.draw.rect(surface, BLACK, 
                            (int(self.x - 5), int(self.y - 5 + self.float_offset), 10, 7), 2)
            pygame.draw.line(surface, BLACK, 
                           (int(self.x - 3), int(self.y + 2 + self.float_offset)),
                           (int(self.x - 3), int(self.y + 5 + self.float_offset)), 2)
            pygame.draw.line(surface, BLACK, 
                           (int(self.x + 3), int(self.y + 2 + self.float_offset)),
                           (int(self.x + 3), int(self.y + 5 + self.float_offset)), 2)
        else:
            text = font.render("?", True, BLACK)
            text_rect = text.get_rect(center=(int(self.x), int(self.y + self.float_offset)))
            surface.blit(text, text_rect)
    
    def check_collision(self, ball):
        if not self.active:
            return False
            
        distance_squared = (ball.x - self.x)**2 + (ball.y - self.y)**2
        if distance_squared < (ball.radius + self.radius)**2:
            self.active = False
            self.collected = True
            self.effect_start_time = time.time()
            
            # Create collection particles
            num_particles = 20
            for _ in range(num_particles):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(2, 5)
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                size = random.uniform(2, 4)
                life = random.uniform(0.5, 1.0)
                self.collection_particles.append((self.x, self.y, vx, vy, size, life))
                
            return True
        return False
    
    def apply_effect(self, game):
        """Apply the power-up effect to the game"""
        if not self.collected:
            return False
            
        current_time = time.time()
        effect_time_remaining = self.effect_duration - (current_time - self.effect_start_time)
        
        # If effect has expired, remove it
        if self.effect_duration > 0 and effect_time_remaining <= 0:
            self.collected = False
            return False
            
        # Apply the effect based on type
        if self.type == "energy":
            # Energy refill (one-time effect)
            game.energy = min(ENERGY_MAX, game.energy + ENERGY_MAX * 0.3)
            self.collected = False  # One-time effect
            return True
            
        elif self.type == "speed":
            # Speed boost (handled in game update)
            return True
            
        elif self.type == "gravity":
            # Gravity field (handled in game update)
            return True
            
        elif self.type == "shield":
            # Shield effect
            game.ball.has_shield = True
            return True
            
        elif self.type == "time":
            # Time slow effect (handled in game update)
            return True
            
        elif self.type == "magnet":
            # Magnet effect (handled in game update)
            return True
            
        return False
        
    def is_effect_active(self):
        """Check if the power-up effect is still active"""
        if not self.collected or self.effect_duration <= 0:
            return False
            
        current_time = time.time()
        return (current_time - self.effect_start_time) < self.effect_duration
        
    def get_remaining_time(self):
        """Get the remaining time for the effect in seconds"""
        if not self.collected or self.effect_duration <= 0:
            return 0
            
        current_time = time.time()
        return max(0, self.effect_duration - (current_time - self.effect_start_time))

# GravityWell
class GravityWell:
    def __init__(self, x, y, radius, strength):
        self.x = x
        self.y = y
        self.radius = radius
        self.strength = strength  # Positive pulls, negative pushes
        self.color = (100, 50, 150) if strength > 0 else (50, 150, 150)
        self.active = True
        self.pulse = 0
        self.particles = []
        
    def update(self, dt):
        self.pulse = (self.pulse + dt * 2) % (2 * math.pi)
        
        # Update particles
        for i in range(len(self.particles) - 1, -1, -1):
            x, y, vx, vy, size, life = self.particles[i]
            life -= dt
            if life <= 0:
                self.particles.pop(i)
                continue
                
            x += vx * dt * 60
            y += vy * dt * 60
            size = max(0.5, size - dt)
            self.particles[i] = (x, y, vx, vy, size, life)
            
        # Spawn new particles
        if random.random() < dt * 5:  # Adjust rate based on dt
            if self.strength > 0:  # Pulling well
                # Particles appear at edge and move toward center
                angle = random.uniform(0, 2 * math.pi)
                distance = self.radius * random.uniform(0.8, 1.2)
                px = self.x + math.cos(angle) * distance
                py = self.y + math.sin(angle) * distance
                
                # Velocity toward center
                vx = (self.x - px) * 0.1
                vy = (self.y - py) * 0.1
                
                size = random.uniform(1, 3)
                life = random.uniform(0.5, 1.0)
                self.particles.append((px, py, vx, vy, size, life))
            else:  # Pushing well
                # Particles appear near center and move outward
                angle = random.uniform(0, 2 * math.pi)
                distance = self.radius * random.uniform(0, 0.2)
                px = self.x + math.cos(angle) * distance
                py = self.y + math.sin(angle) * distance
                
                # Velocity away from center
                speed = random.uniform(1, 3)
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                
                size = random.uniform(1, 3)
                life = random.uniform(0.5, 1.0)
                self.particles.append((px, py, vx, vy, size, life))
        
    def draw(self, surface):
        if not self.active:
            return
            
        # Determine color based on whether it's pulling or pushing
        if self.strength > 0:
            # Pulling gravity well (purple)
            color = (100, 50, 150)
        else:
            # Pushing gravity well (teal)
            color = (50, 150, 150)
            
        # Draw the gravity well with transparency
        # Create a surface with per-pixel alpha
        s = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
        
        # Draw gradient circles from outside to inside
        pulse_radius = self.radius * (1 + 0.1 * math.sin(self.pulse))
        for r in range(int(pulse_radius), 0, -5):
            # Calculate alpha based on radius (more transparent toward edges)
            alpha = 150 * (1 - r/pulse_radius)
            pygame.draw.circle(s, color + (int(alpha),), (self.radius, self.radius), r)
            
        # Draw the surface onto the main surface
        surface.blit(s, (int(self.x - self.radius), int(self.y - self.radius)))
        
        # Draw particles
        for x, y, _, _, size, life in self.particles:
            alpha = int(255 * min(1, life * 2))
            pygame.draw.circle(surface, color + (alpha,), (int(x), int(y)), int(size))
        
        # Draw a small solid circle in the center with pulsing effect
        center_size = 5 + 2 * math.sin(self.pulse)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(center_size))
        
        # Draw direction indicators
        if self.strength > 0:  # Pulling
            # Draw arrows pointing inward
            arrow_length = 15
            num_arrows = 8
            for i in range(num_arrows):
                angle = 2 * math.pi * i / num_arrows
                arrow_x = self.x + math.cos(angle) * (self.radius * 0.7)
                arrow_y = self.y + math.sin(angle) * (self.radius * 0.7)
                end_x = arrow_x - math.cos(angle) * arrow_length
                end_y = arrow_y - math.sin(angle) * arrow_length
                
                # Arrow line
                pygame.draw.line(surface, (200, 100, 255, 150), 
                               (int(arrow_x), int(arrow_y)), 
                               (int(end_x), int(end_y)), 2)
                
                # Arrow head
                head_length = 5
                head_angle = 0.5  # radians
                h1_x = end_x + math.cos(angle + head_angle) * head_length
                h1_y = end_y + math.sin(angle + head_angle) * head_length
                h2_x = end_x + math.cos(angle - head_angle) * head_length
                h2_y = end_y + math.sin(angle - head_angle) * head_length
                
                pygame.draw.line(surface, (200, 100, 255, 150), 
                               (int(end_x), int(end_y)), 
                               (int(h1_x), int(h1_y)), 2)
                pygame.draw.line(surface, (200, 100, 255, 150), 
                               (int(end_x), int(end_y)), 
                               (int(h2_x), int(h2_y)), 2)
        else:  # Pushing
            # Draw arrows pointing outward
            arrow_length = 15
            num_arrows = 8
            for i in range(num_arrows):
                angle = 2 * math.pi * i / num_arrows
                start_x = self.x + math.cos(angle) * (self.radius * 0.3)
                start_y = self.y + math.sin(angle) * (self.radius * 0.3)
                end_x = start_x + math.cos(angle) * arrow_length
                end_y = start_y + math.sin(angle) * arrow_length
                
                # Arrow line
                pygame.draw.line(surface, (100, 200, 200, 150), 
                               (int(start_x), int(start_y)), 
                               (int(end_x), int(end_y)), 2)
                
                # Arrow head
                head_length = 5
                head_angle = 0.5  # radians
                h1_x = end_x + math.cos(angle + math.pi - head_angle) * head_length
                h1_y = end_y + math.sin(angle + math.pi - head_angle) * head_length
                h2_x = end_x + math.cos(angle + math.pi + head_angle) * head_length
                h2_y = end_y + math.sin(angle + math.pi + head_angle) * head_length
                
                pygame.draw.line(surface, (100, 200, 200, 150), 
                               (int(end_x), int(end_y)), 
                               (int(h1_x), int(h1_y)), 2)
                pygame.draw.line(surface, (100, 200, 200, 150), 
                               (int(end_x), int(end_y)), 
                               (int(h2_x), int(h2_y)), 2)
        
    def apply_force(self, ball):
        """Apply gravitational force to the ball based on distance"""
        if not self.active:
            return False
            
        dx = self.x - ball.x
        dy = self.y - ball.y
        distance_squared = dx*dx + dy*dy
        distance = math.sqrt(distance_squared)
        
        # Apply inverse square force within radius of influence
        if distance < self.radius and distance > 0:
            # Avoid division by zero and limit maximum force
            force = min(0.5, self.strength / (distance_squared)) * 30
            
            # Apply the force in the direction of the gravity well
            ball.vel_x += dx/distance * force
            ball.vel_y += dy/distance * force
            
            # Add particle effect if close to center
            if random.random() < 0.1 and distance < self.radius * 0.3:
                if self.strength > 0:  # Pulling
                    self.particles.append((
                        ball.x, ball.y, 
                        (self.x - ball.x) * 0.05, (self.y - ball.y) * 0.05,
                        random.uniform(1, 3), random.uniform(0.3, 0.8)
                    ))
                else:  # Pushing
                    self.particles.append((
                        ball.x, ball.y, 
                        (ball.x - self.x) * 0.05, (ball.y - self.y) * 0.05,
                        random.uniform(1, 3), random.uniform(0.3, 0.8)
                    ))
            
            return True
        return False

# Teleporter
class Teleporter:
    def __init__(self, x, y, pair_id, is_entrance=True, radius=25):
        self.x = x
        self.y = y
        self.radius = radius
        self.pair_id = pair_id  # Teleporters with same pair_id are linked
        self.is_entrance = is_entrance  # If False, it's an exit only
        self.cooldown = 0  # Cooldown to prevent immediate re-teleporting
        self.activation_time = 0  # Used for animation
        self.active = True
        self.pulse = 0
        self.particles = []
        
        # Colors - use blue tones for entrances, purple for exits
        if is_entrance:
            self.color = (0, 191, 255)  # Deep Sky Blue
            self.inner_color = (64, 224, 208)  # Turquoise
        else:
            self.color = (148, 0, 211)  # Dark Violet
            self.inner_color = (186, 85, 211)  # Medium Orchid
            
    def update(self, dt):
        self.pulse = (self.pulse + dt * 3) % (2 * math.pi)
        
        if self.cooldown > 0:
            self.cooldown -= dt * 60
            
        # Update particles
        for i in range(len(self.particles) - 1, -1, -1):
            x, y, vx, vy, size, life = self.particles[i]
            life -= dt
            if life <= 0:
                self.particles.pop(i)
                continue
                
            x += vx * dt * 60
            y += vy * dt * 60
            size = max(0.5, size - dt)
            self.particles[i] = (x, y, vx, vy, size, life)
            
        # Spawn new particles
        if random.random() < dt * 3:  # Adjust rate based on dt
            angle = random.uniform(0, 2 * math.pi)
            distance = self.radius * random.uniform(0.7, 1.0)
            px = self.x + math.cos(angle) * distance
            py = self.y + math.sin(angle) * distance
            
            # Particles rotate around teleporter
            speed = random.uniform(1, 2)
            vx = math.cos(angle + math.pi/2) * speed
            vy = math.sin(angle + math.pi/2) * speed
            
            size = random.uniform(1, 3)
            life = random.uniform(0.5, 1.5)
            
            particle_color = self.color if random.random() < 0.7 else self.inner_color
            self.particles.append((px, py, vx, vy, size, life, particle_color))
        
    def draw(self, surface):
        if not self.active:
            return
            
        # Calculate animation based on time
        pulse = 0.8 + 0.2 * math.sin(self.pulse)
        recent_activation = pygame.time.get_ticks() - self.activation_time < 500  # 500ms animation
        
        # Draw outer glow
        glow_radius = self.radius * 1.5 * pulse
        glow_surf = pygame.Surface((int(glow_radius*2), int(glow_radius*2)), pygame.SRCALPHA)
        for r in range(int(glow_radius), 0, -3):
            alpha = max(0, int(100 * (1 - r/glow_radius)))
            pygame.draw.circle(glow_surf, self.color[:3] + (alpha,), (int(glow_radius), int(glow_radius)), r)
        surface.blit(glow_surf, (int(self.x - glow_radius), int(self.y - glow_radius)))
        
        # Draw particles
        for x, y, _, _, size, life, color in self.particles:
            alpha = int(255 * min(1, life * 2))
            pygame.draw.circle(surface, color + (alpha,), (int(x), int(y)), int(size))
        
        # Draw activation animation
        if recent_activation:
            activation_progress = (pygame.time.get_ticks() - self.activation_time) / 500.0
            # Create expanding circles
            for i in range(3):
                progress = activation_progress - (i * 0.2)
                if 0 <= progress <= 1:
                    expand_radius = self.radius * (1 + progress * 2)
                    alpha = int(255 * (1 - progress))
                    # Create a surface with per-pixel alpha
                    s = pygame.Surface((expand_radius*2, expand_radius*2), pygame.SRCALPHA)
                    pygame.draw.circle(s, self.color + (alpha,), (expand_radius, expand_radius), expand_radius)
                    surface.blit(s, (int(self.x - expand_radius), int(self.y - expand_radius)))
        
        # Draw outer circle of teleporter
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.radius * pulse))
        
        # Draw inner circle (inverted pulse)
        inner_pulse = 0.8 + 0.2 * math.sin(self.pulse + math.pi)  # Opposite phase
        pygame.draw.circle(surface, self.inner_color, (int(self.x), int(self.y)), int(self.radius * 0.7 * inner_pulse))
        
        # Draw rotating pattern
        num_segments = 8
        segment_angle = 2 * math.pi / num_segments
        for i in range(num_segments):
            angle = self.pulse * 0.5 + i * segment_angle
            inner_radius = self.radius * 0.4
            outer_radius = self.radius * 0.7
            start_x = self.x + math.cos(angle) * inner_radius
            start_y = self.y + math.sin(angle) * inner_radius
            end_x = self.x + math.cos(angle) * outer_radius
            end_y = self.y + math.sin(angle) * outer_radius
            
            pygame.draw.line(surface, (255, 255, 255, 150), 
                           (int(start_x), int(start_y)), 
                           (int(end_x), int(end_y)), 2)
        
        # Draw center point that pulses
        center_pulse = 3 + 2 * math.sin(self.pulse * 2)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), int(center_pulse))
        
        # Draw pair_id number
        font = small_font
        text = font.render(str(self.pair_id), True, WHITE)
        text_rect = text.get_rect(center=(int(self.x), int(self.y + self.radius + 15)))
        surface.blit(text, text_rect)
        
        # Draw direction arrow for entrance/exit
        arrow_y_offset = -self.radius - 15
        if self.is_entrance:
            # Down arrow
            pygame.draw.polygon(surface, WHITE, [
                (self.x - 8, self.y + arrow_y_offset),
                (self.x + 8, self.y + arrow_y_offset),
                (self.x, self.y + arrow_y_offset + 10)
            ])
        else:
            # Up arrow
            pygame.draw.polygon(surface, WHITE, [
                (self.x - 8, self.y + arrow_y_offset + 10),
                (self.x + 8, self.y + arrow_y_offset + 10),
                (self.x, self.y + arrow_y_offset)
            ])
        
        # If on cooldown, show visual indicator
        if self.cooldown > 0:
            cooldown_pct = self.cooldown / 60  # Assuming 60 frames = 1 second cooldown
            # Draw cooldown arc
            rect = pygame.Rect(int(self.x - self.radius*0.8), int(self.y - self.radius*0.8), 
                              int(self.radius*1.6), int(self.radius*1.6))
            pygame.draw.arc(surface, (255, 255, 255, 180), rect, 
                           0, cooldown_pct * 2 * math.pi, 3)
    
    def check_collision(self, ball):
        if not self.active or self.cooldown > 0 or not self.is_entrance:
            return False
            
        distance_squared = (ball.x - self.x)**2 + (ball.y - self.y)**2
        return distance_squared < (ball.radius + self.radius * 0.7)**2
    
    def activate(self):
        self.activation_time = pygame.time.get_ticks()
        self.cooldown = 60  # 1 second cooldown (assuming 60 FPS)
        
        # Add particle burst
        num_particles = 30
        for _ in range(num_particles):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(3, 7)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.uniform(2, 5)
            life = random.uniform(0.5, 1.0)
            particle_color = self.color if random.random() < 0.7 else self.inner_color
            self.particles.append((self.x, self.y, vx, vy, size, life, particle_color))

# Particle System
class Particle:
    def __init__(self, x, y, vel_x, vel_y, color, size, life, gravity=0, fade=True):
        self.x = x
        self.y = y
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.color = color
        self.original_color = color[:3] if len(color) > 3 else color
        self.size = size
        self.original_size = size
        self.life = life
        self.max_life = life
        self.gravity = gravity
        self.fade = fade
        
    def update(self, dt):
        # Update position
        self.x += self.vel_x * dt * 60
        self.y += self.vel_y * dt * 60
        
        # Apply gravity
        self.vel_y += self.gravity * dt * 60
        
        # Apply drag/friction
        self.vel_x *= 0.98
        self.vel_y *= 0.98
        
        # Reduce life
        self.life -= dt
        
        # Shrink particle as it ages if fade is enabled
        if self.fade:
            life_ratio = max(0, self.life / self.max_life)
            self.size = self.original_size * life_ratio
            
    def draw(self, surface):
        # Calculate alpha based on remaining life
        if self.fade:
            alpha = int(255 * (self.life / self.max_life))
        else:
            alpha = 255
            
        # Use the provided color with calculated alpha
        if len(self.original_color) == 3:
            color_with_alpha = self.original_color + (alpha,)
        else:
            # If color already has alpha, use it but scale by life
            color_with_alpha = self.original_color + (int(self.color[3] * (self.life / self.max_life)),)
            
        # Create a surface with per-pixel alpha
        if self.size > 0:
            s = pygame.Surface((int(self.size*2), int(self.size*2)), pygame.SRCALPHA)
            pygame.draw.circle(s, color_with_alpha, (int(self.size), int(self.size)), int(self.size))
            surface.blit(s, (int(self.x - self.size), int(self.y - self.size)))
        
    def is_alive(self):
        return self.life > 0

class ParticleSystem:
    def __init__(self):
        self.particles = []
        
    def add_particle(self, x, y, vel_x=0, vel_y=0, color=(255, 255, 255), size=5, life=1.0, gravity=0, fade=True):
        self.particles.append(Particle(x, y, vel_x, vel_y, color, size, life, gravity, fade))
        
    def add_explosion(self, x, y, color, particle_count=20, size_range=(2, 6), speed_range=(1, 3), life_range=(0.5, 1.5), gravity=0):
        for _ in range(particle_count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(speed_range[0], speed_range[1])
            vel_x = math.cos(angle) * speed
            vel_y = math.sin(angle) * speed
            size = random.uniform(size_range[0], size_range[1])
            life = random.uniform(life_range[0], life_range[1])
            
            # Add some slight variation to color
            if len(color) == 3:
                r = min(255, max(0, color[0] + random.randint(-20, 20)))
                g = min(255, max(0, color[1] + random.randint(-20, 20)))
                b = min(255, max(0, color[2] + random.randint(-20, 20)))
                particle_color = (r, g, b)
            else:
                r = min(255, max(0, color[0] + random.randint(-20, 20)))
                g = min(255, max(0, color[1] + random.randint(-20, 20)))
                b = min(255, max(0, color[2] + random.randint(-20, 20)))
                a = color[3]
                particle_color = (r, g, b, a)
                
            self.add_particle(x, y, vel_x, vel_y, particle_color, size, life, gravity)
            
    def add_trail(self, x, y, color, direction_x, direction_y, particle_count=5, life_range=(0.3, 0.8), size_range=(1, 3)):
        # Create particles that move in the opposite direction of movement for a trail effect
        for _ in range(particle_count):
            # Slightly randomize position
            px = x + random.uniform(-5, 5)
            py = y + random.uniform(-5, 5)
            
            # Calculate velocities (opposite of movement direction)
            velocity_x = -direction_x * random.uniform(0.1, 0.5) 
            velocity_y = -direction_y * random.uniform(0.1, 0.5)
            
            # Add some randomness to velocity
            velocity_x += random.uniform(-0.5, 0.5)
            velocity_y += random.uniform(-0.5, 0.5)
            
            # Create the particle
            size = random.uniform(size_range[0], size_range[1])
            life = random.uniform(life_range[0], life_range[1])
            
            # Add some slight variation to color
            if len(color) == 3:
                r = min(255, max(0, color[0] + random.randint(-20, 20)))
                g = min(255, max(0, color[1] + random.randint(-20, 20)))
                b = min(255, max(0, color[2] + random.randint(-20, 20)))
                particle_color = (r, g, b)
            else:
                r = min(255, max(0, color[0] + random.randint(-20, 20)))
                g = min(255, max(0, color[1] + random.randint(-20, 20)))
                b = min(255, max(0, color[2] + random.randint(-20, 20)))
                a = color[3]
                particle_color = (r, g, b, a)
                
            self.add_particle(px, py, velocity_x, velocity_y, particle_color, size, life)
            
    def add_text_particles(self, x, y, text, color, font=None, burst=True):
        if font is None:
            font = small_font
            
        text_surf = font.render(text, True, color)
        text_pixels = pygame.surfarray.array3d(text_surf)
        
        # Scan the text surface for non-black pixels and create particles
        step = 2  # Only sample every nth pixel for performance
        for px in range(0, text_surf.get_width(), step):
            for py in range(0, text_surf.get_height(), step):
                # If pixel isn't black (text pixel)
                if tuple(text_pixels[px, py]) != (0, 0, 0):
                    # Adjust position to world coordinates
                    world_x = x - text_surf.get_width() // 2 + px
                    world_y = y - text_surf.get_height() // 2 + py
                    
                    if burst:
                        # Burst particles outward
                        direction_x = (px - text_surf.get_width() // 2) / (text_surf.get_width() // 2) * 2
                        direction_y = (py - text_surf.get_height() // 2) / (text_surf.get_height() // 2) * 2
                        speed = random.uniform(0.5, 1.5)
                        vel_x = direction_x * speed
                        vel_y = direction_y * speed
                    else:
                        # Random gentle movement
                        vel_x = random.uniform(-0.5, 0.5)
                        vel_y = random.uniform(-0.5, 0.5)
                    
                    size = random.uniform(1, 2)
                    life = random.uniform(0.5, 1.5)
                    
                    self.add_particle(world_x, world_y, vel_x, vel_y, color, size, life, gravity=0.05)
    
    def update(self, dt):
        # Update all particles and remove dead ones
        for particle in self.particles:
            particle.update(dt)
            
        self.particles = [p for p in self.particles if p.is_alive()]
            
    def draw(self, surface):
        for particle in self.particles:
            particle.draw(surface)
            
    def clear(self):
        self.particles = []

# Bounce Pad
class BouncePad:
    def __init__(self, x, y, width, height, direction=(0, -1), strength=1.5):
        self.rect = pygame.Rect(x, y, width, height)
        self.direction = normalize_vector(direction[0], direction[1])
        self.strength = strength
        self.color = (255, 165, 0)  # Orange
        self.active = True
        self.activation_time = 0
        self.particles = []
        self.animation_timer = 0
        
    def update(self, dt):
        self.animation_timer += dt
        
        # Update activation animation
        if pygame.time.get_ticks() - self.activation_time < 500:
            # Spawning animation particles
            if random.random() < dt * 10:
                px = random.uniform(self.rect.left, self.rect.right)
                py = random.uniform(self.rect.top, self.rect.bottom)
                vx = self.direction[0] * random.uniform(2, 4)
                vy = self.direction[1] * random.uniform(2, 4)
                size = random.uniform(2, 4)
                life = random.uniform(0.2, 0.5)
                self.particles.append((px, py, vx, vy, size, life))
        
        # Update particles
        for i in range(len(self.particles) - 1, -1, -1):
            x, y, vx, vy, size, life = self.particles[i]
            life -= dt
            if life <= 0:
                self.particles.pop(i)
                continue
                
            x += vx * dt * 60
            y += vy * dt * 60
            size = max(0.5, size - dt * 2)
            self.particles[i] = (x, y, vx, vy, size, life)
        
    def draw(self, surface):
        # Base rectangle
        pygame.draw.rect(surface, self.color, self.rect)
        
        # Draw arrow indicating direction
        arrow_length = min(self.rect.width, self.rect.height) * 0.8
        center_x = self.rect.centerx
        center_y = self.rect.centery
        end_x = center_x + self.direction[0] * arrow_length / 2
        end_y = center_y + self.direction[1] * arrow_length / 2
        
        # Arrow shaft
        pygame.draw.line(surface, BLACK, (center_x, center_y), (end_x, end_y), 3)
        
        # Arrow head
        head_size = arrow_length * 0.3
        angle = math.atan2(self.direction[1], self.direction[0])
        left_angle = angle + math.pi * 3/4
        right_angle = angle - math.pi * 3/4
        
        point1 = (end_x, end_y)
        point2 = (end_x - math.cos(left_angle) * head_size, 
                 end_y - math.sin(left_angle) * head_size)
        point3 = (end_x - math.cos(right_angle) * head_size, 
                 end_y - math.sin(right_angle) * head_size)
        
        pygame.draw.polygon(surface, BLACK, [point1, point2, point3])
        
        # Animation effect - pulsing
        pulse = (math.sin(self.animation_timer * 5) + 1) / 2
        pulse_width = int(3 + 2 * pulse)
        pygame.draw.rect(surface, (255, 220, 120), self.rect, pulse_width)
        
        # Draw particles
        for x, y, _, _, size, life in self.particles:
            alpha = int(255 * min(1, life * 5))
            pygame.draw.circle(surface, self.color + (alpha,), (int(x), int(y)), int(size))
        
        # If recently activated, draw highlight
        if pygame.time.get_ticks() - self.activation_time < 300:
            highlight_alpha = int(255 * (1 - (pygame.time.get_ticks() - self.activation_time) / 300))
            highlight_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            highlight_surf.fill((255, 255, 255, highlight_alpha))
            surface.blit(highlight_surf, self.rect)
    
    def check_collision(self, ball):
        if not self.active:
            return False
            
        # Check if ball is colliding with bounce pad
        closest_x = max(self.rect.left, min(ball.x, self.rect.right))
        closest_y = max(self.rect.top, min(ball.y, self.rect.bottom))
        
        distance_squared = (ball.x - closest_x)**2 + (ball.y - closest_y)**2
        
        if distance_squared < ball.radius**2:
            # Calculate current velocity magnitude
            current_speed = math.sqrt(ball.vel_x**2 + ball.vel_y**2)
            
            # Apply bounce in specified direction
            new_speed = max(current_speed, 5) * self.strength  # Ensure minimum bounce speed
            ball.vel_x = self.direction[0] * new_speed
            ball.vel_y = self.direction[1] * new_speed
            
            # Record activation for animation
            self.activation_time = pygame.time.get_ticks()
            
            # Spawn particles
            num_particles = 15
            for _ in range(num_particles):
                angle_offset = random.uniform(-0.5, 0.5)
                base_angle = math.atan2(self.direction[1], self.direction[0])
                particle_angle = base_angle + angle_offset
                
                speed = random.uniform(2, 5)
                vx = math.cos(particle_angle) * speed
                vy = math.sin(particle_angle) * speed
                
                px = closest_x
                py = closest_y
                
                size = random.uniform(2, 4)
                life = random.uniform(0.2, 0.5)
                
                self.particles.append((px, py, vx, vy, size, life))
                
            return True
        
        return False

# Game class
class Game:
    def __init__(self):
        self.state = GameState.MAIN_MENU
        self.prev_state = None
        self.level_num = 1
        self.max_unlocked_level = 1
        self.ball = None
        self.energy = ENERGY_MAX
        self.score = 0
        self.stars_collected = 0
        self.total_stars = 0
        self.time_factor = 1.0  # For time slowdown effects
        self.force_multiplier = 0.3
        self.walls = []
        self.surfaces = []
        self.targets = []
        self.power_ups = []
        self.active_power_ups = []
        self.gravity_wells = []
        self.teleporters = []
        self.bounce_pads = []
        self.level_start_time = 0
        self.level_time = 0
        self.pause_start_time = 0
        self.paused = False
        self.level_transition_time = 0
        self.level_transition_direction = 1  # 1 for next level, -1 for previous
        self.game_over_reason = ""
        self.gravity_field_active = False
        self.gravity_field_strength = 0
        self.gravity_field_radius = 150
        self.gravity_field_color = (148, 0, 211, 80)  # Purple with transparency
        self.magnet_active = False
        self.magnet_strength = 0
        self.magnet_radius = 200
        self.screen_shake = 0
        self.transition_alpha = 0
        self.level_complete_time = 0
        self.level_complete_stars = 0
        self.particle_system = ParticleSystem()
        self.toasts = []
        self.settings = self.load_settings()
        self.highscores = self.load_highscores()
        self.level_data = self.load_level_data()
        self.time_dilated = False
        self.dt = 1/60  # Default dt value
        
        # Menu elements
        self.menu_buttons = {}
        self.level_select_buttons = []
        self.settings_sliders = {}
        self.init_menu_elements()
        
        # Tutorial state
        self.tutorial_step = 0
        self.tutorial_messages = [
            "Welcome to Inertia! Use arrow keys to apply force.",
            "Your ball keeps moving until something stops it.",
            "Collect all green targets to complete the level.",
            "Your energy is limited - use it wisely!",
            "Different surfaces affect your movement.",
            "Collect power-ups for special abilities.",
            "Press P to pause, R to restart a level."
        ]
        
    def load_settings(self):
        """Load game settings or create defaults"""
        settings_file = "settings.json"
        default_settings = {
            "music_volume": 0.5,
            "sound_volume": 0.7,
            "screen_shake": True,
            "particles": True,
            "fullscreen": False,
            "controls": {
                "up": pygame.K_UP,
                "down": pygame.K_DOWN,
                "left": pygame.K_LEFT,
                "right": pygame.K_RIGHT,
                "pause": pygame.K_p,
                "reset": pygame.K_r
            }
        }
        
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    return json.load(f)
            except:
                return default_settings
        else:
            with open(settings_file, 'w') as f:
                json.dump(default_settings, f, indent=4)
            return default_settings
    
    def save_settings(self):
        """Save current settings to file"""
        with open("settings.json", 'w') as f:
            json.dump(self.settings, f, indent=4)
    
    def load_highscores(self):
        """Load high scores from file or create new if doesn't exist"""
        default_highscores = {"level_times": {}, "level_scores": {}, "level_stars": {}, "total_stars": 0}
        
        if os.path.exists(HIGHSCORE_FILE):
            try:
                with open(HIGHSCORE_FILE, 'r') as f:
                    highscores = json.load(f)
                    
                    # Check for missing keys and add them
                    for key in default_highscores:
                        if key not in highscores:
                            highscores[key] = default_highscores[key]
                    
                    return highscores
            except:
                # If file is corrupted or not found, create new
                return default_highscores
        else:
            # Create new high scores file
            self.save_highscores(default_highscores)
            return default_highscores
    
    def save_highscores(self, highscores=None):
        """Save high scores to file"""
        if highscores is None:
            highscores = self.highscores
        with open(HIGHSCORE_FILE, 'w') as f:
            json.dump(highscores, f, indent=4)
    
    def load_level_data(self):
        """Load level progression data"""
        level_file = "levels.json"
        default_data = {
            "unlocked": 1,
            "stars": {},  # {level_num: stars_collected}
            "total_stars": 0
        }
        
        if os.path.exists(level_file):
            try:
                with open(level_file, 'r') as f:
                    data = json.load(f)
                    # Update max unlocked level
                    self.max_unlocked_level = data.get("unlocked", 1)
                    # Update total stars
                    self.total_stars = data.get("total_stars", 0)
                    return data
            except:
                return default_data
        else:
            with open(level_file, 'w') as f:
                json.dump(default_data, f, indent=4)
            return default_data
    
    def save_level_data(self):
        """Save level progression data"""
        self.level_data["unlocked"] = self.max_unlocked_level
        self.level_data["total_stars"] = self.total_stars
        
        with open("levels.json", 'w') as f:
            json.dump(self.level_data, f, indent=4)
    
    def init_menu_elements(self):
        """Initialize all menu UI elements"""
        # Main menu buttons
        btn_width, btn_height = 220, 60
        center_x = WIDTH // 2
        center_y = HEIGHT // 2
        spacing = 70
        
        self.menu_buttons = {
            "main": [
                Button(center_x - btn_width//2, center_y - spacing, btn_width, btn_height, 
                      "Play", lambda: self.set_state(GameState.LEVEL_SELECT)),
                Button(center_x - btn_width//2, center_y, btn_width, btn_height, 
                      "Settings", lambda: self.set_state(GameState.SETTINGS)),
                Button(center_x - btn_width//2, center_y + spacing, btn_width, btn_height, 
                      "Credits", lambda: self.set_state(GameState.CREDITS)),
                Button(center_x - btn_width//2, center_y + spacing*2, btn_width, btn_height, 
                      "Quit", pygame.quit)
            ],
            "paused": [
                Button(center_x - btn_width//2, center_y - spacing, btn_width, btn_height, 
                      "Resume", self.toggle_pause),
                Button(center_x - btn_width//2, center_y, btn_width, btn_height, 
                      "Restart Level", self.restart_level),
                Button(center_x - btn_width//2, center_y + spacing, btn_width, btn_height, 
                      "Level Select", lambda: self.set_state(GameState.LEVEL_SELECT)),
                Button(center_x - btn_width//2, center_y + spacing*2, btn_width, btn_height, 
                      "Main Menu", lambda: self.set_state(GameState.MAIN_MENU))
            ],
            "level_complete": [
                Button(center_x - btn_width//2, center_y + spacing, btn_width, btn_height, 
                      "Next Level", self.next_level),
                Button(center_x - btn_width//2, center_y + spacing*2, btn_width, btn_height, 
                      "Level Select", lambda: self.set_state(GameState.LEVEL_SELECT))
            ],
            "game_over": [
                Button(center_x - btn_width//2, center_y, btn_width, btn_height, 
                      "Try Again", self.restart_level),
                Button(center_x - btn_width//2, center_y + spacing, btn_width, btn_height, 
                      "Level Select", lambda: self.set_state(GameState.LEVEL_SELECT))
            ],
            "settings": [
                Button(center_x - btn_width//2, HEIGHT - 120, btn_width, btn_height, 
                      "Back", lambda: self.set_state(self.prev_state or GameState.MAIN_MENU))
            ],
            "credits": [
                Button(center_x - btn_width//2, HEIGHT - 120, btn_width, btn_height, 
                      "Back", lambda: self.set_state(GameState.MAIN_MENU))
            ],
            "level_select": [
                Button(center_x - btn_width//2, HEIGHT - 120, btn_width, btn_height, 
                      "Back", lambda: self.set_state(GameState.MAIN_MENU))
            ]
        }
        
        # Settings sliders
        slider_width = 300
        slider_height = 20
        slider_x = center_x - slider_width//2
        slider_spacing = 70
        
        self.settings_sliders = {
            "music_volume": Slider(slider_x, center_y - slider_spacing*2, slider_width, slider_height, 
                                  0, 1, self.settings["music_volume"], "Music Volume", show_as_percent=True),
            "sound_volume": Slider(slider_x, center_y - slider_spacing, slider_width, slider_height, 
                                  0, 1, self.settings["sound_volume"], "Sound Volume", show_as_percent=True)
        }
        
        # Toggle buttons for boolean settings
        self.settings_toggle_buttons = [
            Button(slider_x, center_y, slider_width, btn_height, 
                  f"Screen Shake: {'ON' if self.settings['screen_shake'] else 'OFF'}", 
                  self.toggle_screen_shake),
            Button(slider_x, center_y + slider_spacing, slider_width, btn_height, 
                  f"Particles: {'ON' if self.settings['particles'] else 'OFF'}", 
                  self.toggle_particles),
            Button(slider_x, center_y + slider_spacing*2, slider_width, btn_height, 
                  f"Fullscreen: {'ON' if self.settings['fullscreen'] else 'OFF'}", 
                  self.toggle_fullscreen)
        ]
        
        # Initialize level select buttons
        self.create_level_select_buttons()
    
    def create_level_select_buttons(self):
        """Create buttons for level selection screen"""
        self.level_select_buttons = []
        
        # Calculate grid dimensions
        grid_cols = 5
        grid_rows = 5
        button_size = 80
        spacing = 20
        
        # Calculate starting position to center the grid
        start_x = (WIDTH - (grid_cols * button_size + (grid_cols - 1) * spacing)) // 2
        start_y = 180
        
        # Get highest unlocked level
        self.max_unlocked_level = self.level_data.get("unlocked", 1)
        
        # Create button for each level
        for level in range(1, MAX_LEVELS + 1):
            row = (level - 1) // grid_cols
            col = (level - 1) % grid_cols
            
            x = start_x + col * (button_size + spacing)
            y = start_y + row * (button_size + spacing + 30)  # Extra space for stars
            
            # Get stars collected for this level
            stars = self.level_data.get("stars", {}).get(str(level), 0)
            
            # Check if level is unlocked
            unlocked = level <= self.max_unlocked_level
            
            # Create button data (we'll draw these manually)
            self.level_select_buttons.append({
                "level": level,
                "rect": pygame.Rect(x, y, button_size, button_size),
                "stars": stars,
                "unlocked": unlocked,
                "hover": False,
                "pulse": 0
            })
    
    def update_level_select_buttons(self):
        """Update level selection buttons with current progress"""
        for button in self.level_select_buttons:
            level = button["level"]
            level_key = str(level)
            button["stars"] = self.level_data.get("stars", {}).get(level_key, 0)
            button["unlocked"] = level <= self.max_unlocked_level
    
    def toggle_screen_shake(self):
        """Toggle screen shake setting"""
        self.settings["screen_shake"] = not self.settings["screen_shake"]
        for btn in self.settings_toggle_buttons:
            if "Screen Shake" in btn.text:
                btn.text = f"Screen Shake: {'ON' if self.settings['screen_shake'] else 'OFF'}"
        self.save_settings()
        play_sound("button_click")
    
    def toggle_particles(self):
        """Toggle particles setting"""
        self.settings["particles"] = not self.settings["particles"]
        for btn in self.settings_toggle_buttons:
            if "Particles" in btn.text:
                btn.text = f"Particles: {'ON' if self.settings['particles'] else 'OFF'}"
        self.save_settings()
        play_sound("button_click")
    
    def toggle_fullscreen(self):
        """Toggle fullscreen setting"""
        self.settings["fullscreen"] = not self.settings["fullscreen"]
        for btn in self.settings_toggle_buttons:
            if "Fullscreen" in btn.text:
                btn.text = f"Fullscreen: {'ON' if self.settings['fullscreen'] else 'OFF'}"
                
        # Apply fullscreen change
        if self.settings["fullscreen"]:
            pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        else:
            pygame.display.set_mode((WIDTH, HEIGHT))
            
        self.save_settings()
        play_sound("button_click")
    
    def set_state(self, new_state):
        """Change game state with proper transitions"""
        if new_state == self.state:
            return
            
        self.prev_state = self.state
        self.state = new_state
        
        # Handle specific state changes
        if new_state == GameState.PLAYING:
            # If starting a new game
            if self.prev_state == GameState.LEVEL_SELECT:
                self.setup_level(self.level_num)
                play_sound("level_complete", 0.5)
                
        elif new_state == GameState.LEVEL_SELECT:
            # Update level select buttons
            self.update_level_select_buttons()
            play_sound("button_click")
            
        elif new_state == GameState.MAIN_MENU:
            # Play menu music
            play_music("menu")
            play_sound("button_click")
            
        elif new_state == GameState.PAUSED:
            self.pause_start_time = time.time()
            play_sound("button_click")
            
        elif new_state == GameState.LEVEL_COMPLETE:
            self.level_complete_time = time.time()
            play_sound("level_complete")
            
            # Create celebration particles
            for _ in range(10):
                x = random.randint(WIDTH//4, WIDTH*3//4)
                y = random.randint(HEIGHT//4, HEIGHT*3//4)
                color = (
                    random.randint(100, 255),
                    random.randint(100, 255),
                    random.randint(100, 255)
                )
                self.particle_system.add_explosion(x, y, color, 
                                                  particle_count=30,
                                                  speed_range=(2, 6),
                                                  size_range=(2, 8),
                                                  life_range=(1, 3))
    
    def toggle_pause(self):
        """Toggle game pause state"""
        if self.state == GameState.PLAYING:
            self.set_state(GameState.PAUSED)
        elif self.state == GameState.PAUSED:
            self.set_state(GameState.PLAYING)
            # Adjust level start time to account for pause duration
            pause_duration = time.time() - self.pause_start_time
            self.level_start_time += pause_duration
    
    def restart_level(self):
        """Restart the current level"""
        self.setup_level(self.level_num)
        self.set_state(GameState.PLAYING)
        play_sound("button_click")
    
    def next_level(self):
        """Advance to the next level"""
        if self.level_num < MAX_LEVELS:
            self.level_num += 1
            self.setup_level(self.level_num)
            self.set_state(GameState.PLAYING)
        else:
            # Game completed!
            self.add_toast("Congratulations! You've completed all levels!")
            self.set_state(GameState.MAIN_MENU)
    
    def add_toast(self, message, duration=2.0, color=WHITE):
        """Add a toast notification"""
        self.toasts.append(Toast(message, duration, color))
    
    def update_highscores(self):
        """Update high scores for the current level"""
        level_key = str(self.level_num)
        
        # Ensure all required keys exist
        if "level_times" not in self.highscores:
            self.highscores["level_times"] = {}
        if "level_scores" not in self.highscores:
            self.highscores["level_scores"] = {}
        if "level_stars" not in self.highscores:
            self.highscores["level_stars"] = {}
        if "total_stars" not in self.highscores:
            self.highscores["total_stars"] = 0
            
        # Update best time
        if self.level_time > 0:  # Only update if we have a valid time
            if (level_key not in self.highscores["level_times"] or 
                self.level_time < self.highscores["level_times"][level_key]):
                self.highscores["level_times"][level_key] = self.level_time
                self.add_toast(f"New best time: {int(self.level_time)} seconds!")
                
        # Update best score
        if (level_key not in self.highscores["level_scores"] or 
            self.score > self.highscores["level_scores"][level_key]):
            self.highscores["level_scores"][level_key] = self.score
            self.add_toast(f"New high score: {self.score} points!")
            
        # Update stars
        if (level_key not in self.highscores["level_stars"] or 
            self.stars_collected > self.highscores["level_stars"][level_key]):
            # Calculate new stars gained
            new_stars = self.stars_collected - self.highscores["level_stars"].get(level_key, 0)
            if new_stars > 0:
                self.total_stars += new_stars
                self.highscores["total_stars"] = self.total_stars
                self.add_toast(f"+{new_stars} new stars collected!")
                
            self.highscores["level_stars"][level_key] = self.stars_collected
            
        # Update level progression data
        if "stars" not in self.level_data:
            self.level_data["stars"] = {}
            
        self.level_data["stars"][level_key] = max(
            self.level_data["stars"].get(level_key, 0),
            self.stars_collected
        )
        self.level_data["total_stars"] = self.total_stars
        
        # Unlock next level if not already unlocked
        if self.level_num == self.max_unlocked_level and self.level_num < MAX_LEVELS:
            # Check if we have enough stars to unlock next level
            star_requirements = self.level_num * REQUIRED_STARS_TO_UNLOCK
            if self.total_stars >= star_requirements:
                self.max_unlocked_level = self.level_num + 1
                self.level_data["unlocked"] = self.max_unlocked_level
                self.add_toast(f"Level {self.max_unlocked_level} unlocked!")
            else:
                stars_needed = star_requirements - self.total_stars
                self.add_toast(f"Need {stars_needed} more stars to unlock next level")
        
        # Save the updated highscores
        self.save_highscores()
        self.save_level_data()
    
    def is_position_valid(self, x, y, radius, check_walls=True, check_objects=True, avoid_start=True):
        """Check if a position is valid (not overlapping with other objects)"""
        # Check if position is within gameplay bounds
        if x - radius < 20 or x + radius > WIDTH - 20 or y - radius < 20 or y + radius > HEIGHT - 20:
            return False
            
        if check_walls:
            for wall in self.walls:
                # Simple rectangular check first
                if (x - radius < wall.rect.right and 
                    x + radius > wall.rect.left and 
                    y - radius < wall.rect.bottom and 
                    y + radius > wall.rect.top):
                    
                    # For the center of the rect
                    if (wall.rect.left < x < wall.rect.right and 
                        wall.rect.top < y < wall.rect.bottom):
                        return False
                    
                    # Detailed corner check
                    corners = [
                        (wall.rect.left, wall.rect.top),
                        (wall.rect.right, wall.rect.top),
                        (wall.rect.left, wall.rect.bottom),
                        (wall.rect.right, wall.rect.bottom)
                    ]
                    
                    # For the corners
                    for corner_x, corner_y in corners:
                        if distance(x, y, corner_x, corner_y) < radius:
                            return False
        
        if check_objects:
            # Check against other game objects
            for target in self.targets:
                if distance(x, y, target.x, target.y) < radius + target.radius + 10:
                    return False
                    
            for power_up in self.power_ups:
                if distance(x, y, power_up.x, power_up.y) < radius + power_up.radius + 10:
                    return False
                    
            for well in self.gravity_wells:
                if distance(x, y, well.x, well.y) < radius + 20:
                    return False
                    
            for teleporter in self.teleporters:
                if distance(x, y, teleporter.x, teleporter.y) < radius + teleporter.radius + 10:
                    return False
                    
            for pad in self.bounce_pads:
                # Rectangular check
                rect_expanded = pad.rect.inflate(radius*2, radius*2)
                if rect_expanded.collidepoint(x, y):
                    return False
        
        # Check against ball starting position
        if avoid_start and self.ball:
            if distance(x, y, self.ball.x, self.ball.y) < radius + self.ball.radius + 50:
                return False
                
        return True
    
    def get_valid_position(self, radius, min_distance_from_center=100, max_attempts=100):
        """Get a random valid position for object placement"""
        center_x, center_y = WIDTH // 2, HEIGHT // 2
        
        for _ in range(max_attempts):
            # Generate random position, biased toward edges
            if random.random() < 0.7:  # 70% chance to be away from center
                # Pick a side
                side = random.randint(0, 3)
                if side == 0:  # Top
                    x = random.randint(50, WIDTH - 50)
                    y = random.randint(50, HEIGHT // 3)
                elif side == 1:  # Right
                    x = random.randint(WIDTH * 2 // 3, WIDTH - 50)
                    y = random.randint(50, HEIGHT - 50)
                elif side == 2:  # Bottom
                    x = random.randint(50, WIDTH - 50)
                    y = random.randint(HEIGHT * 2 // 3, HEIGHT - 50)
                else:  # Left
                    x = random.randint(50, WIDTH // 3)
                    y = random.randint(50, HEIGHT - 50)
            else:
                # Random position anywhere
                x = random.randint(50, WIDTH - 50)
                y = random.randint(50, HEIGHT - 50)
                
            # Check if position is valid
            if (self.is_position_valid(x, y, radius) and 
                distance(x, y, center_x, center_y) > min_distance_from_center):
                return x, y
                
        # If no valid position found after max attempts, try a simpler approach
        for _ in range(max_attempts):
            x = random.randint(50, WIDTH - 50)
            y = random.randint(50, HEIGHT - 50)
            if self.is_position_valid(x, y, radius):
                return x, y
                
        # If still no valid position, return center (should rarely happen)
        return WIDTH // 2, HEIGHT // 2
    
    def setup_level(self, level_num=None):
        """Set up a level with all game objects"""
        if level_num is not None:
            self.level_num = level_num
            
        # Create ball at center left
        self.ball = Ball(100, HEIGHT // 2)
        self.energy = ENERGY_MAX
        
        # Start the level timer
        self.level_start_time = time.time()
        self.level_time = 0
        self.score = 0
        self.stars_collected = 0
        
        # Reset active power-ups and effects
        self.active_power_ups = []
        self.ball.has_shield = False
        self.gravity_field_active = False
        self.gravity_field_strength = 0
        self.magnet_active = False
        self.time_dilated = False
        self.time_factor = 1.0
        
        # Clear previous level objects
        self.walls = []
        self.surfaces = []
        self.targets = []
        self.power_ups = []
        self.gravity_wells = []
        self.teleporters = []
        self.bounce_pads = []
        self.particle_system.clear()
        
        # Add outer walls (slightly inside the screen edges)
        self.walls.append(Wall(0, 0, WIDTH, 20))  # Top
        self.walls.append(Wall(0, HEIGHT-20, WIDTH, 20))  # Bottom
        self.walls.append(Wall(0, 0, 20, HEIGHT))  # Left
        self.walls.append(Wall(WIDTH-20, 0, 20, HEIGHT))  # Right
        
        # Setup level based on level number
        if self.level_num == 1:  # Tutorial level
            # Simple first level with tutorial elements
            self.targets.append(Target(WIDTH - 100, HEIGHT // 2))
            self.walls.append(Wall(300, HEIGHT//2 - 100, 20, 200))
            
            # Add a simple power-up (energy)
            self.power_ups.append(PowerUp(200, HEIGHT//2, "energy"))
            
            # Add a small ice surface
            self.surfaces.append(Surface(350, 250, 150, 150, "ice"))
            
            # Set tutorial mode
            self.tutorial_step = 0
            
        elif self.level_num == 2:
            # Level with multiple targets
            # Add some walls
            self.walls.append(Wall(200, 100, 20, 200))
            self.walls.append(Wall(400, 200, 300, 20))
            self.walls.append(Wall(300, 400, 400, 20))
            
            # Add targets
            self.targets.append(Target(WIDTH - 100, HEIGHT - 100))
            self.targets.append(Target(WIDTH - 100, 100))
            
            # Add a star target (optional)
            star_target = Target(500, 300, required=False)
            star_target.color = YELLOW
            self.targets.append(star_target)
            
            # Add surfaces
            self.surfaces.append(Surface(220, 220, 280, 180, "ice"))
            
            # Add power-ups
            self.power_ups.append(PowerUp(300, 150, "speed"))
            self.power_ups.append(PowerUp(500, 400, "shield"))
            
            # Add a bounce pad
            self.bounce_pads.append(BouncePad(100, 400, 80, 20, (1, -1), 1.5))
            
        elif self.level_num == 3:
            # Level with gravity wells and teleporters
            # Add some walls in a maze pattern
            self.walls.append(Wall(200, 100, 20, 200))
            self.walls.append(Wall(400, 300, 20, 200))
            self.walls.append(Wall(250, 250, 300, 20))
            
            # Add targets
            self.targets.append(Target(700, 100))
            self.targets.append(Target(700, 500))
            self.targets.append(Target(400, 500))
            
            # Add a star target (optional)
            star_target = Target(300, 200, required=False)
            star_target.color = YELLOW
            self.targets.append(star_target)
            
            # Add surfaces
            self.surfaces.append(Surface(220, 400, 150, 150, "mud"))
            self.surfaces.append(Surface(500, 150, 200, 100, "ice"))
            
            # Add power-ups
            self.power_ups.append(PowerUp(300, 350, "energy"))
            self.power_ups.append(PowerUp(600, 250, "gravity"))
            
            # Add gravity wells (one pulling, one pushing)
            self.gravity_wells.append(GravityWell(500, 400, 120, 0.15))  # Pulling
            self.gravity_wells.append(GravityWell(250, 200, 100, -0.1))  # Pushing
            
            # Add teleporters (pair 1)
            self.teleporters.append(Teleporter(150, 150, 1, True))
            self.teleporters.append(Teleporter(650, 400, 1, False))
            
        elif self.level_num == 4:
            # Level with multiple teleporter network
            # Add walls in a more complex pattern
            self.walls.append(Wall(200, 50, 20, 200))
            self.walls.append(Wall(200, 350, 20, 200))
            self.walls.append(Wall(400, 150, 20, 300))
            self.walls.append(Wall(600, 50, 20, 200))
            self.walls.append(Wall(600, 350, 20, 200))
            
            # Add a moving wall
            moving_wall = Wall(300, 300, 50, 20, True)
            moving_wall.move_path = [(300, 300), (500, 300)]
            moving_wall.move_speed = 0.01
            self.walls.append(moving_wall)
            
            # Add targets in hard to reach places
            self.targets.append(Target(300, 100))
            self.targets.append(Target(500, 100))
            self.targets.append(Target(700, 100))
            self.targets.append(Target(300, 500))
            self.targets.append(Target(500, 500))
            
            # Add an optional star target
            star_target = Target(550, 300, required=False)
            star_target.color = YELLOW
            self.targets.append(star_target)
            
            # Add surfaces
            self.surfaces.append(Surface(220, 250, 180, 100, "ice"))
            self.surfaces.append(Surface(420, 350, 180, 100, "mud"))
            self.surfaces.append(Surface(650, 250, 100, 100, "speed"))
            
            # Add power-ups
            self.power_ups.append(PowerUp(300, 300, "energy"))
            self.power_ups.append(PowerUp(500, 200, "shield"))
            self.power_ups.append(PowerUp(700, 400, "time"))
            
            # Add bounce pads
            self.bounce_pads.append(BouncePad(100, 400, 80, 20, (1, -1), 1.5))
            self.bounce_pads.append(BouncePad(300, 200, 20, 80, (1, 0), 1.8))
            
            # Add teleporter network
            # Pair 1: Main entrance to upper right
            self.teleporters.append(Teleporter(100, 300, 1, True))
            self.teleporters.append(Teleporter(650, 100, 1, False))
            
            # Pair 2: Upper middle to lower right
            self.teleporters.append(Teleporter(350, 100, 2, True))
            self.teleporters.append(Teleporter(650, 500, 2, False))
            
            # Pair 3: Lower left to upper left
            self.teleporters.append(Teleporter(350, 500, 3, True))
            self.teleporters.append(Teleporter(150, 100, 3, False))
            
            # Add gravity wells
            self.gravity_wells.append(GravityWell(500, 300, 100, 0.1))
            
        elif self.level_num == 5:
            # Level with special surfaces and magnets
            # Create a spiral wall pattern
            center_x, center_y = WIDTH // 2, HEIGHT // 2
            spiral_segments = 8
            segment_length = 150
            for i in range(spiral_segments):
                angle = i * math.pi / 2
                wall_length = segment_length * (1 + i * 0.3)
                end_x = center_x + math.cos(angle) * wall_length
                end_y = center_y + math.sin(angle) * wall_length
                wall_width = 20
                
                if i % 2 == 0:  # Horizontal walls
                    self.walls.append(Wall(
                        center_x - wall_width//2, 
                        end_y - wall_width//2, 
                        wall_length, 
                        wall_width
                    ))
                else:  # Vertical walls
                    self.walls.append(Wall(
                        end_x - wall_width//2, 
                        center_y - wall_width//2, 
                        wall_width, 
                        wall_length
                    ))
                    
            # Add targets along the spiral
            for i in range(spiral_segments):
                angle = i * math.pi / 2 + math.pi / 4
                distance = segment_length * (0.5 + i * 0.3)
                target_x = center_x + math.cos(angle) * distance
                target_y = center_y + math.sin(angle) * distance
                
                # Make the final target required, others optional
                if i == spiral_segments - 1:
                    self.targets.append(Target(target_x, target_y))
                else:
                    star_target = Target(target_x, target_y, required=False)
                    star_target.color = YELLOW
                    self.targets.append(star_target)
            
            # Add different surface types in sections
            self.surfaces.append(Surface(100, 100, 200, 200, "ice"))
            self.surfaces.append(Surface(500, 100, 200, 200, "mud"))
            self.surfaces.append(Surface(500, 400, 200, 150, "speed"))
            self.surfaces.append(Surface(100, 400, 200, 150, "bouncy"))
            
            # Add power-ups
            self.power_ups.append(PowerUp(200, 200, "energy"))
            self.power_ups.append(PowerUp(600, 200, "shield"))
            self.power_ups.append(PowerUp(200, 450, "magnet"))
            self.power_ups.append(PowerUp(600, 450, "time"))
            
            # Add a moving wall
            moving_wall = Wall(center_x - 100, center_y - 10, 200, 20, True)
            moving_wall.move_path = [(center_x - 100, center_y - 10), 
                                    (center_x - 100, center_y + 100), 
                                    (center_x + 100, center_y + 100),
                                    (center_x + 100, center_y - 10)]
            moving_wall.move_speed = 0.005
            self.walls.append(moving_wall)
            
            # Add bounce pads
            self.bounce_pads.append(BouncePad(50, 300, 100, 20, (1, -0.5), 1.8))
            self.bounce_pads.append(BouncePad(WIDTH - 150, 300, 100, 20, (-1, -0.5), 1.8))
            
        else:
            # Procedurally generated levels for higher levels
            self.generate_procedural_level()
    
    def generate_procedural_level(self):
        """Generate a procedural level based on level number"""
        # Determine complexity based on level number
        num_walls = 3 + min(12, self.level_num)
        num_surfaces = 2 + min(4, self.level_num // 2)
        num_targets = 3 + min(8, self.level_num // 2)
        num_power_ups = min(5, 2 + self.level_num // 3)
        num_gravity_wells = min(4, self.level_num // 2)
        num_teleporter_pairs = min(3, self.level_num // 3)
        num_bounce_pads = min(4, self.level_num // 3)
        num_moving_walls = min(3, self.level_num // 4)
        num_stars = min(3, 1 + self.level_num // 5)  # Optional targets
        
        # Generate walls - mix of random and structured
        if random.random() < 0.7:  # 70% chance for structured walls
            # Create a room-like structure
            self.generate_room_structure()
        else:
            # Random walls
            for _ in range(num_walls - num_moving_walls):
                for attempt in range(20):
                    w_width = random.randint(20, 180)
                    w_height = random.randint(20, 180)
                    
                    # Bias toward horizontal or vertical walls
                    if random.random() < 0.7:
                        if random.random() < 0.5:
                            w_width = max(100, w_width)
                            w_height = 20
                        else:
                            w_width = 20
                            w_height = max(100, w_height)
                    
                    wx = random.randint(50, WIDTH - w_width - 50)
                    wy = random.randint(50, HEIGHT - w_height - 50)
                    
                    # Check if wall position is valid
                    valid_pos = True
                    for wall in self.walls[4:]:  # Skip outer walls
                        if (abs(wx - wall.x) < 40 and abs(wy - wall.y) < 40) or \
                           (abs(wx + w_width - wall.x - wall.width) < 40 and 
                            abs(wy + w_height - wall.y - wall.height) < 40):
                            valid_pos = False
                            break
                    
                    if valid_pos:
                        self.walls.append(Wall(wx, wy, w_width, w_height))
                        break
        
        # Add moving walls
        for _ in range(num_moving_walls):
            w_width = random.randint(40, 100)
            w_height = random.randint(20, 40)
            
            # Try to find valid position
            for attempt in range(20):
                wx = random.randint(100, WIDTH - w_width - 100)
                wy = random.randint(100, HEIGHT - w_height - 100)
                
                if self.is_position_valid(wx + w_width//2, wy + w_height//2, 
                                         max(w_width, w_height) // 2):
                    # Create moving wall
                    moving_wall = Wall(wx, wy, w_width, w_height, True)
                    
                    # Create movement path
                    path_type = random.choice(["linear", "rectangular", "circular"])
                    
                    if path_type == "linear":
                        # Simple back and forth
                        direction = random.choice(["horizontal", "vertical"])
                        distance = random.randint(100, 200)
                        
                        if direction == "horizontal":
                            moving_wall.move_path = [
                                (wx, wy),
                                (wx + distance, wy)
                            ]
                        else:
                            moving_wall.move_path = [
                                (wx, wy),
                                (wx, wy + distance)
                            ]
                            
                    elif path_type == "rectangular":
                        # Rectangular path
                        width = random.randint(100, 200)
                        height = random.randint(100, 200)
                        
                        moving_wall.move_path = [
                            (wx, wy),
                            (wx + width, wy),
                            (wx + width, wy + height),
                            (wx, wy + height)
                        ]
                        
                    else:  # circular
                        # Circular path
                        radius = random.randint(50, 100)
                        center_x = wx + radius
                        center_y = wy + radius
                        
                        # Create circular path with 8 points
                        path = []
                        for i in range(8):
                            angle = i * math.pi / 4
                            point_x = center_x + math.cos(angle) * radius
                            point_y = center_y + math.sin(angle) * radius
                            path.append((point_x, point_y))
                            
                        moving_wall.move_path = path
                    
                    # Set random speed
                    moving_wall.move_speed = random.uniform(0.005, 0.015)
                    self.walls.append(moving_wall)
                    break
        
        # Add surfaces
        surface_types = list(SURFACES.keys())
        for _ in range(num_surfaces):
            for attempt in range(20):
                s_width = random.randint(100, 250)
                s_height = random.randint(100, 250)
                sx = random.randint(50, WIDTH - s_width - 50)
                sy = random.randint(50, HEIGHT - s_height - 50)
                
                if self.is_position_valid(sx + s_width//2, sy + s_height//2, 
                                        max(s_width, s_height) // 2, 
                                        check_objects=False):
                    s_type = random.choice(surface_types)
                    self.surfaces.append(Surface(sx, sy, s_width, s_height, s_type))
                    break
        
        # Add required targets
        for _ in range(num_targets - num_stars):
            for attempt in range(30):
                tx, ty = self.get_valid_position(20)
                if self.is_position_valid(tx, ty, 20):
                    self.targets.append(Target(tx, ty))
                    break
        
        # Add optional star targets
        for _ in range(num_stars):
            for attempt in range(30):
                tx, ty = self.get_valid_position(20)
                if self.is_position_valid(tx, ty, 20):
                    star_target = Target(tx, ty, required=False)
                    star_target.color = YELLOW
                    self.targets.append(star_target)
                    break
        
        # Add power-ups
        power_up_types = ["energy", "speed", "gravity", "shield", "time", "magnet"]
        for _ in range(num_power_ups):
            for attempt in range(20):
                px, ty = self.get_valid_position(15)
                if self.is_position_valid(px, ty, 15):
                    power_type = random.choice(power_up_types)
                    self.power_ups.append(PowerUp(px, ty, power_type))
                    break
        
        # Add gravity wells
        for _ in range(num_gravity_wells):
            for attempt in range(20):
                gx, gy = self.get_valid_position(50)
                if self.is_position_valid(gx, gy, 50):
                    strength = random.choice([0.1, 0.15, 0.2, -0.1, -0.15, -0.2])
                    radius = random.randint(80, 150)
                    self.gravity_wells.append(GravityWell(gx, gy, radius, strength))
                    break
        
        # Add teleporter pairs
        for pair_id in range(1, num_teleporter_pairs + 1):
            for attempt in range(20):
                # Add entrance
                tx1, ty1 = self.get_valid_position(25)
                if self.is_position_valid(tx1, ty1, 25):
                    self.teleporters.append(Teleporter(tx1, ty1, pair_id, True))
                    
                    # Add exit - ensure it's in a different area
                    for exit_attempt in range(30):
                        tx2, ty2 = self.get_valid_position(25)
                        
                        # Make sure exit is far enough from entrance
                        if (distance(tx1, ty1, tx2, ty2) > 200 and 
                            self.is_position_valid(tx2, ty2, 25)):
                            self.teleporters.append(Teleporter(tx2, ty2, pair_id, False))
                            break
                    break
        
        # Add bounce pads
        for _ in range(num_bounce_pads):
            for attempt in range(20):
                pad_width = random.randint(60, 100)
                pad_height = random.randint(20, 30)
                
                # Decide orientation (horizontal or vertical)
                if random.random() < 0.5:
                    pad_width, pad_height = pad_height, pad_width
                
                px = random.randint(50, WIDTH - pad_width - 50)
                py = random.randint(50, HEIGHT - pad_height - 50)
                
                if self.is_position_valid(px + pad_width//2, py + pad_height//2, 
                                        max(pad_width, pad_height) // 2):
                    # Determine bounce direction
                    if pad_width > pad_height:  # Horizontal pad
                        if py < HEIGHT // 2:
                            direction = (0, 1)  # Down
                        else:
                            direction = (0, -1)  # Up
                    else:  # Vertical pad
                        if px < WIDTH // 2:
                            direction = (1, 0)  # Right
                        else:
                            direction = (-1, 0)  # Left
                    
                    # Add some randomness
                    dir_x = direction[0] + random.uniform(-0.3, 0.3)
                    dir_y = direction[1] + random.uniform(-0.3, 0.3)
                    direction = normalize_vector(dir_x, dir_y)
                    
                    strength = random.uniform(1.3, 2.0)
                    self.bounce_pads.append(BouncePad(px, py, pad_width, pad_height, 
                                                    direction, strength))
                    break
    
    def generate_room_structure(self):
        """Generate a room-like structure for the level"""
        room_patterns = [
            "grid",      # Grid of rooms
            "hub",       # Central hub with connected rooms
            "corridor",  # Long corridor with rooms
            "maze"       # Maze-like structure
        ]
        
        pattern = random.choice(room_patterns)
        
        if pattern == "grid":
            # Create a grid of rooms
            grid_size = random.randint(2, 3)
            room_width = (WIDTH - 100) // grid_size
            room_height = (HEIGHT - 100) // grid_size
            
            # Create horizontal walls
            for row in range(grid_size + 1):
                y = 50 + row * room_height
                # Add gaps for doors
                segments = random.randint(1, 3)
                segment_width = room_width * grid_size / segments
                
                for seg in range(segments):
                    door_pos = random.uniform(0.3, 0.7)
                    start_x = 50 + seg * segment_width
                    door_x = start_x + segment_width * door_pos
                    
                    # Before door
                    if door_x - start_x > 50:
                        self.walls.append(Wall(
                            start_x, y - 10, door_x - start_x - 20, 20
                        ))
                    
                    # After door
                    if start_x + segment_width - door_x > 50:
                        self.walls.append(Wall(
                            door_x + 20, y - 10, 
                            start_x + segment_width - door_x - 20, 20
                        ))
            
            # Create vertical walls
            for col in range(grid_size + 1):
                x = 50 + col * room_width
                # Add gaps for doors
                segments = random.randint(1, 3)
                segment_height = room_height * grid_size / segments
                
                for seg in range(segments):
                    door_pos = random.uniform(0.3, 0.7)
                    start_y = 50 + seg * segment_height
                    door_y = start_y + segment_height * door_pos
                    
                    # Before door
                    if door_y - start_y > 50:
                        self.walls.append(Wall(
                            x - 10, start_y, 20, door_y - start_y - 20
                        ))
                    
                    # After door
                    if start_y + segment_height - door_y > 50:
                        self.walls.append(Wall(
                            x - 10, door_y + 20, 
                            20, start_y + segment_height - door_y - 20
                        ))
                        
        elif pattern == "hub":
            # Central hub with connected rooms
            hub_x = WIDTH // 2
            hub_y = HEIGHT // 2
            hub_size = random.randint(100, 150)
            
            # Create central hub
            self.walls.append(Wall(hub_x - hub_size, hub_y - hub_size, hub_size * 2, 20))  # Top
            self.walls.append(Wall(hub_x - hub_size, hub_y + hub_size - 20, hub_size * 2, 20))  # Bottom
            self.walls.append(Wall(hub_x - hub_size, hub_y - hub_size, 20, hub_size * 2))  # Left
            self.walls.append(Wall(hub_x + hub_size - 20, hub_y - hub_size, 20, hub_size * 2))  # Right
            
            # Create connected rooms
            num_rooms = random.randint(3, 5)
            for i in range(num_rooms):
                angle = i * (2 * math.pi / num_rooms)
                distance = hub_size + random.randint(50, 100)
                room_size = random.randint(80, 120)
                
                room_x = hub_x + math.cos(angle) * distance - room_size // 2
                room_y = hub_y + math.sin(angle) * distance - room_size // 2
                
                # Create room walls
                self.walls.append(Wall(room_x, room_y, room_size, 20))  # Top
                self.walls.append(Wall(room_x, room_y + room_size - 20, room_size, 20))  # Bottom
                self.walls.append(Wall(room_x, room_y, 20, room_size))  # Left
                self.walls.append(Wall(room_x + room_size - 20, room_y, 20, room_size))  # Right
                
                # Create corridor to hub
                corridor_width = 40
                corridor_length = distance - hub_size - room_size // 2
                
                # Calculate corridor position and dimensions
                if abs(math.cos(angle)) > abs(math.sin(angle)):
                    # Horizontal corridor
                    if math.cos(angle) > 0:  # Right
                        cor_x = hub_x + hub_size
                        cor_y = hub_y - corridor_width // 2 + math.sin(angle) * hub_size
                        cor_width = corridor_length
                        cor_height = corridor_width
                    else:  # Left
                        cor_x = room_x + room_size
                        cor_y = hub_y - corridor_width // 2 + math.sin(angle) * hub_size
                        cor_width = corridor_length
                        cor_height = corridor_width
                else:
                    # Vertical corridor
                    if math.sin(angle) > 0:  # Down
                        cor_x = hub_x - corridor_width // 2 + math.cos(angle) * hub_size
                        cor_y = hub_y + hub_size
                        cor_width = corridor_width
                        cor_height = corridor_length
                    else:  # Up
                        cor_x = hub_x - corridor_width // 2 + math.cos(angle) * hub_size
                        cor_y = room_y + room_size
                        cor_width = corridor_width
                        cor_height = corridor_length
                
                # Add corridor walls
                if cor_width > cor_height:  # Horizontal corridor
                    self.walls.append(Wall(cor_x, cor_y, cor_width, 20))  # Top
                    self.walls.append(Wall(cor_x, cor_y + cor_height - 20, cor_width, 20))  # Bottom
                else:  # Vertical corridor
                    self.walls.append(Wall(cor_x, cor_y, 20, cor_height))  # Left
                    self.walls.append(Wall(cor_x + cor_width - 20, cor_y, 20, cor_height))  # Right
                    
        elif pattern == "corridor":
            # Long corridor with rooms
            corridor_width = random.randint(80, 120)
            
            # Decide orientation
            if random.random() < 0.5:
                # Horizontal corridor
                corridor_y = HEIGHT // 2 - corridor_width // 2
                
                # Corridor walls
                self.walls.append(Wall(50, corridor_y, WIDTH - 100, 20))  # Top
                self.walls.append(Wall(50, corridor_y + corridor_width, WIDTH - 100, 20))  # Bottom
                
                # Create rooms off the corridor
                num_rooms = random.randint(2, 4)
                for _ in range(num_rooms):
                    # Decide if room is above or below corridor
                    if random.random() < 0.5:
                        # Room above
                        room_x = random.randint(100, WIDTH - 200)
                        room_y = corridor_y - random.randint(100, 150)
                        room_width = random.randint(100, 150)
                        room_height = corridor_y - room_y
                    else:
                        # Room below
                        room_x = random.randint(100, WIDTH - 200)
                        room_y = corridor_y + corridor_width
                        room_width = random.randint(100, 150)
                        room_height = random.randint(100, 150)
                    
                    # Create room walls
                    if room_y < corridor_y:  # Above
                        self.walls.append(Wall(room_x, room_y, room_width, 20))  # Top
                        # Skip bottom (connects to corridor)
                        self.walls.append(Wall(room_x, room_y, 20, room_height))  # Left
                        self.walls.append(Wall(room_x + room_width - 20, room_y, 20, room_height))  # Right
                    else:  # Below
                        # Skip top (connects to corridor)
                        self.walls.append(Wall(room_x, room_y + room_height - 20, room_width, 20))  # Bottom
                        self.walls.append(Wall(room_x, room_y, 20, room_height))  # Left
                        self.walls.append(Wall(room_x + room_width - 20, room_y, 20, room_height))  # Right
                    
                    # Create door
                    door_width = 40
                    door_x = room_x + (room_width - door_width) // 2
                    
                    if room_y < corridor_y:  # Above
                        # Remove part of corridor top wall
                        for wall in self.walls:
                            if wall.y == corridor_y and wall.x <= door_x <= wall.x + wall.width:
                                # Split wall if door is in the middle
                                if door_x > wall.x + 20 and door_x + door_width < wall.x + wall.width - 20:
                                    # Create two walls on either side of the door
                                    self.walls.append(Wall(wall.x, wall.y, door_x - wall.x, 20))
                                    self.walls.append(Wall(door_x + door_width, wall.y, 
                                                          wall.x + wall.width - door_x - door_width, 20))
                                    self.walls.remove(wall)
                                break
                    else:  # Below
                        # Remove part of corridor bottom wall
                        for wall in self.walls:
                            if wall.y == corridor_y + corridor_width and wall.x <= door_x <= wall.x + wall.width:
                                # Split wall if door is in the middle
                                if door_x > wall.x + 20 and door_x + door_width < wall.x + wall.width - 20:
                                    # Create two walls on either side of the door
                                    self.walls.append(Wall(wall.x, wall.y, door_x - wall.x, 20))
                                    self.walls.append(Wall(door_x + door_width, wall.y, 
                                                          wall.x + wall.width - door_x - door_width, 20))
                                    self.walls.remove(wall)
                                break
            else:
                # Vertical corridor
                corridor_x = WIDTH // 2 - corridor_width // 2
                
                # Corridor walls
                self.walls.append(Wall(corridor_x, 50, 20, HEIGHT - 100))  # Left
                self.walls.append(Wall(corridor_x + corridor_width, 50, 20, HEIGHT - 100))  # Right
                
                # Create rooms off the corridor
                num_rooms = random.randint(2, 4)
                for _ in range(num_rooms):
                    # Decide if room is to left or right of corridor
                    if random.random() < 0.5:
                        # Room to left
                        room_y = random.randint(100, HEIGHT - 200)
                        room_x = corridor_x - random.randint(100, 150)
                        room_height = random.randint(100, 150)
                        room_width = corridor_x - room_x
                    else:
                        # Room to right
                        room_y = random.randint(100, HEIGHT - 200)
                        room_x = corridor_x + corridor_width
                        room_height = random.randint(100, 150)
                        room_width = random.randint(100, 150)
                    
                    # Create room walls
                    self.walls.append(Wall(room_x, room_y, room_width, 20))  # Top
                    self.walls.append(Wall(room_x, room_y + room_height - 20, room_width, 20))  # Bottom
                    
                    if room_x < corridor_x:  # Left
                        self.walls.append(Wall(room_x, room_y, 20, room_height))  # Left
                        # Skip right (connects to corridor)
                    else:  # Right
                        # Skip left (connects to corridor)
                        self.walls.append(Wall(room_x + room_width - 20, room_y, 20, room_height))  # Right
                    
                    # Create door
                    door_height = 40
                    door_y = room_y + (room_height - door_height) // 2
                    
                    if room_x < corridor_x:  # Left
                        # Remove part of corridor left wall
                        for wall in self.walls:
                            if wall.x == corridor_x and wall.y <= door_y <= wall.y + wall.height:
                                # Split wall if door is in the middle
                                if door_y > wall.y + 20 and door_y + door_height < wall.y + wall.height - 20:
                                    # Create two walls above and below the door
                                    self.walls.append(Wall(wall.x, wall.y, 20, door_y - wall.y))
                                    self.walls.append(Wall(wall.x, door_y + door_height, 
                                                         20, wall.y + wall.height - door_y - door_height))
                                    self.walls.remove(wall)
                                break
                    else:  # Right
                        # Remove part of corridor right wall
                        for wall in self.walls:
                            if wall.x == corridor_x + corridor_width and wall.y <= door_y <= wall.y + wall.height:
                                # Split wall if door is in the middle
                                if door_y > wall.y + 20 and door_y + door_height < wall.y + wall.height - 20:
                                    # Create two walls above and below the door
                                    self.walls.append(Wall(wall.x, wall.y, 20, door_y - wall.y))
                                    self.walls.append(Wall(wall.x, door_y + door_height, 
                                                         20, wall.y + wall.height - door_y - door_height))
                                    self.walls.remove(wall)
                                break
                                
        else:  # maze
            # Create a simple random maze
            grid_size = random.randint(3, 4)
            cell_width = (WIDTH - 100) // grid_size
            cell_height = (HEIGHT - 100) // grid_size
            
            # Create grid of walls
            for row in range(grid_size + 1):
                for col in range(grid_size + 1):
                    x = 50 + col * cell_width
                    y = 50 + row * cell_height
                    
                    # Probabilistic wall placement
                    if col < grid_size and random.random() < 0.7:
                        # Horizontal wall with gap
                        gap_pos = random.randint(0, cell_width - 40)
                        
                        if gap_pos > 20:
                            self.walls.append(Wall(x, y, gap_pos, 20))
                        
                        if gap_pos + 40 < cell_width:
                            self.walls.append(Wall(x + gap_pos + 40, y, 
                                                cell_width - gap_pos - 40, 20))
                    
                    if row < grid_size and random.random() < 0.7:
                        # Vertical wall with gap
                        gap_pos = random.randint(0, cell_height - 40)
                        
                        if gap_pos > 20:
                            self.walls.append(Wall(x, y, 20, gap_pos))
                        
                        if gap_pos + 40 < cell_height:
                            self.walls.append(Wall(x, y + gap_pos + 40, 
                                                20, cell_height - gap_pos - 40))
    
    def handle_input(self, keys):
        """Handle keyboard input"""
        # Only handle input in playing state
        if self.state != GameState.PLAYING:
            return
            
        # Calculate force to apply
        force_x, force_y = 0, 0
        
        controls = self.settings["controls"]
        
        if keys[controls["left"]]:
            force_x -= self.force_multiplier
        if keys[controls["right"]]:
            force_x += self.force_multiplier
        if keys[controls["up"]]:
            force_y -= self.force_multiplier
        if keys[controls["down"]]:
            force_y += self.force_multiplier
            
        # Apply force if energy available
        if (force_x != 0 or force_y != 0) and self.energy > 0:
            # Normalize diagonal movement
            if force_x != 0 and force_y != 0:
                normalized_x, normalized_y = normalize_vector(force_x, force_y)
                force_x = normalized_x * self.force_multiplier
                force_y = normalized_y * self.force_multiplier
            
            # Calculate energy cost based on force magnitude
            force_magnitude = math.sqrt(force_x**2 + force_y**2)
            energy_cost = force_magnitude * FORCE_COST
            
            if energy_cost <= self.energy:
                self.ball.apply_force(force_x, force_y)
                self.energy -= energy_cost
                
                # Add force indicator particles
                speed = math.sqrt(force_x**2 + force_y**2)
                if self.settings["particles"] and random.random() < 0.3:
                    self.particle_system.add_trail(
                        self.ball.x, self.ball.y,
                        (255, 255, 255, 100),
                        -force_x / speed if speed > 0 else 0,
                        -force_y / speed if speed > 0 else 0,
                        particle_count=5,
                        life_range=(0.2, 0.5)
                    )
            else:
                # Apply reduced force with remaining energy
                ratio = self.energy / energy_cost
                self.ball.apply_force(force_x * ratio, force_y * ratio)
                self.energy = 0
                
                # Play energy low warning
                if random.random() < 0.1:
                    play_sound("energy_low", 0.3)
    
    def update(self, dt):
        """Update game state"""
        # Store dt value for time dilation effects
        self.dt = dt
        
        # Apply time dilation if active
        if self.time_dilated:
            dt *= self.time_factor
        
        # Update toasts
        for toast in self.toasts:
            toast.update()
        self.toasts = [t for t in self.toasts if t.active]
        
        # Update based on current state
        if self.state == GameState.PLAYING:
            self.update_game(dt)
        elif self.state == GameState.MAIN_MENU:
            self.update_main_menu(dt)
        elif self.state == GameState.LEVEL_SELECT:
            self.update_level_select(dt)
        elif self.state == GameState.LEVEL_COMPLETE:
            self.update_level_complete(dt)
        elif self.state == GameState.PAUSED:
            # Don't update game when paused
            pass
        elif self.state == GameState.SETTINGS:
            self.update_settings(dt)
        
        # Always update particle system
        self.particle_system.update(dt)
        
        # Update screen shake
        if self.screen_shake > 0:
            self.screen_shake -= dt * 60
            if self.screen_shake < 0:
                self.screen_shake = 0
                
        # Update transition alpha
        if self.transition_alpha > 0:
            self.transition_alpha -= dt * 500  # Fade out
            if self.transition_alpha < 0:
                self.transition_alpha = 0
    
    def update_game(self, dt):
        """Update gameplay state"""
        # Update level time
        self.level_time = time.time() - self.level_start_time
        
        # Energy regeneration
        self.energy = min(ENERGY_MAX, self.energy + ENERGY_REGEN * dt * 60)
        
        # Default friction
        friction = FRICTION
        
        # Flag for ball on special surface
        on_special_surface = False
        
        # Update game objects
        for wall in self.walls:
            wall.update(dt)
            
        for surface in self.surfaces:
            surface.update(dt)
            
        for target in self.targets:
            target.update(dt)
            
        for power_up in self.power_ups:
            power_up.update(dt)
            
        for gravity_well in self.gravity_wells:
            gravity_well.update(dt)
            
        for teleporter in self.teleporters:
            teleporter.update(dt)
            
        for bounce_pad in self.bounce_pads:
            bounce_pad.update(dt)
        
        # Check if any power-ups are active and apply their effects
        for power_up in list(self.active_power_ups):
            # Apply effects of active power-ups
            if power_up.apply_effect(self):
                # Handle specific power-up effects
                if power_up.type == "speed" and power_up.is_effect_active():
                    # Speed boost reduces friction by 50%
                    friction *= 0.5
                    
                    # Add trail particles
                    if self.settings["particles"] and (abs(self.ball.vel_x) > 0.5 or abs(self.ball.vel_y) > 0.5):
                        speed = math.sqrt(self.ball.vel_x**2 + self.ball.vel_y**2)
                        if random.random() < 0.3 * dt * 60:
                            self.particle_system.add_trail(
                                self.ball.x, self.ball.y,
                                (0, 191, 255, 150),  # Blue with transparency
                                self.ball.vel_x / speed if speed > 0 else 0,
                                self.ball.vel_y / speed if speed > 0 else 0
                            )
                            
                elif power_up.type == "shield" and power_up.is_effect_active():
                    # Shield effect
                    self.ball.has_shield = True
                    
                elif power_up.type == "gravity" and power_up.is_effect_active():
                    # Gravity field effect
                    self.gravity_field_active = True
                    
                elif power_up.type == "time" and power_up.is_effect_active():
                    # Time dilation effect
                    self.time_dilated = True
                    self.time_factor = 0.5  # 50% slower
                    
                elif power_up.type == "magnet" and power_up.is_effect_active():
                    # Magnet effect
                    self.magnet_active = True
                    self.magnet_strength = 0.1
                    self.magnet_radius = 200
            else:
                # Effect has expired
                if power_up.type == "shield":
                    self.ball.has_shield = False
                elif power_up.type == "gravity":
                    self.gravity_field_active = False
                    self.gravity_field_strength = 0
                elif power_up.type == "time":
                    self.time_dilated = False
                    self.time_factor = 1.0
                elif power_up.type == "magnet":
                    self.magnet_active = False
                    self.magnet_strength = 0
                
                # Remove from active power-ups
                if power_up in self.active_power_ups:
                    self.active_power_ups.remove(power_up)
        
        # Apply player-controlled gravity field if active
        if self.gravity_field_active and self.gravity_field_strength != 0:
            # Apply gravity to all objects within radius
            for target in self.targets:
                if target.active:
                    dx = self.ball.x - target.x
                    dy = self.ball.y - target.y
                    dist = math.sqrt(dx*dx + dy*dy)
                    
                    if dist < self.gravity_field_radius and dist > 0:
                        force = self.gravity_field_strength / (dist * dist)
                        # Move the target toward or away from the player
                        target.x += dx/dist * force * 2 * dt * 60
                        target.y += dy/dist * force * 2 * dt * 60
                        
                        # Add occasional gravity field particles
                        if self.settings["particles"] and random.random() < 0.1 * dt * 60:
                            if self.gravity_field_strength > 0:  # Pulling
                                particle_color = (148, 0, 211, 120)  # Purple with transparency
                                # Particles move from target towards ball
                                self.particle_system.add_particle(
                                    target.x, target.y,
                                    particle_color,
                                    dx/dist * random.uniform(0.5, 1.5),
                                    dy/dist * random.uniform(0.5, 1.5),
                                    random.uniform(1, 3),
                                    random.uniform(0.2, 0.5)
                                )
                            else:  # Pushing
                                particle_color = (0, 191, 255, 120)  # Blue with transparency
                                # Particles move away from ball towards target
                                self.particle_system.add_particle(
                                    self.ball.x, self.ball.y,
                                    particle_color,
                                    -dx/dist * random.uniform(0.5, 1.5),
                                    -dy/dist * random.uniform(0.5, 1.5),
                                    random.uniform(1, 3),
                                    random.uniform(0.2, 0.5)
                                )
        
        # Apply magnet effect if active
        if self.magnet_active:
            # Attract targets to the ball
            for target in self.targets:
                if target.active:
                    dx = self.ball.x - target.x
                    dy = self.ball.y - target.y
                    dist = math.sqrt(dx*dx + dy*dy)
                    
                    if dist < self.magnet_radius and dist > self.ball.radius + target.radius:
                        # Calculate force (stronger at medium distance)
                        distance_factor = 1 - abs(dist / self.magnet_radius - 0.5) * 2
                        force = self.magnet_strength * distance_factor
                        
                        # Move the target toward the player
                        target.x += dx/dist * force * dt * 60
                        target.y += dy/dist * force * dt * 60
                        
                        # Add magnet particles
                        if self.settings["particles"] and random.random() < 0.05 * dt * 60:
                            particle_color = (255, 69, 0, 120)  # Orange with transparency
                            self.particle_system.add_particle(
                                target.x, target.y,
                                particle_color,
                                dx/dist * random.uniform(0.3, 1.0),
                                dy/dist * random.uniform(0.3, 1.0),
                                random.uniform(1, 2),
                                random.uniform(0.3, 0.7)
                            )
        
        # Check if ball is on any special surface
        for surface in self.surfaces:
            if surface.is_ball_on_surface(self.ball):
                friction = surface.friction
                on_special_surface = True
                
                # Apply special surface effect
                surface.apply_effect(self.ball)
                
                # Add surface-specific particle effects
                if self.settings["particles"] and random.random() < 0.1 * dt * 60:
                    surface.add_particle(self.ball.x, self.ball.y, 
                                        self.ball.vel_x, self.ball.vel_y)
        
        # Update ball position with appropriate friction
        self.ball.update(dt, friction)
        
        # Apply forces from gravity wells
        for well in self.gravity_wells:
            well.apply_force(self.ball)
        
        # Check bounce pad collisions
        for pad in self.bounce_pads:
            if pad.check_collision(self.ball):
                # Add screen shake
                if self.settings["screen_shake"]:
                    self.screen_shake = 5
                
                # Play bounce sound
                play_sound("bounce", 0.6)
        
        # Check teleporter collisions
        for teleporter in self.teleporters:
            if teleporter.check_collision(self.ball):
                # Find the exit teleporter with the same pair_id
                exit_teleporter = None
                for t in self.teleporters:
                    if t.pair_id == teleporter.pair_id and t != teleporter:
                        exit_teleporter = t
                        break
                
                if exit_teleporter:
                    # Teleport the ball and preserve momentum
                    self.ball.x = exit_teleporter.x
                    self.ball.y = exit_teleporter.y
                    
                    # Add particle effects at both teleporters
                    teleporter.activate()
                    exit_teleporter.activate()
                    
                    # Add screen shake
                    if self.settings["screen_shake"]:
                        self.screen_shake = 5
                    
                    # Play teleport sound
                    play_sound("teleport", 0.7)
                    
                    break  # Only teleport once
        
        # Check wall collisions
        for wall in self.walls:
            collision = wall.check_collision(self.ball)
            if collision:
                # Add screen shake if fast impact
                speed = math.sqrt(self.ball.vel_x**2 + self.ball.vel_y**2)
                if self.settings["screen_shake"] and speed > 5:
                    self.screen_shake = min(10, speed * 0.5)
                
                # Play collision sound
                play_sound("collision", min(1.0, speed * 0.1))
                
                # If shield is active, prevent the bounce effect
                if self.ball.has_shield:
                    self.ball.has_shield = False
                    # Find the power-up that provided the shield and deactivate it
                    for power_up in self.active_power_ups:
                        if power_up.type == "shield":
                            power_up.collected = False
                            self.active_power_ups.remove(power_up)
                            break
                    
                    # Play shield break sound
                    play_sound("shield_break", 0.8)
                    
                    # Add special shield break particles
                    if self.settings["particles"]:
                        self.particle_system.add_explosion(
                            self.ball.x, self.ball.y,
                            (220, 220, 220),  # Silver/white
                            particle_count=40,
                            speed_range=(2, 5),
                            life_range=(0.5, 1.0)
                        )
            
        # Check power-up collisions
        for power_up in self.power_ups:
            if power_up.check_collision(self.ball):
                self.active_power_ups.append(power_up)
                self.score += 50  # Bonus points for collecting power-up
                
                # Play power-up sound
                play_sound("powerup", 0.8)
                
                # Add toast notification
                if power_up.type == "energy":
                    self.add_toast("Energy Refill!", 1.5, power_up.color)
                elif power_up.type == "speed":
                    self.add_toast("Speed Boost!", 1.5, power_up.color)
                elif power_up.type == "gravity":
                    self.add_toast("Gravity Field! Press G to toggle", 2.0, power_up.color)
                elif power_up.type == "shield":
                    self.add_toast("Shield Activated!", 1.5, power_up.color)
                elif power_up.type == "time":
                    self.add_toast("Time Slow!", 1.5, power_up.color)
                elif power_up.type == "magnet":
                    self.add_toast("Target Magnet!", 1.5, power_up.color)
                
                # Add particle effect for power-up collection
                if self.settings["particles"]:
                    self.particle_system.add_explosion(
                        power_up.x, power_up.y, 
                        power_up.color, 
                        particle_count=30, 
                        size_range=(2, 8), 
                        speed_range=(1, 4), 
                        life_range=(0.5, 1.5)
                    )
        
        # Check target collisions
        required_targets_active = 0
        optional_targets_active = 0
        
        for target in self.targets:
            if target.check_collision(self.ball):
                self.score += 100  # Base points for any target
                
                if not target.required:
                    # Star target collected
                    self.stars_collected += 1
                    self.score += 150  # Extra points for star targets
                    play_sound("star", 1.0)
                    self.add_toast("Star Collected!", 1.5, YELLOW)
                else:
                    # Regular target
                    play_sound("powerup", 0.8)
                
                # Add particle effect for target collection
                if self.settings["particles"]:
                    self.particle_system.add_explosion(
                        target.x, target.y,
                        target.color,
                        particle_count=40,
                        speed_range=(2, 5),
                        life_range=(0.5, 1.5)
                    )
            
            # Count active targets
            if target.active:
                if target.required:
                    required_targets_active += 1
                else:
                    optional_targets_active += 1
        
        # Check level completion - only required targets need to be collected
        if required_targets_active == 0:
            self.level_complete_stars = self.stars_collected
            self.update_highscores()
            self.set_state(GameState.LEVEL_COMPLETE)
        
        # Ensure ball stays within bounds
        if self.ball.x < 20 + self.ball.radius:
            self.ball.x = 20 + self.ball.radius
            self.ball.vel_x = abs(self.ball.vel_x) * 0.5  # Bounce with energy loss
        elif self.ball.x > WIDTH - 20 - self.ball.radius:
            self.ball.x = WIDTH - 20 - self.ball.radius
            self.ball.vel_x = -abs(self.ball.vel_x) * 0.5  # Bounce with energy loss
            
        if self.ball.y < 20 + self.ball.radius:
            self.ball.y = 20 + self.ball.radius
            self.ball.vel_y = abs(self.ball.vel_y) * 0.5  # Bounce with energy loss
        elif self.ball.y > HEIGHT - 20 - self.ball.radius:
            self.ball.y = HEIGHT - 20 - self.ball.radius
            self.ball.vel_y = -abs(self.ball.vel_y) * 0.5  # Bounce with energy loss
    
    def update_main_menu(self, dt):
        """Update main menu state"""
        # Generate random background particles
        if self.settings["particles"] and random.random() < 0.1:
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            color = (
                random.randint(50, 200),
                random.randint(50, 200),
                random.randint(200, 255)
            )
            vel_x = random.uniform(-0.5, 0.5)
            vel_y = random.uniform(-0.5, 0.5)
            
            self.particle_system.add_particle(
                x, y, vel_x, vel_y, color, 
                random.uniform(2, 5), 
                random.uniform(1, 3)
            )
    
    def update_level_select(self, dt):
        """Update level select state"""
        pass
    
    def update_level_complete(self, dt):
        """Update level complete state"""
        # Generate celebration particles
        if self.settings["particles"] and random.random() < 0.2:
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            color = (
                random.randint(100, 255),
                random.randint(100, 255),
                random.randint(100, 255)
            )
            
            self.particle_system.add_explosion(
                x, y, color, 
                particle_count=10,
                speed_range=(1, 3),
                size_range=(2, 5),
                life_range=(0.5, 1.5)
            )
    
    def draw_game_over(self, surface):
        """Draw game over screen"""
        # First draw the game state behind
        self.draw_game(surface)
        
        # Add overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        # Draw game over text
        game_over_text = heading_font.render("GAME OVER", True, RED)
        game_over_rect = game_over_text.get_rect(center=(WIDTH//2, HEIGHT//3))
        surface.blit(game_over_text, game_over_rect)
        
        # Draw reason text
        if self.game_over_reason:
            reason_text = medium_font.render(self.game_over_reason, True, WHITE)
            reason_rect = reason_text.get_rect(center=(WIDTH//2, game_over_rect.bottom + 30))
            surface.blit(reason_text, reason_rect)
            
        # Draw buttons
        for button in self.menu_buttons["game_over"]:
            button.draw(surface)
    
    def draw_settings(self, surface):
        """Draw settings screen"""
        # Draw background
        self.draw_menu_background(surface)
        
        # Draw title with a decorative underline
        title_text = heading_font.render("SETTINGS", True, WHITE)
        title_rect = title_text.get_rect(center=(WIDTH//2, 70))
        surface.blit(title_text, title_rect)
        
        # Draw decorative underline
        underline_width = title_rect.width + 40
        pygame.draw.line(surface, CYAN, 
                        (WIDTH//2 - underline_width//2, title_rect.bottom + 10),
                        (WIDTH//2 + underline_width//2, title_rect.bottom + 10), 3)
        
        # Draw settings panel background
        panel_rect = pygame.Rect(WIDTH//2 - 200, title_rect.bottom + 30, 400, 350)
        pygame.draw.rect(surface, (40, 50, 60), panel_rect, border_radius=15)
        pygame.draw.rect(surface, (80, 100, 120), panel_rect, 2, border_radius=15)
        
        # Draw section title
        section_text = medium_font.render("Audio", True, CYAN)
        section_rect = section_text.get_rect(topleft=(panel_rect.left + 20, panel_rect.top + 20))
        surface.blit(section_text, section_rect)
        
        # Draw sliders
        for i, (key, slider) in enumerate(self.settings_sliders.items()):
            # Adjust slider position to be inside the panel
            slider.rect.x = panel_rect.left + 50
            slider.rect.y = section_rect.bottom + 20 + i * 70
            slider.draw(surface)
        
        # Draw section title for display settings
        display_text = medium_font.render("Display", True, CYAN)
        display_rect = display_text.get_rect(topleft=(panel_rect.left + 20, self.settings_sliders["sound_volume"].rect.bottom + 30))
        surface.blit(display_text, display_rect)
        
        # Draw toggle buttons
        for i, button in enumerate(self.settings_toggle_buttons):
            # Adjust button position to be inside the panel
            button.rect.x = panel_rect.left + 50
            button.rect.y = display_rect.bottom + 20 + i * 60
            button.draw(surface)
            
        # Draw back button
        for button in self.menu_buttons["settings"]:
            button.draw(surface)
            
        # Draw version info
        version_text = small_font.render("v1.0.0", True, (150, 150, 150))
        version_rect = version_text.get_rect(bottomright=(WIDTH - 10, HEIGHT - 10))
        surface.blit(version_text, version_rect)
    
    def draw_credits(self, surface):
        """Draw credits screen"""
        # Draw background
        self.draw_menu_background(surface)
        
        # Draw title
        title_text = heading_font.render("CREDITS", True, WHITE)
        title_rect = title_text.get_rect(center=(WIDTH//2, 70))
        surface.blit(title_text, title_rect)
        
        # Draw credits content
        credits = [
            "Inertia: Deluxe Edition",
            "",
            "A game by PyGameLegends",
            "",
            "Programming: The Python Team",
            "Art & Design: Creative Studios",
            "Sound Effects: Audio Masters",
            "Music: Melodic Minds",
            "",
            "Made with PyGame",
            "",
            "Thanks for playing!"
        ]
        
        y = 150
        for line in credits:
            if line:
                text = medium_font.render(line, True, WHITE)
            else:
                text = medium_font.render(" ", True, WHITE)  # Empty line
                
            text_rect = text.get_rect(center=(WIDTH//2, y))
            surface.blit(text, text_rect)
            y += 30
            
        # Draw back button
        for button in self.menu_buttons["settings"]:
            button.draw(surface)
    
    def draw_tutorial(self, surface):
        """Draw tutorial screen"""
        # First draw the game state behind
        self.draw_game(surface)
        
        # Add overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))
        
        # Draw tutorial content
        # (Add detailed tutorial instructions here)
    
    def handle_events(self):
        """Handle all pygame events"""
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False  # Exit the game
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    mouse_clicked = True
                    
            if event.type == pygame.KEYDOWN:
                # Global key handling
                if event.key == pygame.K_ESCAPE:
                    # ESC key behavior depends on state
                    if self.state == GameState.PLAYING:
                        self.set_state(GameState.PAUSED)
                    elif self.state == GameState.PAUSED:
                        self.set_state(GameState.PLAYING)
                    elif self.state in [GameState.SETTINGS, GameState.CREDITS, GameState.LEVEL_SELECT]:
                        self.set_state(GameState.MAIN_MENU)
                        
                # State-specific key handling
                if self.state == GameState.PLAYING:
                    if event.key == self.settings["controls"]["pause"]:
                        self.toggle_pause()
                    elif event.key == self.settings["controls"]["reset"]:
                        self.restart_level()
                    elif event.key == pygame.K_g and self.gravity_field_active:
                        # Toggle gravity field direction
                        if self.gravity_field_strength == 0:
                            self.gravity_field_strength = 0.2
                            self.gravity_field_color = (148, 0, 211, 80)  # Purple (pull)
                            play_sound("button_click", 0.5)
                        elif self.gravity_field_strength > 0:
                            self.gravity_field_strength = -0.2
                            self.gravity_field_color = (0, 191, 255, 80)  # Blue (push)
                            play_sound("button_click", 0.5)
                        else:
                            self.gravity_field_strength = 0
                            play_sound("button_click", 0.3)
                    elif event.key == pygame.K_space and self.level_num == 1:
                        # Advance tutorial
                        self.tutorial_step += 1
                        play_sound("button_click", 0.5)
        
        # Handle button interactions for different states
        if self.state == GameState.MAIN_MENU:
            for button in self.menu_buttons["main"]:
                if button.update(mouse_pos, mouse_clicked):
                    button.action()
                    
        elif self.state == GameState.LEVEL_SELECT:
            # Check level buttons
            for button in self.level_select_buttons:
                if button["unlocked"] and button["rect"].collidepoint(mouse_pos) and mouse_clicked:
                    self.level_num = button["level"]
                    self.set_state(GameState.PLAYING)
                    play_sound("button_click")
                    
            # Check back button
            for button in self.menu_buttons["level_select"]:
                if button.update(mouse_pos, mouse_clicked):
                    button.action()
                    
        elif self.state == GameState.PAUSED:
            for button in self.menu_buttons["paused"]:
                if button.update(mouse_pos, mouse_clicked):
                    button.action()
                    
        elif self.state == GameState.LEVEL_COMPLETE:
            for button in self.menu_buttons["level_complete"]:
                if button.update(mouse_pos, mouse_clicked):
                    button.action()
                    
        elif self.state == GameState.GAME_OVER:
            for button in self.menu_buttons["game_over"]:
                if button.update(mouse_pos, mouse_clicked):
                    button.action()
                    
        elif self.state == GameState.SETTINGS:
            # Update settings sliders
            for slider in self.settings_sliders.values():
                slider.update(mouse_pos, pygame.mouse.get_pressed())
                
            # Update toggle buttons
            for button in self.settings_toggle_buttons:
                if button.update(mouse_pos, mouse_clicked):
                    button.action()
                    
            # Update back button
            for button in self.menu_buttons["settings"]:
                if button.update(mouse_pos, mouse_clicked):
                    button.action()
                    self.save_settings()
                    
        elif self.state == GameState.CREDITS:
            for button in self.menu_buttons["settings"]:
                if button.update(mouse_pos, mouse_clicked):
                    button.action()
        
        return True  # Continue the game loop
    
    def run(self):
        """Main game loop"""
        running = True
        
        # Initialize game
        self.set_state(GameState.MAIN_MENU)
        play_music("menu")
        
        # For calculating delta time
        prev_time = time.time()
        
        while running:
            # Calculate delta time
            current_time = time.time()
            dt = current_time - prev_time
            prev_time = current_time
            
            # Cap dt to prevent large jumps
            dt = min(dt, 0.1)
            
            # Handle events
            running = self.handle_events()
            
            # Handle keyboard input
            if self.state == GameState.PLAYING:
                self.handle_input(pygame.key.get_pressed())
            
            # Update game state
            self.update(dt)
            
            # Draw the game
            self.draw(screen)
            
            # Update the display
            pygame.display.flip()
            
            # Cap the frame rate
            clock.tick(FPS)
            
        # Save settings and high scores before quitting
        self.save_settings()
        self.save_highscores()
        self.save_level_data()
        
        pygame.quit()
        sys.exit()

    def update_settings(self, dt):
        """Update settings state"""
        # Apply settings changes
        if "music_volume" in self.settings_sliders:
            new_music_volume = self.settings_sliders["music_volume"].current_value
            if self.settings["music_volume"] != new_music_volume:
                self.settings["music_volume"] = new_music_volume
                # Apply music volume change immediately
                pygame.mixer.music.set_volume(new_music_volume)
            
        if "sound_volume" in self.settings_sliders:
            self.settings["sound_volume"] = self.settings_sliders["sound_volume"].current_value
    
    def draw(self, surface):
        """Draw the current game state"""
        # Fill background
        surface.fill((20, 30, 40))
        
        # Apply screen shake
        shake_offset_x = 0
        shake_offset_y = 0
        if self.settings["screen_shake"] and self.screen_shake > 0:
            shake_offset_x = random.randint(-int(self.screen_shake), int(self.screen_shake))
            shake_offset_y = random.randint(-int(self.screen_shake), int(self.screen_shake))
        
        # Draw current state
        if self.state == GameState.PLAYING or self.state == GameState.PAUSED:
            self.draw_game(surface, shake_offset_x, shake_offset_y)
        elif self.state == GameState.MAIN_MENU:
            self.draw_main_menu(surface)
        elif self.state == GameState.LEVEL_SELECT:
            self.draw_level_select(surface)
        elif self.state == GameState.LEVEL_COMPLETE:
            self.draw_level_complete(surface)
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over(surface)
        elif self.state == GameState.SETTINGS:
            self.draw_settings(surface)
        elif self.state == GameState.CREDITS:
            self.draw_credits(surface)
        elif self.state == GameState.TUTORIAL:
            self.draw_tutorial(surface)
        
        # Draw particles (drawn on top in all states)
        self.particle_system.draw(surface)
        
        # Draw toasts
        for toast in self.toasts:
            toast.draw(surface)
            
        # Draw transition overlay
        if self.transition_alpha > 0:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, int(self.transition_alpha)))
            surface.blit(overlay, (0, 0))

    def draw_main_menu(self, surface):
        """Draw main menu state"""
        # Draw animated background
        self.draw_menu_background(surface)
        
        # Draw game title with glow effect
        glow_size = 20
        glow_color = (100, 200, 255, 30)
        glow_surf = pygame.Surface((title_font.size("INERTIA")[0] + glow_size*2, 
                                   title_font.size("INERTIA")[1] + glow_size*2), pygame.SRCALPHA)
        
        # Create pulsing glow
        pulse_time = pygame.time.get_ticks() * 0.001
        glow_alpha = int(math.sin(pulse_time * 2) * 20 + 30)
        glow_color = (100, 200, 255, glow_alpha)
        
        # Draw multiple blurred circles for glow effect
        for i in range(10):
            size = glow_size * (1 - i/10)
            alpha = glow_alpha * (1 - i/10)
            temp_color = (glow_color[0], glow_color[1], glow_color[2], int(alpha))
            pygame.draw.circle(glow_surf, temp_color, 
                              (glow_surf.get_width()//2, glow_surf.get_height()//2), 
                              glow_surf.get_width()//2 - i*2)
        
        # Position glow
        glow_rect = glow_surf.get_rect(center=(WIDTH//2, HEIGHT//4))
        surface.blit(glow_surf, (glow_rect.x - glow_size, glow_rect.y - glow_size))
        
        # Draw game title
        title_text = title_font.render("INERTIA", True, (100, 200, 255))
        title_shadow = title_font.render("INERTIA", True, (50, 100, 150))
        
        # Add pulsing effect to title
        pulse = math.sin(pygame.time.get_ticks() * 0.002) * 0.1 + 1
        title_width = int(title_text.get_width() * pulse)
        title_height = int(title_text.get_height() * pulse)
        
        scaled_title = pygame.transform.scale(title_text, (title_width, title_height))
        scaled_shadow = pygame.transform.scale(title_shadow, (title_width, title_height))
        
        title_rect = scaled_title.get_rect(center=(WIDTH//2, HEIGHT//4))
        shadow_rect = scaled_shadow.get_rect(center=(WIDTH//2 + 5, HEIGHT//4 + 5))
        
        # Draw shadow first, then title
        surface.blit(scaled_shadow, shadow_rect)
        surface.blit(scaled_title, title_rect)
        
        # Draw subtitle with a decorative underline
        subtitle_text = medium_font.render("DELUXE EDITION", True, (255, 255, 100))
        subtitle_rect = subtitle_text.get_rect(center=(WIDTH//2, title_rect.bottom + 20))
        surface.blit(subtitle_text, subtitle_rect)
        
        # Draw decorative underline
        underline_width = subtitle_rect.width + 20
        pygame.draw.line(surface, (255, 255, 100), 
                        (WIDTH//2 - underline_width//2, subtitle_rect.bottom + 5),
                        (WIDTH//2 + underline_width//2, subtitle_rect.bottom + 5), 2)
        
        # Draw menu panel background
        panel_rect = pygame.Rect(WIDTH//2 - 150, subtitle_rect.bottom + 30, 300, 300)
        pygame.draw.rect(surface, (30, 40, 60, 200), panel_rect, border_radius=15)
        pygame.draw.rect(surface, (80, 120, 180), panel_rect, 2, border_radius=15)
        
        # Draw menu buttons with adjusted positions
        for i, button in enumerate(self.menu_buttons["main"]):
            # Adjust button position to be inside the panel
            button.rect.x = panel_rect.left + 40
            button.rect.y = panel_rect.top + 30 + i * 70
            button.draw(surface)
            
        # Draw version and credits
        version_text = small_font.render("Version 1.0", True, (150, 150, 150))
        credits_text = small_font.render("Created by PyGameLegends", True, (150, 150, 150))
        
        surface.blit(version_text, (20, HEIGHT - 50))
        surface.blit(credits_text, (20, HEIGHT - 25))
        
        # Draw total stars collected with a star icon
        stars_text = medium_font.render(f"Total Stars: {self.total_stars}", True, YELLOW)
        stars_rect = stars_text.get_rect(topright=(WIDTH - 20, HEIGHT - 50))
        
        # Draw star icon
        star_size = 20
        star_x = stars_rect.left - star_size - 10
        star_y = stars_rect.centery
        
        # Draw star with glow
        star_glow = pygame.Surface((star_size*3, star_size*3), pygame.SRCALPHA)
        pygame.draw.circle(star_glow, (255, 255, 0, 50), (star_size*3//2, star_size*3//2), star_size)
        surface.blit(star_glow, (star_x - star_size, star_y - star_size))
        
        # Draw star
        pygame.draw.polygon(surface, YELLOW, [
            (star_x, star_y - star_size),
            (star_x + star_size/4, star_y - star_size/2),
            (star_x + star_size/2, star_y - star_size/2),
            (star_x + star_size/4, star_y),
            (star_x + star_size/2, star_y + star_size/2),
            (star_x, star_y + star_size/4),
            (star_x - star_size/2, star_y + star_size/2),
            (star_x - star_size/4, star_y),
            (star_x - star_size/2, star_y - star_size/2),
            (star_x - star_size/4, star_y - star_size/2),
        ])
        
        surface.blit(stars_text, stars_rect)

    def draw_menu_background(self, surface):
        """Draw animated background for menus"""
        # Draw subtle grid pattern
        grid_size = 50
        grid_color = (40, 50, 70)
        
        # Animate grid based on time
        offset_x = int(pygame.time.get_ticks() * 0.02) % grid_size
        offset_y = int(pygame.time.get_ticks() * 0.01) % grid_size
        
        for x in range(-offset_x, WIDTH, grid_size):
            pygame.draw.line(surface, grid_color, (x, 0), (x, HEIGHT), 1)
        for y in range(-offset_y, HEIGHT, grid_size):
            pygame.draw.line(surface, grid_color, (0, y), (WIDTH, y), 1)
            
        # Draw circular patterns
        time_val = pygame.time.get_ticks() * 0.001
        for i in range(3):
            radius = 150 + i * 100
            alpha = int(50 - i * 10)
            speed = 0.2 - i * 0.05
            
            # Calculate position based on time
            angle = time_val * speed
            x = WIDTH // 2 + math.cos(angle) * 50
            y = HEIGHT // 2 + math.sin(angle) * 50
            
            # Draw circle with alpha
            circle_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(circle_surf, (100, 150, 255, alpha), (radius, radius), radius, 2)
            surface.blit(circle_surf, (int(x - radius), int(y - radius)))

    def draw_level_select(self, surface):
        """Draw level select screen"""
        # Draw background
        self.draw_menu_background(surface)
        
        # Draw title with an animated glow effect
        title_text = heading_font.render("SELECT LEVEL", True, WHITE)
        title_rect = title_text.get_rect(center=(WIDTH//2, 70))
        
        # Animated underline
        pulse_time = pygame.time.get_ticks() * 0.001
        
        # Draw glow behind title
        glow_size = 30
        glow_surf = pygame.Surface((title_rect.width + glow_size*2, 
                                  title_rect.height + glow_size*2), pygame.SRCALPHA)
        
        # Create pulsing glow
        glow_alpha = int(math.sin(pulse_time * 2) * 20 + 30)
        glow_color = (255, 255, 100, glow_alpha)
        
        # Draw multiple blurred circles for glow effect
        for i in range(5):
            size = glow_size * (1 - i/5)
            alpha = glow_alpha * (1 - i/5)
            temp_color = (glow_color[0], glow_color[1], glow_color[2], int(alpha))
            pygame.draw.rect(glow_surf, temp_color, 
                           (glow_size - i*2, glow_size - i*2, 
                            title_rect.width + i*4, title_rect.height + i*4), 
                           border_radius=10)
        
        # Position glow
        surface.blit(glow_surf, (title_rect.x - glow_size, title_rect.y - glow_size))
        
        # Draw title with subtle shadow
        shadow_offset = 3
        title_shadow = heading_font.render("SELECT LEVEL", True, (30, 30, 30))
        surface.blit(title_shadow, (title_rect.x + shadow_offset, title_rect.y + shadow_offset))
        surface.blit(title_text, title_rect)
        
        # Draw decorative animated underline
        underline_width = title_rect.width + 40
        underline_y = title_rect.bottom + 5
        # Draw glowing underline
        pygame.draw.line(surface, YELLOW, 
                        (WIDTH//2 - underline_width//2, underline_y),
                        (WIDTH//2 + underline_width//2, underline_y), 3)
        
        # Add animated particles on the underline
        particle_count = 3
        for i in range(particle_count):
            # Calculate position along the line based on time
            offset = (pulse_time * 0.5 + i/particle_count) % 1.0
            particle_x = WIDTH//2 - underline_width//2 + offset * underline_width
            
            # Draw glowing particle
            particle_size = 6 + math.sin(pulse_time * 5) * 2
            pygame.draw.circle(surface, (255, 255, 255, 200), 
                              (int(particle_x), int(underline_y)), int(particle_size))
        
        # Draw stars information with an animated glowing effect
        stars_text = medium_font.render(f"Total Stars: {self.total_stars}", True, YELLOW)
        stars_rect = stars_text.get_rect(centerx=WIDTH//2, top=title_rect.bottom + 20)
        
        # Animated glow effect
        glow_alpha = int(abs(math.sin(pulse_time * 2)) * 50 + 20)
        
        # Draw star icon next to text
        star_size = 20
        star_x = stars_rect.left - star_size - 10
        star_y = stars_rect.centery
        
        # Draw star with glow
        star_glow = pygame.Surface((star_size*3, star_size*3), pygame.SRCALPHA)
        glow_radius = star_size + math.sin(pulse_time * 4) * 5
        pygame.draw.circle(star_glow, (255, 255, 0, glow_alpha), 
                          (star_size*3//2, star_size*3//2), int(glow_radius))
        surface.blit(star_glow, (star_x - star_size, star_y - star_size))
        
        # Draw star
        pygame.draw.polygon(surface, YELLOW, [
            (star_x, star_y - star_size),
            (star_x + star_size/4, star_y - star_size/2),
            (star_x + star_size/2, star_y - star_size/2),
            (star_x + star_size/4, star_y),
            (star_x + star_size/2, star_y + star_size/2),
            (star_x, star_y + star_size/4),
            (star_x - star_size/2, star_y + star_size/2),
            (star_x - star_size/4, star_y),
            (star_x - star_size/2, star_y - star_size/2),
            (star_x - star_size/4, star_y - star_size/2),
        ])
        
        # Draw text with glow
        glow_surf = pygame.Surface((stars_text.get_width() + 20, stars_text.get_height() + 20), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (255, 255, 0, glow_alpha), glow_surf.get_rect(), border_radius=10)
        surface.blit(glow_surf, (stars_rect.left - 10, stars_rect.top - 10))
        surface.blit(stars_text, stars_rect)
        
        # Draw level selection grid with a stylish panel background
        panel_rect = pygame.Rect(WIDTH//2 - 350, stars_rect.bottom + 20, 700, 400)
        
        # Draw panel with gradient effect
        gradient_surf = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        for i in range(panel_rect.height):
            alpha = 200 - i * 0.3
            pygame.draw.line(gradient_surf, (30, 40, 50, alpha), 
                           (0, i), (panel_rect.width, i))
        surface.blit(gradient_surf, panel_rect)
        
        # Draw sleek border with rounded corners
        pygame.draw.rect(surface, (80, 100, 120), panel_rect, 2, border_radius=15)
        
        # Subtle inner glow for panel
        glow_surf = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        for i in range(5):
            pygame.draw.rect(glow_surf, (100, 150, 255, 10 - i*2), 
                           (i, i, panel_rect.width - i*2, panel_rect.height - i*2), 
                           border_radius=15)
        surface.blit(glow_surf, panel_rect)
        
        # Get mouse position for hover effects
        mouse_pos = pygame.mouse.get_pos()
        current_time = pygame.time.get_ticks() * 0.001
        
        # Draw level buttons with improved animation
        for button in self.level_select_buttons:
            rect = button["rect"]
            level = button["level"]
            stars = button["stars"]
            unlocked = button["unlocked"]
            
            # Check if mouse is hovering and update pulse
            prev_hover = button["hover"]
            button["hover"] = rect.collidepoint(mouse_pos)
            
            # Start a new pulse when hover state changes
            if button["hover"] and not prev_hover:
                button["pulse"] = 0
            
            # Update pulse animation
            if button["hover"]:
                button["pulse"] = min(1.0, button["pulse"] + 0.05)
            else:
                button["pulse"] = max(0.0, button["pulse"] - 0.03)
            
            # Determine button colors and effects based on state
            if not unlocked:
                base_color = (60, 60, 70)  # Locked - darker
                border_color = (100, 100, 100)  # Gray border
                hover_color = (70, 70, 80)  # Slightly lighter on hover
            else:
                base_color = (80, 120, 180)  # Normal - blue
                border_color = (150, 180, 220)  # Light blue border
                hover_color = (100, 180, 255)  # Hover - brighter blue
            
            # Create color transition based on hover state
            if button["pulse"] > 0:
                # Interpolate between base and hover color
                color = (
                    int(base_color[0] + (hover_color[0] - base_color[0]) * button["pulse"]),
                    int(base_color[1] + (hover_color[1] - base_color[1]) * button["pulse"]),
                    int(base_color[2] + (hover_color[2] - base_color[2]) * button["pulse"])
                )
            else:
                color = base_color
            
            # Draw button with 3D effect and improved animations
            shadow_offset = 4
            shadow_rect = rect.copy()
            shadow_rect.y += shadow_offset
            
            # Draw shadow (darker for 3D effect)
            pygame.draw.rect(surface, (20, 30, 40), shadow_rect, border_radius=10)
            
            # Draw main button with rounded corners
            pygame.draw.rect(surface, color, rect, border_radius=10)
            
            # Draw animation effect on hover
            if button["pulse"] > 0:
                # Draw outer glow
                glow_size = int(button["pulse"] * 20)
                if glow_size > 0:
                    glow_surf = pygame.Surface((rect.width + glow_size*2, rect.height + glow_size*2), pygame.SRCALPHA)
                    glow_alpha = int(button["pulse"] * 100)
                    pygame.draw.rect(glow_surf, hover_color + (glow_alpha,), 
                                   (0, 0, rect.width + glow_size*2, rect.height + glow_size*2), 
                                   border_radius=15)
                    surface.blit(glow_surf, (rect.left - glow_size, rect.top - glow_size))
                    
                # Draw animated border
                border_width = 2 + int(button["pulse"] * 2)
                pygame.draw.rect(surface, (200, 230, 255), rect, border_width, border_radius=10)
                
                # Add subtle shine effect on top
                shine_height = int(rect.height * 0.3)
                shine_surf = pygame.Surface((rect.width, shine_height), pygame.SRCALPHA)
                for i in range(shine_height):
                    alpha = 100 - i * (100 / shine_height)
                    pygame.draw.line(shine_surf, (255, 255, 255, int(alpha * button["pulse"])), 
                                   (0, i), (rect.width, i))
                
                shine_rect = pygame.Rect(rect.left, rect.top, rect.width, shine_height)
                surface.blit(shine_surf, shine_rect)
            else:
                # Normal border
                pygame.draw.rect(surface, border_color, rect, 2, border_radius=10)
            
            # Draw level number with shadow effect for better readability
            level_text = medium_font.render(str(level), True, WHITE)
            level_rect = level_text.get_rect(center=rect.center)
            
            # Draw text shadow
            shadow_text = medium_font.render(str(level), True, (20, 20, 20))
            shadow_rect = shadow_text.get_rect(center=(level_rect.centerx + 2, level_rect.centery + 2))
            surface.blit(shadow_text, shadow_rect)
            surface.blit(level_text, level_rect)
            
            # Draw stars with improved visuals
            if unlocked:
                star_size = 15
                star_spacing = 20
                start_x = rect.centerx - (star_spacing * (3-1)) // 2
                star_y = rect.bottom + 10
                
                for i in range(3):  # Max 3 stars per level
                    star_x = start_x + i * star_spacing
                    
                    # Add subtle animation to stars based on time
                    star_offset_y = math.sin(current_time * 2 + i * 0.5) * 2
                    
                    if i < stars:
                        # Filled star with improved glow
                        star_glow = pygame.Surface((star_size*2, star_size*2), pygame.SRCALPHA)
                        glow_alpha = 50 + int(math.sin(current_time * 3 + i) * 20)
                        pygame.draw.circle(star_glow, (255, 255, 0, glow_alpha), 
                                         (star_size, star_size), star_size)
                        surface.blit(star_glow, (star_x - star_size, star_y - star_size + star_offset_y))
                        
                        # Filled star with better shape
                        pygame.draw.polygon(surface, YELLOW, [
                            (star_x, star_y - star_size + star_offset_y),
                            (star_x + star_size/4, star_y - star_size/2 + star_offset_y),
                            (star_x + star_size/2, star_y - star_size/2 + star_offset_y),
                            (star_x + star_size/4, star_y + star_offset_y),
                            (star_x + star_size/2, star_y + star_size/2 + star_offset_y),
                            (star_x, star_y + star_size/4 + star_offset_y),
                            (star_x - star_size/2, star_y + star_size/2 + star_offset_y),
                            (star_x - star_size/4, star_y + star_offset_y),
                            (star_x - star_size/2, star_y - star_size/2 + star_offset_y),
                            (star_x - star_size/4, star_y - star_size/2 + star_offset_y),
                        ])
                    else:
                        # Empty star with better contrast
                        empty_star_color = (100, 100, 120)
                        pygame.draw.polygon(surface, empty_star_color, [
                            (star_x, star_y - star_size + star_offset_y),
                            (star_x + star_size/4, star_y - star_size/2 + star_offset_y),
                            (star_x + star_size/2, star_y - star_size/2 + star_offset_y),
                            (star_x + star_size/4, star_y + star_offset_y),
                            (star_x + star_size/2, star_y + star_size/2 + star_offset_y),
                            (star_x, star_y + star_size/4 + star_offset_y),
                            (star_x - star_size/2, star_y + star_size/2 + star_offset_y),
                            (star_x - star_size/4, star_y + star_offset_y),
                            (star_x - star_size/2, star_y - star_size/2 + star_offset_y),
                            (star_x - star_size/4, star_y - star_size/2 + star_offset_y),
                        ], 2)
            else:
                # Improved lock icon for locked levels
                lock_color = (180, 180, 180)
                lock_size = 15
                lock_x = rect.centerx
                lock_y = rect.bottom + 15
                
                # Add subtle animation to lock
                lock_float = math.sin(current_time * 2) * 2
                
                # Draw lock with shadow for depth
                pygame.draw.rect(surface, (40, 40, 40), 
                               (lock_x - lock_size//2 + 2, lock_y - lock_size//2 + 2 + lock_float, 
                                lock_size, lock_size), 
                               border_radius=3)
                
                # Draw lock body
                pygame.draw.rect(surface, lock_color, 
                               (lock_x - lock_size//2, lock_y - lock_size//2 + lock_float, 
                                lock_size, lock_size), 
                               border_radius=3)
                
                # Draw lock highlight for 3D effect
                pygame.draw.line(surface, (220, 220, 220),
                               (lock_x - lock_size//2 + 2, lock_y - lock_size//2 + 2 + lock_float),
                               (lock_x - lock_size//2 + 2, lock_y + lock_size//2 - 2 + lock_float), 2)
                
                # Draw lock shackle with improved shape
                pygame.draw.arc(surface, lock_color, 
                              (lock_x - lock_size//2, lock_y - lock_size - lock_size//2 + lock_float, 
                               lock_size, lock_size), 
                              0, math.pi, 2)
                
                # Draw unlock requirement text with improved styling
                if level > 1:  # Don't show for level 1
                    stars_needed = level * REQUIRED_STARS_TO_UNLOCK
                    req_text = tiny_font.render(f"Need {stars_needed} stars", True, (220, 220, 220))
                    req_rect = req_text.get_rect(center=(rect.centerx, rect.bottom + 35 + lock_float))
                    
                    # Add subtle shadow for better readability
                    shadow_text = tiny_font.render(f"Need {stars_needed} stars", True, (40, 40, 40))
                    shadow_rect = shadow_text.get_rect(center=(req_rect.centerx + 1, req_rect.centery + 1))
                    surface.blit(shadow_text, shadow_rect)
                    surface.blit(req_text, req_rect)
        
        # Draw back button with improved styling
        for button in self.menu_buttons["level_select"]:
            # Update button style to match the new sleek design
            button.color = (0, 100, 200)  
            button.hover_color = (50, 150, 255)
            button.draw(surface, glow=True)  # Assuming you have a glow parameter for the button class

    def draw_level_complete(self, surface):
        """Draw level complete screen"""
        # First draw the game state behind
        self.draw_game(surface)
        
        # Add overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        # Draw level complete text with animation
        complete_text = heading_font.render("LEVEL COMPLETE!", True, WHITE)
        
        # Animate text entry
        time_since_complete = time.time() - self.level_complete_time
        if time_since_complete < 0.5:
            # Slide in from top
            progress = time_since_complete / 0.5
            text_y = -complete_text.get_height() + progress * (HEIGHT // 3 + complete_text.get_height())
        else:
            text_y = HEIGHT // 3
            
        complete_rect = complete_text.get_rect(centerx=WIDTH//2, top=text_y)
        surface.blit(complete_text, complete_rect)
        
        # Draw stats with animation
        if time_since_complete > 0.7:
            stats_y = complete_rect.bottom + 50
            spacing = 40
            
            # Time
            minutes = int(self.level_time // 60)
            seconds = int(self.level_time % 60)
            time_text = medium_font.render(f"Time: {minutes:02d}:{seconds:02d}", True, WHITE)
            time_rect = time_text.get_rect(centerx=WIDTH//2, top=stats_y)
            surface.blit(time_text, time_rect)
            
            # Score
            score_text = medium_font.render(f"Score: {self.score}", True, WHITE)
            score_rect = score_text.get_rect(centerx=WIDTH//2, top=stats_y + spacing)
            surface.blit(score_text, score_rect)
            
            # Stars collected
            stars_text = medium_font.render(f"Stars Collected: {self.level_complete_stars}/3", True, YELLOW)
            stars_rect = stars_text.get_rect(centerx=WIDTH//2, top=stats_y + spacing * 2)
            surface.blit(stars_text, stars_rect)
            
            # Draw stars with animation
            if time_since_complete > 1.0:
                star_size = 40
                star_spacing = 60
                start_x = WIDTH//2 - star_spacing
                star_y = stars_rect.bottom + 30
                
                for i in range(3):  # Max 3 stars per level
                    star_x = start_x + i * star_spacing
                    star_time = 1.0 + i * 0.5  # Stagger star animations
                    
                    if time_since_complete > star_time:
                        # Calculate animation progress
                        star_progress = min(1.0, (time_since_complete - star_time) / 0.5)
                        
                        # Scale and fade in
                        current_size = star_size * star_progress
                        alpha = int(255 * star_progress)
                        
                        if i < self.level_complete_stars:
                            # Play star sound once for each star
                            if star_progress < 0.1 and i == 0:
                                play_sound("star", 0.8)
                            elif star_progress < 0.1 and i == 1:
                                play_sound("star", 0.8)
                            elif star_progress < 0.1 and i == 2:
                                play_sound("star", 0.8)
                                
                            # Filled star with animation
                            star_surf = pygame.Surface((star_size*2, star_size*2), pygame.SRCALPHA)
                            
                            # Draw star polygon
                            pygame.draw.polygon(star_surf, YELLOW + (alpha,), [
                                (star_size, 0),
                                (star_size + star_size/4, star_size - star_size/2),
                                (star_size*2, star_size - star_size/2),
                                (star_size + star_size/2, star_size),
                                (star_size*2, star_size*2),
                                (star_size, star_size + star_size/2),
                                (0, star_size*2),
                                (star_size - star_size/2, star_size),
                                (0, star_size - star_size/2),
                                (star_size - star_size/4, star_size - star_size/2),
                            ])
                            
                            # Scale to animation size
                            if current_size < star_size:
                                scale_factor = current_size / star_size
                                scaled_star = pygame.transform.scale(
                                    star_surf, 
                                    (int(star_surf.get_width() * scale_factor), 
                                     int(star_surf.get_height() * scale_factor))
                                )
                                star_rect = scaled_star.get_rect(center=(star_x, star_y))
                                surface.blit(scaled_star, star_rect)
                            else:
                                # Add pulsing effect when fully shown
                                pulse = 1 + 0.2 * math.sin((time_since_complete - star_time) * 5)
                                pulse_size = int(star_size * 2 * pulse)
                                scaled_star = pygame.transform.scale(
                                    star_surf, 
                                    (pulse_size, pulse_size)
                                )
                                star_rect = scaled_star.get_rect(center=(star_x, star_y))
                                surface.blit(scaled_star, star_rect)
                        else:
                            # Empty star
                            star_surf = pygame.Surface((star_size*2, star_size*2), pygame.SRCALPHA)
                            pygame.draw.polygon(star_surf, (100, 100, 100, alpha), [
                                (star_size, 0),
                                (star_size + star_size/4, star_size - star_size/2),
                                (star_size*2, star_size - star_size/2),
                                (star_size + star_size/2, star_size),
                                (star_size*2, star_size*2),
                                (star_size, star_size + star_size/2),
                                (0, star_size*2),
                                (star_size - star_size/2, star_size),
                                (0, star_size - star_size/2),
                                (star_size - star_size/4, star_size - star_size/2),
                            ], 2)
                            
                            # Scale to animation size
                            if current_size < star_size:
                                scale_factor = current_size / star_size
                                scaled_star = pygame.transform.scale(
                                    star_surf, 
                                    (int(star_surf.get_width() * scale_factor), 
                                     int(star_surf.get_height() * scale_factor))
                                )
                                star_rect = scaled_star.get_rect(center=(star_x, star_y))
                                surface.blit(scaled_star, star_rect)
                            else:
                                star_rect = star_surf.get_rect(center=(star_x, star_y))
                                surface.blit(star_surf, star_rect)
                                
            # Draw buttons
            if time_since_complete > 2.5:
                for button in self.menu_buttons["level_complete"]:
                    button.draw(surface)

    def draw_game(self, surface, shake_offset_x=0, shake_offset_y=0):
        """Draw the game state with all gameplay elements"""
        # Draw background grid
        grid_size = 50
        grid_color = (40, 50, 60)
        
        for x in range(0, WIDTH, grid_size):
            pygame.draw.line(surface, grid_color, 
                           (x + shake_offset_x, 0 + shake_offset_y), 
                           (x + shake_offset_x, HEIGHT + shake_offset_y), 1)
        for y in range(0, HEIGHT, grid_size):
            pygame.draw.line(surface, grid_color, 
                           (0 + shake_offset_x, y + shake_offset_y), 
                           (WIDTH + shake_offset_x, y + shake_offset_y), 1)
        
        # Draw level elements
        for wall in self.walls:
            wall.draw(surface, shake_offset_x, shake_offset_y)
            
        # Draw player
        self.ball.draw(surface, shake_offset_x, shake_offset_y)
        
        # Draw collectibles
        for star in self.stars:
            if not star.collected:
                star.draw(surface, shake_offset_x, shake_offset_y)
                
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(surface, shake_offset_x, shake_offset_y)
            
        # Draw exit portal if level is complete
        if self.exit_portal_active:
            self.exit_portal.draw(surface, shake_offset_x, shake_offset_y)
            
        # Draw UI elements
        self.draw_hud(surface)
        
        # Draw any active effects
        if self.gravity_field_active:
            # Draw semi-transparent gravity field
            field_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            field_surf.fill(self.gravity_field_color)
            surface.blit(field_surf, (0, 0))
            
            # Draw gravity direction indicator
            if self.gravity_field_strength != 0:
                center_x, center_y = WIDTH // 2, HEIGHT // 2
                indicator_length = 50
                
                if self.gravity_field_strength > 0:  # Pull
                    start_x, start_y = center_x - indicator_length, center_y
                    end_x, end_y = center_x + indicator_length, center_y
                else:  # Push
                    start_x, start_y = center_x + indicator_length, center_y
                    end_x, end_y = center_x - indicator_length, center_y
                    
                pygame.draw.line(surface, WHITE, (start_x, start_y), (end_x, end_y), 3)
                
                # Draw arrowhead
                arrow_size = 10
                if self.gravity_field_strength > 0:  # Pull
                    pygame.draw.polygon(surface, WHITE, [
                        (end_x, end_y),
                        (end_x - arrow_size, end_y - arrow_size // 2),
                        (end_x - arrow_size, end_y + arrow_size // 2)
                    ])
                else:  # Push
                    pygame.draw.polygon(surface, WHITE, [
                        (end_x, end_y),
                        (end_x + arrow_size, end_y - arrow_size // 2),
                        (end_x + arrow_size, end_y + arrow_size // 2)
                    ])
        
        # Draw tutorial tips if first level
        if self.level_num == 1 and self.tutorial_step > 0:
            self.draw_tutorial_tips(surface)
    
    def draw_hud(self, surface):
        """Draw heads-up display elements"""
        # Draw level indicator
        level_text = medium_font.render(f"Level {self.level_num}", True, WHITE)
        surface.blit(level_text, (20, 20))
        
        # Draw score
        score_text = medium_font.render(f"Score: {self.score}", True, WHITE)
        surface.blit(score_text, (20, 60))
        
        # Draw stars collected
        stars_text = medium_font.render(f"Stars: {self.stars_collected}/3", True, YELLOW)
        surface.blit(stars_text, (20, 100))
        
        # Draw timer
        minutes = int(self.level_time // 60)
        seconds = int(self.level_time % 60)
        timer_text = medium_font.render(f"Time: {minutes:02d}:{seconds:02d}", True, WHITE)
        surface.blit(timer_text, (WIDTH - timer_text.get_width() - 20, 20))
        
        # Draw energy bar if applicable
        if hasattr(self, 'energy'):
            # Background
            pygame.draw.rect(surface, (60, 60, 60), (WIDTH - 220, 60, 200, 20))
            
            # Energy level
            energy_percent = self.energy / 100.0  # Assuming max energy is 100
            energy_width = int(200 * energy_percent)
            
            # Change color based on energy level
            if energy_percent > 0.6:
                energy_color = GREEN
            elif energy_percent > 0.3:
                energy_color = YELLOW
            else:
                energy_color = RED
                
            pygame.draw.rect(surface, energy_color, (WIDTH - 220, 60, energy_width, 20))
            
            # Border
            pygame.draw.rect(surface, WHITE, (WIDTH - 220, 60, 200, 20), 2)
            
            # Label
            energy_label = small_font.render("ENERGY", True, WHITE)
            surface.blit(energy_label, (WIDTH - 220, 40))
    
    def draw_tutorial_tips(self, surface):
        """Draw tutorial tips for the first level"""
        if self.tutorial_step == 1:
            tip_text = ["Use arrow keys to move", "Press SPACE to continue"]
        elif self.tutorial_step == 2:
            tip_text = ["Collect stars to increase your score", "Press SPACE to continue"]
        elif self.tutorial_step == 3:
            tip_text = ["Complete the level quickly for better time stars", "Press SPACE to continue"]
        elif self.tutorial_step == 4:
            tip_text = ["Press G to toggle gravity fields when available", "Press SPACE to continue"]
        elif self.tutorial_step == 5:
            tip_text = ["Press P to pause the game", "Press R to restart the level", "Good luck!"]
        else:
            return
            
        # Draw background panel
        tip_height = len(tip_text) * 30 + 40
        panel_rect = pygame.Rect(WIDTH//2 - 250, HEIGHT - tip_height - 20, 500, tip_height)
        pygame.draw.rect(surface, (0, 0, 0, 180), panel_rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, panel_rect, 2, border_radius=10)
        
        # Draw tip text
        for i, line in enumerate(tip_text):
            tip_surf = medium_font.render(line, True, WHITE)
            tip_rect = tip_surf.get_rect(center=(WIDTH//2, panel_rect.top + 30 + i * 30))
            surface.blit(tip_surf, tip_rect)

    def draw_main_menu(self, surface):
        """Draw main menu state"""
        # Draw animated background
        self.draw_menu_background(surface)
        
        # Draw game title with glow effect
        glow_size = 20
        glow_color = (100, 200, 255, 30)
        glow_surf = pygame.Surface((title_font.size("INERTIA")[0] + glow_size*2, 
                                   title_font.size("INERTIA")[1] + glow_size*2), pygame.SRCALPHA)
        
        # Create pulsing glow
        pulse_time = pygame.time.get_ticks() * 0.001
        glow_alpha = int(math.sin(pulse_time * 2) * 20 + 30)
        glow_color = (100, 200, 255, glow_alpha)
        
        # Draw multiple blurred circles for glow effect
        for i in range(10):
            size = glow_size * (1 - i/10)
            alpha = glow_alpha * (1 - i/10)
            temp_color = (glow_color[0], glow_color[1], glow_color[2], int(alpha))
            pygame.draw.circle(glow_surf, temp_color, 
                              (glow_surf.get_width()//2, glow_surf.get_height()//2), 
                              glow_surf.get_width()//2 - i*2)
        
        # Position glow
        glow_rect = glow_surf.get_rect(center=(WIDTH//2, HEIGHT//4))
        surface.blit(glow_surf, (glow_rect.x - glow_size, glow_rect.y - glow_size))
        
        # Draw game title
        title_text = title_font.render("INERTIA", True, (100, 200, 255))
        title_shadow = title_font.render("INERTIA", True, (50, 100, 150))
        
        # Add pulsing effect to title
        pulse = math.sin(pygame.time.get_ticks() * 0.002) * 0.1 + 1
        title_width = int(title_text.get_width() * pulse)
        title_height = int(title_text.get_height() * pulse)
        
        scaled_title = pygame.transform.scale(title_text, (title_width, title_height))
        scaled_shadow = pygame.transform.scale(title_shadow, (title_width, title_height))
        
        title_rect = scaled_title.get_rect(center=(WIDTH//2, HEIGHT//4))
        shadow_rect = scaled_shadow.get_rect(center=(WIDTH//2 + 5, HEIGHT//4 + 5))
        
        # Draw shadow first, then title
        surface.blit(scaled_shadow, shadow_rect)
        surface.blit(scaled_title, title_rect)
        
        # Draw subtitle with a decorative underline
        subtitle_text = medium_font.render("DELUXE EDITION", True, (255, 255, 100))
        subtitle_rect = subtitle_text.get_rect(center=(WIDTH//2, title_rect.bottom + 20))
        surface.blit(subtitle_text, subtitle_rect)
        
        # Draw decorative underline
        underline_width = subtitle_rect.width + 20
        pygame.draw.line(surface, (255, 255, 100), 
                        (WIDTH//2 - underline_width//2, subtitle_rect.bottom + 5),
                        (WIDTH//2 + underline_width//2, subtitle_rect.bottom + 5), 2)
        
        # Draw menu panel background
        panel_rect = pygame.Rect(WIDTH//2 - 150, subtitle_rect.bottom + 30, 300, 300)
        pygame.draw.rect(surface, (30, 40, 60, 200), panel_rect, border_radius=15)
        pygame.draw.rect(surface, (80, 120, 180), panel_rect, 2, border_radius=15)
        
        # Draw menu buttons with adjusted positions
        for i, button in enumerate(self.menu_buttons["main"]):
            # Adjust button position to be inside the panel
            button.rect.x = panel_rect.left + 40
            button.rect.y = panel_rect.top + 30 + i * 70
            button.draw(surface)
            
        # Draw version and credits
        version_text = small_font.render("Version 1.0", True, (150, 150, 150))
        credits_text = small_font.render("Created by PyGameLegends", True, (150, 150, 150))
        
        surface.blit(version_text, (20, HEIGHT - 50))
        surface.blit(credits_text, (20, HEIGHT - 25))
        
        # Draw total stars collected with a star icon
        stars_text = medium_font.render(f"Total Stars: {self.total_stars}", True, YELLOW)
        stars_rect = stars_text.get_rect(topright=(WIDTH - 20, HEIGHT - 50))
        
        # Draw star icon
        star_size = 20
        star_x = stars_rect.left - star_size - 10
        star_y = stars_rect.centery
        
        # Draw star with glow
        star_glow = pygame.Surface((star_size*3, star_size*3), pygame.SRCALPHA)
        pygame.draw.circle(star_glow, (255, 255, 0, 50), (star_size*3//2, star_size*3//2), star_size)
        surface.blit(star_glow, (star_x - star_size, star_y - star_size))
        
        # Draw star
        pygame.draw.polygon(surface, YELLOW, [
            (star_x, star_y - star_size),
            (star_x + star_size/4, star_y - star_size/2),
            (star_x + star_size/2, star_y - star_size/2),
            (star_x + star_size/4, star_y),
            (star_x + star_size/2, star_y + star_size/2),
            (star_x, star_y + star_size/4),
            (star_x - star_size/2, star_y + star_size/2),
            (star_x - star_size/4, star_y),
            (star_x - star_size/2, star_y - star_size/2),
            (star_x - star_size/4, star_y - star_size/2),
        ])
        
        surface.blit(stars_text, stars_rect)

    def draw_menu_background(self, surface):
        """Draw animated background for menus"""
        # Draw subtle grid pattern
        grid_size = 50
        grid_color = (40, 50, 70)
        
        # Animate grid based on time
        offset_x = int(pygame.time.get_ticks() * 0.02) % grid_size
        offset_y = int(pygame.time.get_ticks() * 0.01) % grid_size
        
        for x in range(-offset_x, WIDTH, grid_size):
            pygame.draw.line(surface, grid_color, (x, 0), (x, HEIGHT), 1)
        for y in range(-offset_y, HEIGHT, grid_size):
            pygame.draw.line(surface, grid_color, (0, y), (WIDTH, y), 1)
            
        # Draw circular patterns
        time_val = pygame.time.get_ticks() * 0.001
        for i in range(3):
            radius = 150 + i * 100
            alpha = int(50 - i * 10)
            speed = 0.2 - i * 0.05
            
            # Calculate position based on time
            angle = time_val * speed
            x = WIDTH // 2 + math.cos(angle) * 50
            y = HEIGHT // 2 + math.sin(angle) * 50
            
            # Draw circle with alpha
            circle_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(circle_surf, (100, 150, 255, alpha), (radius, radius), radius, 2)
            surface.blit(circle_surf, (int(x - radius), int(y - radius)))

    def draw_level_select(self, surface):
        """Draw level select screen"""
        # Draw background
        self.draw_menu_background(surface)
        
        # Draw title with an animated glow effect
        title_text = heading_font.render("SELECT LEVEL", True, WHITE)
        title_rect = title_text.get_rect(center=(WIDTH//2, 70))
        
        # Animated underline
        pulse_time = pygame.time.get_ticks() * 0.001
        
        # Draw glow behind title
        glow_size = 30
        glow_surf = pygame.Surface((title_rect.width + glow_size*2, 
                                  title_rect.height + glow_size*2), pygame.SRCALPHA)
        
        # Create pulsing glow
        glow_alpha = int(math.sin(pulse_time * 2) * 20 + 30)
        glow_color = (255, 255, 100, glow_alpha)
        
        # Draw multiple blurred circles for glow effect
        for i in range(5):
            size = glow_size * (1 - i/5)
            alpha = glow_alpha * (1 - i/5)
            temp_color = (glow_color[0], glow_color[1], glow_color[2], int(alpha))
            pygame.draw.rect(glow_surf, temp_color, 
                           (glow_size - i*2, glow_size - i*2, 
                            title_rect.width + i*4, title_rect.height + i*4), 
                           border_radius=10)
        
        # Position glow
        surface.blit(glow_surf, (title_rect.x - glow_size, title_rect.y - glow_size))
        
        # Draw title with subtle shadow
        shadow_offset = 3
        title_shadow = heading_font.render("SELECT LEVEL", True, (30, 30, 30))
        surface.blit(title_shadow, (title_rect.x + shadow_offset, title_rect.y + shadow_offset))
        surface.blit(title_text, title_rect)
        
        # Draw decorative animated underline
        underline_width = title_rect.width + 40
        underline_y = title_rect.bottom + 5
        # Draw glowing underline
        pygame.draw.line(surface, YELLOW, 
                        (WIDTH//2 - underline_width//2, underline_y),
                        (WIDTH//2 + underline_width//2, underline_y), 3)
        
        # Add animated particles on the underline
        particle_count = 3
        for i in range(particle_count):
            # Calculate position along the line based on time
            offset = (pulse_time * 0.5 + i/particle_count) % 1.0
            particle_x = WIDTH//2 - underline_width//2 + offset * underline_width
            
            # Draw glowing particle
            particle_size = 6 + math.sin(pulse_time * 5) * 2
            pygame.draw.circle(surface, (255, 255, 255, 200), 
                              (int(particle_x), int(underline_y)), int(particle_size))
        
        # Draw stars information with an animated glowing effect
        stars_text = medium_font.render(f"Total Stars: {self.total_stars}", True, YELLOW)
        stars_rect = stars_text.get_rect(centerx=WIDTH//2, top=title_rect.bottom + 20)
        
        # Animated glow effect
        glow_alpha = int(abs(math.sin(pulse_time * 2)) * 50 + 20)
        
        # Draw star icon next to text
        star_size = 20
        star_x = stars_rect.left - star_size - 10
        star_y = stars_rect.centery
        
        # Draw star with glow
        star_glow = pygame.Surface((star_size*3, star_size*3), pygame.SRCALPHA)
        glow_radius = star_size + math.sin(pulse_time * 4) * 5
        pygame.draw.circle(star_glow, (255, 255, 0, glow_alpha), 
                          (star_size*3//2, star_size*3//2), int(glow_radius))
        surface.blit(star_glow, (star_x - star_size, star_y - star_size))
        
        # Draw star
        pygame.draw.polygon(surface, YELLOW, [
            (star_x, star_y - star_size),
            (star_x + star_size/4, star_y - star_size/2),
            (star_x + star_size/2, star_y - star_size/2),
            (star_x + star_size/4, star_y),
            (star_x + star_size/2, star_y + star_size/2),
            (star_x, star_y + star_size/4),
            (star_x - star_size/2, star_y + star_size/2),
            (star_x - star_size/4, star_y),
            (star_x - star_size/2, star_y - star_size/2),
            (star_x - star_size/4, star_y - star_size/2),
        ])
        
        # Draw text with glow
        glow_surf = pygame.Surface((stars_text.get_width() + 20, stars_text.get_height() + 20), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (255, 255, 0, glow_alpha), glow_surf.get_rect(), border_radius=10)
        surface.blit(glow_surf, (stars_rect.left - 10, stars_rect.top - 10))
        surface.blit(stars_text, stars_rect)
        
        # Draw level selection grid with a stylish panel background
        panel_rect = pygame.Rect(WIDTH//2 - 350, stars_rect.bottom + 20, 700, 400)
        
        # Draw panel with gradient effect
        gradient_surf = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        for i in range(panel_rect.height):
            alpha = 200 - i * 0.3
            pygame.draw.line(gradient_surf, (30, 40, 50, alpha), 
                           (0, i), (panel_rect.width, i))
        surface.blit(gradient_surf, panel_rect)
        
        # Draw sleek border with rounded corners
        pygame.draw.rect(surface, (80, 100, 120), panel_rect, 2, border_radius=15)
        
        # Subtle inner glow for panel
        glow_surf = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        for i in range(5):
            pygame.draw.rect(glow_surf, (100, 150, 255, 10 - i*2), 
                           (i, i, panel_rect.width - i*2, panel_rect.height - i*2), 
                           border_radius=15)
        surface.blit(glow_surf, panel_rect)
        
        # Get mouse position for hover effects
        mouse_pos = pygame.mouse.get_pos()
        current_time = pygame.time.get_ticks() * 0.001
        
        # Draw level buttons with improved animation
        for button in self.level_select_buttons:
            rect = button["rect"]
            level = button["level"]
            stars = button["stars"]
            unlocked = button["unlocked"]
            
            # Check if mouse is hovering and update pulse
            prev_hover = button["hover"]
            button["hover"] = rect.collidepoint(mouse_pos)
            
            # Start a new pulse when hover state changes
            if button["hover"] and not prev_hover:
                button["pulse"] = 0
            
            # Update pulse animation
            if button["hover"]:
                button["pulse"] = min(1.0, button["pulse"] + 0.05)
            else:
                button["pulse"] = max(0.0, button["pulse"] - 0.03)
            
            # Determine button colors and effects based on state
            if not unlocked:
                base_color = (60, 60, 70)  # Locked - darker
                border_color = (100, 100, 100)  # Gray border
                hover_color = (70, 70, 80)  # Slightly lighter on hover
            else:
                base_color = (80, 120, 180)  # Normal - blue
                border_color = (150, 180, 220)  # Light blue border
                hover_color = (100, 180, 255)  # Hover - brighter blue
            
            # Create color transition based on hover state
            if button["pulse"] > 0:
                # Interpolate between base and hover color
                color = (
                    int(base_color[0] + (hover_color[0] - base_color[0]) * button["pulse"]),
                    int(base_color[1] + (hover_color[1] - base_color[1]) * button["pulse"]),
                    int(base_color[2] + (hover_color[2] - base_color[2]) * button["pulse"])
                )
            else:
                color = base_color
            
            # Draw button with 3D effect and improved animations
            shadow_offset = 4
            shadow_rect = rect.copy()
            shadow_rect.y += shadow_offset
            
            # Draw shadow (darker for 3D effect)
            pygame.draw.rect(surface, (20, 30, 40), shadow_rect, border_radius=10)
            
            # Draw main button with rounded corners
            pygame.draw.rect(surface, color, rect, border_radius=10)
            
            # Draw animation effect on hover
            if button["pulse"] > 0:
                # Draw outer glow
                glow_size = int(button["pulse"] * 20)
                if glow_size > 0:
                    glow_surf = pygame.Surface((rect.width + glow_size*2, rect.height + glow_size*2), pygame.SRCALPHA)
                    glow_alpha = int(button["pulse"] * 100)
                    pygame.draw.rect(glow_surf, hover_color + (glow_alpha,), 
                                   (0, 0, rect.width + glow_size*2, rect.height + glow_size*2), 
                                   border_radius=15)
                    surface.blit(glow_surf, (rect.left - glow_size, rect.top - glow_size))
                    
                # Draw animated border
                border_width = 2 + int(button["pulse"] * 2)
                pygame.draw.rect(surface, (200, 230, 255), rect, border_width, border_radius=10)
                
                # Add subtle shine effect on top
                shine_height = int(rect.height * 0.3)
                shine_surf = pygame.Surface((rect.width, shine_height), pygame.SRCALPHA)
                for i in range(shine_height):
                    alpha = 100 - i * (100 / shine_height)
                    pygame.draw.line(shine_surf, (255, 255, 255, int(alpha * button["pulse"])), 
                                   (0, i), (rect.width, i))
                
                shine_rect = pygame.Rect(rect.left, rect.top, rect.width, shine_height)
                surface.blit(shine_surf, shine_rect)
            else:
                # Normal border
                pygame.draw.rect(surface, border_color, rect, 2, border_radius=10)
            
            # Draw level number with shadow effect for better readability
            level_text = medium_font.render(str(level), True, WHITE)
            level_rect = level_text.get_rect(center=rect.center)
            
            # Draw text shadow
            shadow_text = medium_font.render(str(level), True, (20, 20, 20))
            shadow_rect = shadow_text.get_rect(center=(level_rect.centerx + 2, level_rect.centery + 2))
            surface.blit(shadow_text, shadow_rect)
            surface.blit(level_text, level_rect)
            
            # Draw stars with improved visuals
            if unlocked:
                star_size = 15
                star_spacing = 20
                start_x = rect.centerx - (star_spacing * (3-1)) // 2
                star_y = rect.bottom + 10
                
                for i in range(3):  # Max 3 stars per level
                    star_x = start_x + i * star_spacing
                    
                    # Add subtle animation to stars based on time
                    star_offset_y = math.sin(current_time * 2 + i * 0.5) * 2
                    
                    if i < stars:
                        # Filled star with improved glow
                        star_glow = pygame.Surface((star_size*2, star_size*2), pygame.SRCALPHA)
                        glow_alpha = 50 + int(math.sin(current_time * 3 + i) * 20)
                        pygame.draw.circle(star_glow, (255, 255, 0, glow_alpha), 
                                         (star_size, star_size), star_size)
                        surface.blit(star_glow, (star_x - star_size, star_y - star_size + star_offset_y))
                        
                        # Filled star with better shape
                        pygame.draw.polygon(surface, YELLOW, [
                            (star_x, star_y - star_size + star_offset_y),
                            (star_x + star_size/4, star_y - star_size/2 + star_offset_y),
                            (star_x + star_size/2, star_y - star_size/2 + star_offset_y),
                            (star_x + star_size/4, star_y + star_offset_y),
                            (star_x + star_size/2, star_y + star_size/2 + star_offset_y),
                            (star_x, star_y + star_size/4 + star_offset_y),
                            (star_x - star_size/2, star_y + star_size/2 + star_offset_y),
                            (star_x - star_size/4, star_y + star_offset_y),
                            (star_x - star_size/2, star_y - star_size/2 + star_offset_y),
                            (star_x - star_size/4, star_y - star_size/2 + star_offset_y),
                        ])
                    else:
                        # Empty star with better contrast
                        empty_star_color = (100, 100, 120)
                        pygame.draw.polygon(surface, empty_star_color, [
                            (star_x, star_y - star_size + star_offset_y),
                            (star_x + star_size/4, star_y - star_size/2 + star_offset_y),
                            (star_x + star_size/2, star_y - star_size/2 + star_offset_y),
                            (star_x + star_size/4, star_y + star_offset_y),
                            (star_x + star_size/2, star_y + star_size/2 + star_offset_y),
                            (star_x, star_y + star_size/4 + star_offset_y),
                            (star_x - star_size/2, star_y + star_size/2 + star_offset_y),
                            (star_x - star_size/4, star_y + star_offset_y),
                            (star_x - star_size/2, star_y - star_size/2 + star_offset_y),
                            (star_x - star_size/4, star_y - star_size/2 + star_offset_y),
                        ], 2)
            else:
                # Improved lock icon for locked levels
                lock_color = (180, 180, 180)
                lock_size = 15
                lock_x = rect.centerx
                lock_y = rect.bottom + 15
                
                # Add subtle animation to lock
                lock_float = math.sin(current_time * 2) * 2
                
                # Draw lock with shadow for depth
                pygame.draw.rect(surface, (40, 40, 40), 
                               (lock_x - lock_size//2 + 2, lock_y - lock_size//2 + 2 + lock_float, 
                                lock_size, lock_size), 
                               border_radius=3)
                
                # Draw lock body
                pygame.draw.rect(surface, lock_color, 
                               (lock_x - lock_size//2, lock_y - lock_size//2 + lock_float, 
                                lock_size, lock_size), 
                               border_radius=3)
                
                # Draw lock highlight for 3D effect
                pygame.draw.line(surface, (220, 220, 220),
                               (lock_x - lock_size//2 + 2, lock_y - lock_size//2 + 2 + lock_float),
                               (lock_x - lock_size//2 + 2, lock_y + lock_size//2 - 2 + lock_float), 2)
                
                # Draw lock shackle with improved shape
                pygame.draw.arc(surface, lock_color, 
                              (lock_x - lock_size//2, lock_y - lock_size - lock_size//2 + lock_float, 
                               lock_size, lock_size), 
                              0, math.pi, 2)
                
                # Draw unlock requirement text with improved styling
                if level > 1:  # Don't show for level 1
                    stars_needed = level * REQUIRED_STARS_TO_UNLOCK
                    req_text = tiny_font.render(f"Need {stars_needed} stars", True, (220, 220, 220))
                    req_rect = req_text.get_rect(center=(rect.centerx, rect.bottom + 35 + lock_float))
                    
                    # Add subtle shadow for better readability
                    shadow_text = tiny_font.render(f"Need {stars_needed} stars", True, (40, 40, 40))
                    shadow_rect = shadow_text.get_rect(center=(req_rect.centerx + 1, req_rect.centery + 1))
                    surface.blit(shadow_text, shadow_rect)
                    surface.blit(req_text, req_rect)
        
        # Draw back button with improved styling
        for button in self.menu_buttons["level_select"]:
            # Update button style to match the new sleek design
            button.color = (0, 100, 200)  
            button.hover_color = (50, 150, 255)
            button.draw(surface, glow=True)  # Assuming you have a glow parameter for the button class

    def draw_level_complete(self, surface):
        """Draw level complete screen"""
        # First draw the game state behind
        self.draw_game(surface)
        
        # Add overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        # Draw level complete text with animation
        complete_text = heading_font.render("LEVEL COMPLETE!", True, WHITE)
        
        # Animate text entry
        time_since_complete = time.time() - self.level_complete_time
        if time_since_complete < 0.5:
            # Slide in from top
            progress = time_since_complete / 0.5
            text_y = -complete_text.get_height() + progress * (HEIGHT // 3 + complete_text.get_height())
        else:
            text_y = HEIGHT // 3
            
        complete_rect = complete_text.get_rect(centerx=WIDTH//2, top=text_y)
        surface.blit(complete_text, complete_rect)
        
        # Draw stats with animation
        if time_since_complete > 0.7:
            stats_y = complete_rect.bottom + 50
            spacing = 40
            
            # Time
            minutes = int(self.level_time // 60)
            seconds = int(self.level_time % 60)
            time_text = medium_font.render(f"Time: {minutes:02d}:{seconds:02d}", True, WHITE)
            time_rect = time_text.get_rect(centerx=WIDTH//2, top=stats_y)
            surface.blit(time_text, time_rect)
            
            # Score
            score_text = medium_font.render(f"Score: {self.score}", True, WHITE)
            score_rect = score_text.get_rect(centerx=WIDTH//2, top=stats_y + spacing)
            surface.blit(score_text, score_rect)
            
            # Stars collected
            stars_text = medium_font.render(f"Stars Collected: {self.level_complete_stars}/3", True, YELLOW)
            stars_rect = stars_text.get_rect(centerx=WIDTH//2, top=stats_y + spacing * 2)
            surface.blit(stars_text, stars_rect)
            
            # Draw stars with animation
            if time_since_complete > 1.0:
                star_size = 40
                star_spacing = 60
                start_x = WIDTH//2 - star_spacing
                star_y = stars_rect.bottom + 30
                
                for i in range(3):  # Max 3 stars per level
                    star_x = start_x + i * star_spacing
                    star_time = 1.0 + i * 0.5  # Stagger star animations
                    
                    if time_since_complete > star_time:
                        # Calculate animation progress
                        star_progress = min(1.0, (time_since_complete - star_time) / 0.5)
                        
                        # Scale and fade in
                        current_size = star_size * star_progress
                        alpha = int(255 * star_progress)
                        
                        if i < self.level_complete_stars:
                            # Play star sound once for each star
                            if star_progress < 0.1 and i == 0:
                                play_sound("star", 0.8)
                            elif star_progress < 0.1 and i == 1:
                                play_sound("star", 0.8)
                            elif star_progress < 0.1 and i == 2:
                                play_sound("star", 0.8)
                                
                            # Filled star with animation
                            star_surf = pygame.Surface((star_size*2, star_size*2), pygame.SRCALPHA)
                            
                            # Draw star polygon
                            pygame.draw.polygon(star_surf, YELLOW + (alpha,), [
                                (star_size, 0),
                                (star_size + star_size/4, star_size - star_size/2),
                                (star_size*2, star_size - star_size/2),
                                (star_size + star_size/2, star_size),
                                (star_size*2, star_size*2),
                                (star_size, star_size + star_size/2),
                                (0, star_size*2),
                                (star_size - star_size/2, star_size),
                                (0, star_size - star_size/2),
                                (star_size - star_size/4, star_size - star_size/2),
                            ])
                            
                            # Scale to animation size
                            if current_size < star_size:
                                scale_factor = current_size / star_size
                                scaled_star = pygame.transform.scale(
                                    star_surf, 
                                    (int(star_surf.get_width() * scale_factor), 
                                     int(star_surf.get_height() * scale_factor))
                                )
                                star_rect = scaled_star.get_rect(center=(star_x, star_y))
                                surface.blit(scaled_star, star_rect)
                            else:
                                # Add pulsing effect when fully shown
                                pulse = 1 + 0.2 * math.sin((time_since_complete - star_time) * 5)
                                pulse_size = int(star_size * 2 * pulse)
                                scaled_star = pygame.transform.scale(
                                    star_surf, 
                                    (pulse_size, pulse_size)
                                )
                                star_rect = scaled_star.get_rect(center=(star_x, star_y))
                                surface.blit(scaled_star, star_rect)
                        else:
                            # Empty star
                            star_surf = pygame.Surface((star_size*2, star_size*2), pygame.SRCALPHA)
                            pygame.draw.polygon(star_surf, (100, 100, 100, alpha), [
                                (star_size, 0),
                                (star_size + star_size/4, star_size - star_size/2),
                                (star_size*2, star_size - star_size/2),
                                (star_size + star_size/2, star_size),
                                (star_size*2, star_size*2),
                                (star_size, star_size + star_size/2),
                                (0, star_size*2),
                                (star_size - star_size/2, star_size),
                                (0, star_size - star_size/2),
                                (star_size - star_size/4, star_size - star_size/2),
                            ], 2)
                            
                            # Scale to animation size
                            if current_size < star_size:
                                scale_factor = current_size / star_size
                                scaled_star = pygame.transform.scale(
                                    star_surf, 
                                    (int(star_surf.get_width() * scale_factor), 
                                     int(star_surf.get_height() * scale_factor))
                                )
                                star_rect = scaled_star.get_rect(center=(star_x, star_y))
                                surface.blit(scaled_star, star_rect)
                            else:
                                star_rect = star_surf.get_rect(center=(star_x, star_y))
                                surface.blit(star_surf, star_rect)
                                
            # Draw buttons
            if time_since_complete > 2.5:
                for button in self.menu_buttons["level_complete"]:
                    button.draw(surface)

    def draw_game(self, surface, shake_offset_x=0, shake_offset_y=0):
        """Draw the game state with all gameplay elements"""
        # Draw background grid
        grid_size = 50
        grid_color = (40, 50, 60)
        
        for x in range(0, WIDTH, grid_size):
            pygame.draw.line(surface, grid_color, 
                           (x + shake_offset_x, 0 + shake_offset_y), 
                           (x + shake_offset_x, HEIGHT + shake_offset_y), 1)
        for y in range(0, HEIGHT, grid_size):
            pygame.draw.line(surface, grid_color, 
                           (0 + shake_offset_x, y + shake_offset_y), 
                           (WIDTH + shake_offset_x, y + shake_offset_y), 1)
        
        # Draw level elements
        for wall in self.walls:
            wall.draw(surface, shake_offset_x, shake_offset_y)
            
        # Draw player
        self.ball.draw(surface, shake_offset_x, shake_offset_y)
        
        # Draw collectibles
        for star in self.stars:
            if not star.collected:
                star.draw(surface, shake_offset_x, shake_offset_y)
                
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(surface, shake_offset_x, shake_offset_y)
            
        # Draw exit portal if level is complete
        if self.exit_portal_active:
            self.exit_portal.draw(surface, shake_offset_x, shake_offset_y)
            
        # Draw UI elements
        self.draw_hud(surface)
        
        # Draw any active effects
        if self.gravity_field_active:
            # Draw semi-transparent gravity field
            field_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            field_surf.fill(self.gravity_field_color)
            surface.blit(field_surf, (0, 0))
            
            # Draw gravity direction indicator
            if self.gravity_field_strength != 0:
                center_x, center_y = WIDTH // 2, HEIGHT // 2
                indicator_length = 50
                
                if self.gravity_field_strength > 0:  # Pull
                    start_x, start_y = center_x - indicator_length, center_y
                    end_x, end_y = center_x + indicator_length, center_y
                else:  # Push
                    start_x, start_y = center_x + indicator_length, center_y
                    end_x, end_y = center_x - indicator_length, center_y
                    
                pygame.draw.line(surface, WHITE, (start_x, start_y), (end_x, end_y), 3)
                
                # Draw arrowhead
                arrow_size = 10
                if self.gravity_field_strength > 0:  # Pull
                    pygame.draw.polygon(surface, WHITE, [
                        (end_x, end_y),
                        (end_x - arrow_size, end_y - arrow_size // 2),
                        (end_x - arrow_size, end_y + arrow_size // 2)
                    ])
                else:  # Push
                    pygame.draw.polygon(surface, WHITE, [
                        (end_x, end_y),
                        (end_x + arrow_size, end_y - arrow_size // 2),
                        (end_x + arrow_size, end_y + arrow_size // 2)
                    ])
        
        # Draw tutorial tips if first level
        if self.level_num == 1 and self.tutorial_step > 0:
            self.draw_tutorial_tips(surface)
    
    def draw_hud(self, surface):
        """Draw heads-up display elements"""
        # Draw level indicator
        level_text = medium_font.render(f"Level {self.level_num}", True, WHITE)
        surface.blit(level_text, (20, 20))
        
        # Draw score
        score_text = medium_font.render(f"Score: {self.score}", True, WHITE)
        surface.blit(score_text, (20, 60))
        
        # Draw stars collected
        stars_text = medium_font.render(f"Stars: {self.stars_collected}/3", True, YELLOW)
        surface.blit(stars_text, (20, 100))
        
        # Draw timer
        minutes = int(self.level_time // 60)
        seconds = int(self.level_time % 60)
        timer_text = medium_font.render(f"Time: {minutes:02d}:{seconds:02d}", True, WHITE)
        surface.blit(timer_text, (WIDTH - timer_text.get_width() - 20, 20))
        
        # Draw energy bar if applicable
        if hasattr(self, 'energy'):
            # Background
            pygame.draw.rect(surface, (60, 60, 60), (WIDTH - 220, 60, 200, 20))
            
            # Energy level
            energy_percent = self.energy / 100.0  # Assuming max energy is 100
            energy_width = int(200 * energy_percent)
            
            # Change color based on energy level
            if energy_percent > 0.6:
                energy_color = GREEN
            elif energy_percent > 0.3:
                energy_color = YELLOW
            else:
                energy_color = RED
                
            pygame.draw.rect(surface, energy_color, (WIDTH - 220, 60, energy_width, 20))
            
            # Border
            pygame.draw.rect(surface, WHITE, (WIDTH - 220, 60, 200, 20), 2)
            
            # Label
            energy_label = small_font.render("ENERGY", True, WHITE)
            surface.blit(energy_label, (WIDTH - 220, 40))
    
    def draw_tutorial_tips(self, surface):
        """Draw tutorial tips for the first level"""
        if self.tutorial_step == 1:
            tip_text = ["Use arrow keys to move", "Press SPACE to continue"]
        elif self.tutorial_step == 2:
            tip_text = ["Collect stars to increase your score", "Press SPACE to continue"]
        elif self.tutorial_step == 3:
            tip_text = ["Complete the level quickly for better time stars", "Press SPACE to continue"]
        elif self.tutorial_step == 4:
            tip_text = ["Press G to toggle gravity fields when available", "Press SPACE to continue"]
        elif self.tutorial_step == 5:
            tip_text = ["Press P to pause the game", "Press R to restart the level", "Good luck!"]
        else:
            return
            
        # Draw background panel
        tip_height = len(tip_text) * 30 + 40
        panel_rect = pygame.Rect(WIDTH//2 - 250, HEIGHT - tip_height - 20, 500, tip_height)
        pygame.draw.rect(surface, (0, 0, 0, 180), panel_rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, panel_rect, 2, border_radius=10)
        
        # Draw tip text
        for i, line in enumerate(tip_text):
            tip_surf = medium_font.render(line, True, WHITE)
            tip_rect = tip_surf.get_rect(center=(WIDTH//2, panel_rect.top + 30 + i * 30))
            surface.blit(tip_surf, tip_rect)

    def draw_main_menu(self, surface):
        """Draw main menu state"""
        # Draw animated background
        self.draw_menu_background(surface)
        
        # Draw game title with glow effect
        glow_size = 20
        glow_color = (100, 200, 255, 30)
        glow_surf = pygame.Surface((title_font.size("INERTIA")[0] + glow_size*2, 
                                   title_font.size("INERTIA")[1] + glow_size*2), pygame.SRCALPHA)
        
        # Create pulsing glow
        pulse_time = pygame.time.get_ticks() * 0.001
        glow_alpha = int(math.sin(pulse_time * 2) * 20 + 30)
        glow_color = (100, 200, 255, glow_alpha)
        
        # Draw multiple blurred circles for glow effect
        for i in range(10):
            size = glow_size * (1 - i/10)
            alpha = glow_alpha * (1 - i/10)
            temp_color = (glow_color[0], glow_color[1], glow_color[2], int(alpha))
            pygame.draw.circle(glow_surf, temp_color, 
                              (glow_surf.get_width()//2, glow_surf.get_height()//2), 
                              glow_surf.get_width()//2 - i*2)
        
        # Position glow
        glow_rect = glow_surf.get_rect(center=(WIDTH//2, HEIGHT//4))
        surface.blit(glow_surf, (glow_rect.x - glow_size, glow_rect.y - glow_size))
        
        # Draw game title
        title_text = title_font.render("INERTIA", True, (100, 200, 255))
        title_shadow = title_font.render("INERTIA", True, (50, 100, 150))
        
        # Add pulsing effect to title
        pulse = math.sin(pygame.time.get_ticks() * 0.002) * 0.1 + 1
        title_width = int(title_text.get_width() * pulse)
        title_height = int(title_text.get_height() * pulse)
        
        scaled_title = pygame.transform.scale(title_text, (title_width, title_height))
        scaled_shadow = pygame.transform.scale(title_shadow, (title_width, title_height))
        
        title_rect = scaled_title.get_rect(center=(WIDTH//2, HEIGHT//4))
        shadow_rect = scaled_shadow.get_rect(center=(WIDTH//2 + 5, HEIGHT//4 + 5))
        
        # Draw shadow first, then title
        surface.blit(scaled_shadow, shadow_rect)
        surface.blit(scaled_title, title_rect)
        
        # Draw subtitle with a decorative underline
        subtitle_text = medium_font.render("DELUXE EDITION", True, (255, 255, 100))
        subtitle_rect = subtitle_text.get_rect(center=(WIDTH//2, title_rect.bottom + 20))
        surface.blit(subtitle_text, subtitle_rect)
        
        # Draw decorative underline
        underline_width = subtitle_rect.width + 20
        pygame.draw.line(surface, (255, 255, 100), 
                        (WIDTH//2 - underline_width//2, subtitle_rect.bottom + 5),
                        (WIDTH//2 + underline_width//2, subtitle_rect.bottom + 5), 2)
        
        # Draw menu panel background
        panel_rect = pygame.Rect(WIDTH//2 - 150, subtitle_rect.bottom + 30, 300, 300)
        pygame.draw.rect(surface, (30, 40, 60, 200), panel_rect, border_radius=15)
        pygame.draw.rect(surface, (80, 120, 180), panel_rect, 2, border_radius=15)
        
        # Draw menu buttons with adjusted positions
        for i, button in enumerate(self.menu_buttons["main"]):
            # Adjust button position to be inside the panel
            button.rect.x = panel_rect.left + 40
            button.rect.y = panel_rect.top + 30 + i * 70
            button.draw(surface)
            
        # Draw version and credits
        version_text = small_font.render("Version 1.0", True, (150, 150, 150))
        credits_text = small_font.render("Created by PyGameLegends", True, (150, 150, 150))
        
        surface.blit(version_text, (20, HEIGHT - 50))
        surface.blit(credits_text, (20, HEIGHT - 25))
        
        # Draw total stars collected with a star icon
        stars_text = medium_font.render(f"Total Stars: {self.total_stars}", True, YELLOW)
        stars_rect = stars_text.get_rect(topright=(WIDTH - 20, HEIGHT - 50))
        
        # Draw star icon
        star_size = 20
        star_x = stars_rect.left - star_size - 10
        star_y = stars_rect.centery
        
        # Draw star with glow
        star_glow = pygame.Surface((star_size*3, star_size*3), pygame.SRCALPHA)
        pygame.draw.circle(star_glow, (255, 255, 0, 50), (star_size*3//2, star_size*3//2), star_size)
        surface.blit(star_glow, (star_x - star_size, star_y - star_size))
        
        # Draw star
        pygame.draw.polygon(surface, YELLOW, [
            (star_x, star_y - star_size),
            (star_x + star_size/4, star_y - star_size/2),
            (star_x + star_size/2, star_y - star_size/2),
            (star_x + star_size/4, star_y),
            (star_x + star_size/2, star_y + star_size/2),
            (star_x, star_y + star_size/4),
            (star_x - star_size/2, star_y + star_size/2),
            (star_x - star_size/4, star_y),
            (star_x - star_size/2, star_y - star_size/2),
            (star_x - star_size/4, star_y - star_size/2),
        ])
        
        surface.blit(stars_text, stars_rect)

    def draw_menu_background(self, surface):
        """Draw animated background for menus"""
        # Draw subtle grid pattern
        grid_size = 50
        grid_color = (40, 50, 70)
        
        # Animate grid based on time
        offset_x = int(pygame.time.get_ticks() * 0.02) % grid_size
        offset_y = int(pygame.time.get_ticks() * 0.01) % grid_size
        
        for x in range(-offset_x, WIDTH, grid_size):
            pygame.draw.line(surface, grid_color, (x, 0), (x, HEIGHT), 1)
        for y in range(-offset_y, HEIGHT, grid_size):
            pygame.draw.line(surface, grid_color, (0, y), (WIDTH, y), 1)
            
        # Draw circular patterns
        time_val = pygame.time.get_ticks() * 0.001
        for i in range(3):
            radius = 150 + i * 100
            alpha = int(50 - i * 10)
            speed = 0.2 - i * 0.05
            
            # Calculate position based on time
            angle = time_val * speed
            x = WIDTH // 2 + math.cos(angle) * 50
            y = HEIGHT // 2 + math.sin(angle) * 50
            
            # Draw circle with alpha
            circle_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(circle_surf, (100, 150, 255, alpha), (radius, radius), radius, 2)
            surface.blit(circle_surf, (int(x - radius), int(y - radius)))

    def draw_level_select(self, surface):
        """Draw level select screen"""
        # Draw background
        self.draw_menu_background(surface)
        
        # Draw title with an animated glow effect
        title_text = heading_font.render("SELECT LEVEL", True, WHITE)
        title_rect = title_text.get_rect(center=(WIDTH//2, 70))
        
        # Animated underline
        pulse_time = pygame.time.get_ticks() * 0.001
        
        # Draw glow behind title
        glow_size = 30
        glow_surf = pygame.Surface((title_rect.width + glow_size*2, 
                                  title_rect.height + glow_size*2), pygame.SRCALPHA)
        
        # Create pulsing glow
        glow_alpha = int(math.sin(pulse_time * 2) * 20 + 30)
        glow_color = (255, 255, 100, glow_alpha)
        
        # Draw multiple blurred circles for glow effect
        for i in range(5):
            size = glow_size * (1 - i/5)
            alpha = glow_alpha * (1 - i/5)
            temp_color = (glow_color[0], glow_color[1], glow_color[2], int(alpha))
            pygame.draw.rect(glow_surf, temp_color, 
                           (glow_size - i*2, glow_size - i*2, 
                            title_rect.width + i*4, title_rect.height + i*4), 
                           border_radius=10)
        
        # Position glow
        surface.blit(glow_surf, (title_rect.x - glow_size, title_rect.y - glow_size))
        
        # Draw title with subtle shadow
        shadow_offset = 3
        title_shadow = heading_font.render("SELECT LEVEL", True, (30, 30, 30))
        surface.blit(title_shadow, (title_rect.x + shadow_offset, title_rect.y + shadow_offset))
        surface.blit(title_text, title_rect)
        
        # Draw decorative animated underline
        underline_width = title_rect.width + 40
        underline_y = title_rect.bottom + 5
        # Draw glowing underline
        pygame.draw.line(surface, YELLOW, 
                        (WIDTH//2 - underline_width//2, underline_y),
                        (WIDTH//2 + underline_width//2, underline_y), 3)
        
        # Add animated particles on the underline
        particle_count = 3
        for i in range(particle_count):
            # Calculate position along the line based on time
            offset = (pulse_time * 0.5 + i/particle_count) % 1.0
            particle_x = WIDTH//2 - underline_width//2 + offset * underline_width
            
            # Draw glowing particle
            particle_size = 6 + math.sin(pulse_time * 5) * 2
            pygame.draw.circle(surface, (255, 255, 255, 200), 
                              (int(particle_x), int(underline_y)), int(particle_size))
        
        # Draw stars information with an animated glowing effect
        stars_text = medium_font.render(f"Total Stars: {self.total_stars}", True, YELLOW)
        stars_rect = stars_text.get_rect(centerx=WIDTH//2, top=title_rect.bottom + 20)
        
        # Animated glow effect
        glow_alpha = int(abs(math.sin(pulse_time * 2)) * 50 + 20)
        
        # Draw star icon next to text
        star_size = 20
        star_x = stars_rect.left - star_size - 10
        star_y = stars_rect.centery
        
        # Draw star with glow
        star_glow = pygame.Surface((star_size*3, star_size*3), pygame.SRCALPHA)
        glow_radius = star_size + math.sin(pulse_time * 4) * 5
        pygame.draw.circle(star_glow, (255, 255, 0, glow_alpha), 
                          (star_size*3//2, star_size*3//2), int(glow_radius))
        surface.blit(star_glow, (star_x - star_size, star_y - star_size))
        
        # Draw star
        pygame.draw.polygon(surface, YELLOW, [
            (star_x, star_y - star_size),
            (star_x + star_size/4, star_y - star_size/2),
            (star_x + star_size/2, star_y - star_size/2),
            (star_x + star_size/4, star_y),
            (star_x + star_size/2, star_y + star_size/2),
            (star_x, star_y + star_size/4),
            (star_x - star_size/2, star_y + star_size/2),
            (star_x - star_size/4, star_y),
            (star_x - star_size/2, star_y - star_size/2),
            (star_x - star_size/4, star_y - star_size/2),
        ])
        
        # Draw text with glow
        glow_surf = pygame.Surface((stars_text.get_width() + 20, stars_text.get_height() + 20), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (255, 255, 0, glow_alpha), glow_surf.get_rect(), border_radius=10)
        surface.blit(glow_surf, (stars_rect.left - 10, stars_rect.top - 10))
        surface.blit(stars_text, stars_rect)
        
        # Draw level selection grid with a stylish panel background
        panel_rect = pygame.Rect(WIDTH//2 - 350, stars_rect.bottom + 20, 700, 400)
        
        # Draw panel with gradient effect
        gradient_surf = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        for i in range(panel_rect.height):
            alpha = 200 - i * 0.3
            pygame.draw.line(gradient_surf, (30, 40, 50, alpha), 
                           (0, i), (panel_rect.width, i))
        surface.blit(gradient_surf, panel_rect)
        
        # Draw sleek border with rounded corners
        pygame.draw.rect(surface, (80, 100, 120), panel_rect, 2, border_radius=15)
        
        # Subtle inner glow for panel
        glow_surf = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        for i in range(5):
            pygame.draw.rect(glow_surf, (100, 150, 255, 10 - i*2), 
                           (i, i, panel_rect.width - i*2, panel_rect.height - i*2), 
                           border_radius=15)
        surface.blit(glow_surf, panel_rect)
        
        # Get mouse position for hover effects
        mouse_pos = pygame.mouse.get_pos()
        current_time = pygame.time.get_ticks() * 0.001
        
        # Draw level buttons with improved animation
        for button in self.level_select_buttons:
            rect = button["rect"]
            level = button["level"]
            stars = button["stars"]
            unlocked = button["unlocked"]
            
            # Check if mouse is hovering and update pulse
            prev_hover = button["hover"]
            button["hover"] = rect.collidepoint(mouse_pos)
            
            # Start a new pulse when hover state changes
            if button["hover"] and not prev_hover:
                button["pulse"] = 0
            
            # Update pulse animation
            if button["hover"]:
                button["pulse"] = min(1.0, button["pulse"] + 0.05)
            else:
                button["pulse"] = max(0.0, button["pulse"] - 0.03)
            
            # Determine button colors and effects based on state
            if not unlocked:
                base_color = (60, 60, 70)  # Locked - darker
                border_color = (100, 100, 100)  # Gray border
                hover_color = (70, 70, 80)  # Slightly lighter on hover
            else:
                base_color = (80, 120, 180)  # Normal - blue
                border_color = (150, 180, 220)  # Light blue border
                hover_color = (100, 180, 255)  # Hover - brighter blue
            
            # Create color transition based on hover state
            if button["pulse"] > 0:
                # Interpolate between base and hover color
                color = (
                    int(base_color[0] + (hover_color[0] - base_color[0]) * button["pulse"]),
                    int(base_color[1] + (hover_color[1] - base_color[1]) * button["pulse"]),
                    int(base_color[2] + (hover_color[2] - base_color[2]) * button["pulse"])
                )
            else:
                color = base_color
            
            # Draw button with 3D effect and improved animations
            shadow_offset = 4
            shadow_rect = rect.copy()
            shadow_rect.y += shadow_offset
            
            # Draw shadow (darker for 3D effect)
            pygame.draw.rect(surface, (20, 30, 40), shadow_rect, border_radius=10)
            
            # Draw main button with rounded corners
            pygame.draw.rect(surface, color, rect, border_radius=10)
            
            # Draw animation effect on hover
            if button["pulse"] > 0:
                # Draw outer glow
                glow_size = int(button["pulse"] * 20)
                if glow_size > 0:
                    glow_surf = pygame.Surface((rect.width + glow_size*2, rect.height + glow_size*2), pygame.SRCALPHA)
                    glow_alpha = int(button["pulse"] * 100)
                    pygame.draw.rect(glow_surf, hover_color + (glow_alpha,), 
                                   (0, 0, rect.width + glow_size*2, rect.height + glow_size*2), 
                                   border_radius=15)
                    surface.blit(glow_surf, (rect.left - glow_size, rect.top - glow_size))
                    
                # Draw animated border
                border_width = 2 + int(button["pulse"] * 2)
                pygame.draw.rect(surface, (200, 230, 255), rect, border_width, border_radius=10)
                
                # Add subtle shine effect on top
                shine_height = int(rect.height * 0.3)
                shine_surf = pygame.Surface((rect.width, shine_height), pygame.SRCALPHA)
                for i in range(shine_height):
                    alpha = 100 - i * (100 / shine_height)
                    pygame.draw.line(shine_surf, (255, 255, 255, int(alpha * button["pulse"])), 
                                   (0, i), (rect.width, i))
                
                shine_rect = pygame.Rect(rect.left, rect.top, rect.width, shine_height)
                surface.blit(shine_surf, shine_rect)
            else:
                # Normal border
                pygame.draw.rect(surface, border_color, rect, 2, border_radius=10)
            
            # Draw level number with shadow effect for better readability
            level_text = medium_font.render(str(level), True, WHITE)
            level_rect = level_text.get_rect(center=rect.center)
            
            # Draw text shadow
            shadow_text = medium_font.render(str(level), True, (20, 20, 20))
            shadow_rect = shadow_text.get_rect(center=(level_rect.centerx + 2, level_rect.centery + 2))
            surface.blit(shadow_text, shadow_rect)
            surface.blit(level_text, level_rect)
            
            # Draw stars with improved visuals
            if unlocked:
                star_size = 15
                star_spacing = 20
                start_x = rect.centerx - (star_spacing * (3-1)) // 2
                star_y = rect.bottom + 10
                
                for i in range(3):  # Max 3 stars per level
                    star_x = start_x + i * star_spacing
                    
                    # Add subtle animation to stars based on time
                    star_offset_y = math.sin(current_time * 2 + i * 0.5) * 2
                    
                    if i < stars:
                        # Filled star with improved glow
                        star_glow = pygame.Surface((star_size*2, star_size*2), pygame.SRCALPHA)
                        glow_alpha = 50 + int(math.sin(current_time * 3 + i) * 20)
                        pygame.draw.circle(star_glow, (255, 255, 0, glow_alpha), 
                                         (star_size, star_size), star_size)
                        surface.blit(star_glow, (star_x - star_size, star_y - star_size + star_offset_y))
                        
                        # Filled star with better shape
                        pygame.draw.polygon(surface, YELLOW, [
                            (star_x, star_y - star_size + star_offset_y),
                            (star_x + star_size/4, star_y - star_size/2 + star_offset_y),
                            (star_x + star_size/2, star_y - star_size/2 + star_offset_y),
                            (star_x + star_size/4, star_y + star_offset_y),
                            (star_x + star_size/2, star_y + star_size/2 + star_offset_y),
                            (star_x, star_y + star_size/4 + star_offset_y),
                            (star_x - star_size/2, star_y + star_size/2 + star_offset_y),
                            (star_x - star_size/4, star_y + star_offset_y),
                            (star_x - star_size/2, star_y - star_size/2 + star_offset_y),
                            (star_x - star_size/4, star_y - star_size/2 + star_offset_y),
                        ])
                    else:
                        # Empty star with better contrast
                        empty_star_color = (100, 100, 120)
                        pygame.draw.polygon(surface, empty_star_color, [
                            (star_x, star_y - star_size + star_offset_y),
                            (star_x + star_size/4, star_y - star_size/2 + star_offset_y),
                            (star_x + star_size/2, star_y - star_size/2 + star_offset_y),
                            (star_x + star_size/4, star_y + star_offset_y),
                            (star_x + star_size/2, star_y + star_size/2 + star_offset_y),
                            (star_x, star_y + star_size/4 + star_offset_y),
                            (star_x - star_size/2, star_y + star_size/2 + star_offset_y),
                            (star_x - star_size/4, star_y + star_offset_y),
                            (star_x - star_size/2, star_y - star_size/2 + star_offset_y),
                            (star_x - star_size/4, star_y - star_size/2 + star_offset_y),
                        ], 2)
            else:
                # Improved lock icon for locked levels
                lock_color = (180, 180, 180)
                lock_size = 15
                lock_x = rect.centerx
                lock_y = rect.bottom + 15
                
                # Add subtle animation to lock
                lock_float = math.sin(current_time * 2) * 2
                
                # Draw lock with shadow for depth
                pygame.draw.rect(surface, (40, 40, 40), 
                               (lock_x - lock_size//2 + 2, lock_y - lock_size//2 + 2 + lock_float, 
                                lock_size, lock_size), 
                               border_radius=3)
                
                # Draw lock body
                pygame.draw.rect(surface, lock_color, 
                               (lock_x - lock_size//2, lock_y - lock_size//2 + lock_float, 
                                lock_size, lock_size), 
                               border_radius=3)
                
                # Draw lock highlight for 3D effect
                pygame.draw.line(surface, (220, 220, 220),
                               (lock_x - lock_size//2 + 2, lock_y - lock_size//2 + 2 + lock_float),
                               (lock_x - lock_size//2 + 2, lock_y + lock_size//2 - 2 + lock_float), 2)
                
                # Draw lock shackle with improved shape
                pygame.draw.arc(surface, lock_color, 
                              (lock_x - lock_size//2, lock_y - lock_size - lock_size//2 + lock_float, 
                               lock_size, lock_size), 
                              0, math.pi, 2)
                
                # Draw unlock requirement text with improved styling
                if level > 1:  # Don't show for level 1
                    stars_needed = level * REQUIRED_STARS_TO_UNLOCK
                    req_text = tiny_font.render(f"Need {stars_needed} stars", True, (220, 220, 220))
                    req_rect = req_text.get_rect(center=(rect.centerx, rect.bottom + 35 + lock_float))
                    
                    # Add subtle shadow for better readability
                    shadow_text = tiny_font.render(f"Need {stars_needed} stars", True, (40, 40, 40))
                    shadow_rect = shadow_text.get_rect(center=(req_rect.centerx + 1, req_rect.centery + 1))
                    surface.blit(shadow_text, shadow_rect)
                    surface.blit(req_text, req_rect)
        
        # Draw back button with improved styling
        for button in self.menu_buttons["level_select"]:
            # Update button style to match the new sleek design
            button.color = (0, 100, 200)  
            button.hover_color = (50, 150, 255)
            button.draw(surface, glow=True)  # Assuming you have a glow parameter for the button class

    def draw_level_complete(self, surface):
        """Draw level complete screen"""
        # First draw the game state behind
        self.draw_game(surface)
        
        # Add overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        # Draw level complete text with animation
        complete_text = heading_font.render("LEVEL COMPLETE!", True, WHITE)
        
        # Animate text entry
        time_since_complete = time.time() - self.level_complete_time
        if time_since_complete < 0.5:
            # Slide in from top
            progress = time_since_complete / 0.5
            text_y = -complete_text.get_height() + progress * (HEIGHT // 3 + complete_text.get_height())
        else:
            text_y = HEIGHT // 3
            
        complete_rect = complete_text.get_rect(centerx=WIDTH//2, top=text_y)
        surface.blit(complete_text, complete_rect)
        
        # Draw stats with animation
        if time_since_complete > 0.7:
            stats_y = complete_rect.bottom + 50
            spacing = 40
            
            # Time
            minutes = int(self.level_time // 60)
            seconds = int(self.level_time % 60)
            time_text = medium_font.render(f"Time: {minutes:02d}:{seconds:02d}", True, WHITE)
            time_rect = time_text.get_rect(centerx=WIDTH//2, top=stats_y)
            surface.blit(time_text, time_rect)
            
            # Score
            score_text = medium_font.render(f"Score: {self.score}", True, WHITE)
            score_rect = score_text.get_rect(centerx=WIDTH//2, top=stats_y + spacing)
            surface.blit(score_text, score_rect)
            
            # Stars collected
            stars_text = medium_font.render(f"Stars Collected: {self.level_complete_stars}/3", True, YELLOW)
            stars_rect = stars_text.get_rect(centerx=WIDTH//2, top=stats_y + spacing * 2)
            surface.blit(stars_text, stars_rect)
            
            # Draw stars with animation
            if time_since_complete > 1.0:
                star_size = 40
                star_spacing = 60
                start_x = WIDTH//2 - star_spacing
                star_y = stars_rect.bottom + 30
                
                for i in range(3):  # Max 3 stars per level
                    star_x = start_x + i * star_spacing
                    star_time = 1.0 + i * 0.5  # Stagger star animations
                    
                    if time_since_complete > star_time:
                        # Calculate animation progress
                        star_progress = min(1.0, (time_since_complete - star_time) / 0.5)
                        
                        # Scale and fade in
                        current_size = star_size * star_progress
                        alpha = int(255 * star_progress)
                        
                        if i < self.level_complete_stars:
                            # Play star sound once for each star
                            if star_progress < 0.1 and i == 0:
                                play_sound("star", 0.8)
                            elif star_progress < 0.1 and i == 1:
                                play_sound("star", 0.8)
                            elif star_progress < 0.1 and i == 2:
                                play_sound("star", 0.8)
                                
                            # Filled star with animation
                            star_surf = pygame.Surface((star_size*2, star_size*2), pygame.SRCALPHA)
                            
                            # Draw star polygon
                            pygame.draw.polygon(star_surf, YELLOW + (alpha,), [
                                (star_size, 0),
                                (star_size + star_size/4, star_size - star_size/2),
                                (star_size*2, star_size - star_size/2),
                                (star_size + star_size/2, star_size),
                                (star_size*2, star_size*2),
                                (star_size, star_size + star_size/2),
                                (0, star_size*2),
                                (star_size - star_size/2, star_size),
                                (0, star_size - star_size/2),
                                (star_size - star_size/4, star_size - star_size/2),
                            ])
                            
                            # Scale to animation size
                            if current_size < star_size:
                                scale_factor = current_size / star_size
                                scaled_star = pygame.transform.scale(
                                    star_surf, 
                                    (int(star_surf.get_width() * scale_factor), 
                                     int(star_surf.get_height() * scale_factor))
                                )
                                star_rect = scaled_star.get_rect(center=(star_x, star_y))
                                surface.blit(scaled_star, star_rect)
                            else:
                                # Add pulsing effect when fully shown
                                pulse = 1 + 0.2 * math.sin((time_since_complete - star_time) * 5)
                                pulse_size = int(star_size * 2 * pulse)
                                scaled_star = pygame.transform.scale(
                                    star_surf, 
                                    (pulse_size, pulse_size)
                                )
                                star_rect = scaled_star.get_rect(center=(star_x, star_y))
                                surface.blit(scaled_star, star_rect)
                        else:
                            # Empty star
                            star_surf = pygame.Surface((star_size*2, star_size*2), pygame.SRCALPHA)
                            pygame.draw.polygon(star_surf, (100, 100, 100, alpha), [
                                (star_size, 0),
                                (star_size + star_size/4, star_size - star_size/2),
                                (star_size*2, star_size - star_size/2),
                                (star_size + star_size/2, star_size),
                                (star_size*2, star_size*2),
                                (star_size, star_size + star_size/2),
                                (0, star_size*2),
                                (star_size - star_size/2, star_size),
                                (0, star_size - star_size/2),
                                (star_size - star_size/4, star_size - star_size/2),
                            ], 2)
                            
                            # Scale to animation size
                            if current_size < star_size:
                                scale_factor = current_size / star_size
                                scaled_star = pygame.transform.scale(
                                    star_surf, 
                                    (int(star_surf.get_width() * scale_factor), 
                                     int(star_surf.get_height() * scale_factor))
                                )
                                star_rect = scaled_star.get_rect(center=(star_x, star_y))
                                surface.blit(scaled_star, star_rect)
# Main entry point
if __name__ == "__main__":
    game = Game()
    game.run()