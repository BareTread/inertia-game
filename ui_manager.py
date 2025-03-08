import pygame
from state_manager import GameState
from typing import List, Dict, Any, Tuple
from ui.button import Button
from ui.slider import Slider
from ui.toast import Toast
from utils.constants import WIDTH, HEIGHT, WHITE, BLACK, BLUE, GREEN, RED, YELLOW

class UIManager:
    def __init__(self, game):
        self.game = game
        self.ui_elements = []
        self.fonts = {}
        self.toasts = []
        self.toast_duration = 3.0  # seconds
        
        # Initialize fonts
        self._initialize_fonts()
    
    def _initialize_fonts(self):
        """Initialize fonts used in the UI."""
        pygame.font.init()
        
        # Load system fonts as fallbacks
        system_fonts = pygame.font.get_fonts()
        
        # Try to load custom fonts, fall back to system fonts
        try:
            # Try to load custom fonts first
            self.fonts['title'] = pygame.font.Font(None, 48)
            self.fonts['heading'] = pygame.font.Font(None, 36)
            self.fonts['normal'] = pygame.font.Font(None, 24)
            self.fonts['small'] = pygame.font.Font(None, 18)
        except:
            # Fall back to system fonts
            default_font = system_fonts[0] if system_fonts else None
            self.fonts['title'] = pygame.font.SysFont(default_font, 48)
            self.fonts['heading'] = pygame.font.SysFont(default_font, 36)
            self.fonts['normal'] = pygame.font.SysFont(default_font, 24)
            self.fonts['small'] = pygame.font.SysFont(default_font, 18)
    
    def setup_for_state(self, state):
        """Set up UI elements for the given state."""
        self.ui_elements = []
        
        if state == GameState.MAIN_MENU:
            # Create main menu UI elements
            title_y = HEIGHT // 4
            button_width = 200
            button_height = 50
            button_x = WIDTH // 2
            button_start_y = HEIGHT // 2
            button_padding = 20
            
            # Add buttons for main menu
            play_button = Button(
                button_x, button_start_y,
                button_width, button_height,
                "Play", 
                font=self.fonts['normal'],
                callback=lambda: self._start_level(1)
            )
            
            level_select_button = Button(
                button_x, button_start_y + button_height + button_padding,
                button_width, button_height,
                "Level Select",
                font=self.fonts['normal'],
                callback=lambda: self.game.state_manager.change_state(GameState.LEVEL_SELECT)
            )
            
            settings_button = Button(
                button_x, button_start_y + (button_height + button_padding) * 2,
                button_width, button_height,
                "Settings",
                font=self.fonts['normal'],
                callback=lambda: self.game.state_manager.change_state(GameState.SETTINGS)
            )
            
            quit_button = Button(
                button_x, button_start_y + (button_height + button_padding) * 3,
                button_width, button_height,
                "Quit",
                font=self.fonts['normal'],
                callback=self.game._quit_game
            )
            
            self.ui_elements.extend([play_button, level_select_button, settings_button, quit_button])
            
        elif state == GameState.LEVEL_SELECT:
            # Create level select UI elements
            back_button = Button(
                20, HEIGHT - 70,
                100, 50,
                "Back",
                font=self.fonts['normal'],
                callback=lambda: self.game.state_manager.change_state(GameState.MAIN_MENU)
            )
            
            self.ui_elements.append(back_button)
            
            # Create level buttons
            levels_per_row = 5
            button_width = 80
            button_height = 80
            padding = 20
            start_x = (WIDTH - (levels_per_row * (button_width + padding) - padding)) // 2
            start_y = 120
            
            unlocked_level = self.game.level_manager.levels_data.get("unlocked", 1)
            
            for i in range(1, 21):  # Show max 20 levels
                row = (i - 1) // levels_per_row
                col = (i - 1) % levels_per_row
                
                x = start_x + col * (button_width + padding)
                y = start_y + row * (button_height + padding)
                
                # Calculate stars (if any)
                stars = self.game.level_manager.levels_data.get("stars", {}).get(str(i), 0)
                
                # Create button text with stars
                button_text = f"{i}\n"
                if stars > 0:
                    button_text += "★" * stars + "☆" * (3 - stars)
                
                # Level button
                level_button = Button(
                    x, y,
                    button_width, button_height,
                    str(i),
                    font=self.fonts['normal'],
                    callback=lambda level=i: self._start_level(level) if level <= unlocked_level else None,
                    disabled=i > unlocked_level,
                    bg_color=GREEN if i <= unlocked_level else BLUE
                )
                
                self.ui_elements.append(level_button)
            
        elif state == GameState.SETTINGS:
            # Create settings UI elements
            back_button = Button(
                20, HEIGHT - 70,
                100, 50,
                "Back",
                font=self.fonts['normal'],
                callback=lambda: self.game.state_manager.change_state(GameState.MAIN_MENU)
            )
            
            # Sound volume slider
            sound_slider = Slider(
                WIDTH // 2, 150,
                300, 20,
                label="Sound Volume",
                value=self.game.settings.get("sound_volume", 0.7),
                font=self.fonts['normal'],
                callback=self.game._set_sound_volume
            )
            
            # Music volume slider
            music_slider = Slider(
                WIDTH // 2, 220,
                300, 20,
                label="Music Volume",
                value=self.game.settings.get("music_volume", 0.5),
                font=self.fonts['normal'],
                callback=self.game._set_music_volume
            )
            
            # Toggle buttons for other settings
            fullscreen_button = Button(
                WIDTH // 2, 290,
                300, 40,
                "Fullscreen: " + ("On" if self.game.settings.get("fullscreen", False) else "Off"),
                font=self.fonts['normal'],
                callback=self.game._toggle_fullscreen
            )
            
            particles_button = Button(
                WIDTH // 2, 340,
                300, 40,
                "Particles: " + ("On" if self.game.settings.get("particles", True) else "Off"),
                font=self.fonts['normal'],
                callback=self.game._toggle_particles
            )
            
            screen_shake_button = Button(
                WIDTH // 2, 390,
                300, 40,
                "Screen Shake: " + ("On" if self.game.settings.get("screen_shake", True) else "Off"),
                font=self.fonts['normal'],
                callback=self.game._toggle_screen_shake
            )
            
            self.ui_elements.extend([
                back_button, sound_slider, music_slider,
                fullscreen_button, particles_button, screen_shake_button
            ])
        
        elif state == GameState.GAME:
            # Game UI elements like pause button
            pause_button = Button(
                WIDTH - 60, 20,
                40, 40,
                "||",
                font=self.fonts['normal'],
                callback=lambda: self.game.state_manager.change_state(GameState.PAUSED)
            )
            
            restart_button = Button(
                WIDTH - 110, 20,
                40, 40,
                "R",
                font=self.fonts['normal'],
                callback=lambda: self.game._restart_level()
            )
            
            self.ui_elements.extend([pause_button, restart_button])
        
        elif state == GameState.PAUSED:
            # Create pause menu UI elements
            resume_button = Button(
                WIDTH // 2, HEIGHT // 2 - 60,
                200, 50,
                "Resume",
                font=self.fonts['normal'],
                callback=lambda: self.game.state_manager.change_state(GameState.GAME)
            )
            
            restart_button = Button(
                WIDTH // 2, HEIGHT // 2,
                200, 50,
                "Restart Level",
                font=self.fonts['normal'],
                callback=lambda: self.game._restart_level()
            )
            
            settings_button = Button(
                WIDTH // 2, HEIGHT // 2 + 60,
                200, 50,
                "Settings",
                font=self.fonts['normal'],
                callback=lambda: self.game.state_manager.change_state(GameState.SETTINGS)
            )
            
            quit_button = Button(
                WIDTH // 2, HEIGHT // 2 + 120,
                200, 50,
                "Main Menu",
                font=self.fonts['normal'],
                callback=lambda: self.game.state_manager.change_state(GameState.MAIN_MENU)
            )
            
            self.ui_elements.extend([resume_button, restart_button, settings_button, quit_button])
            
        elif state == GameState.LEVEL_COMPLETE:
            # Create level complete UI elements
            current_level = self.game.level_manager.current_level
            next_level = current_level + 1 if isinstance(current_level, int) else 1
            
            # Check if next level is unlocked
            unlocked = self.game.level_manager.levels_data.get("unlocked", 1)
            next_level_available = next_level <= unlocked
            
            next_level_button = Button(
                WIDTH // 2, HEIGHT // 2 + 60,
                200, 50,
                "Next Level" if next_level_available else "Next Level (Locked)",
                font=self.fonts['normal'],
                callback=lambda: self.game.level_manager.setup_level(next_level) and self.game.state_manager.change_state(GameState.GAME),
                disabled=not next_level_available
            )
            
            restart_button = Button(
                WIDTH // 2, HEIGHT // 2 + 120,
                200, 50,
                "Retry Level",
                font=self.fonts['normal'],
                callback=lambda: self.game._restart_level()
            )
            
            main_menu_button = Button(
                WIDTH // 2, HEIGHT // 2 + 180,
                200, 50,
                "Main Menu",
                font=self.fonts['normal'],
                callback=lambda: self.game.state_manager.change_state(GameState.MAIN_MENU)
            )
            
            self.ui_elements.extend([next_level_button, restart_button, main_menu_button])
    
    def process_events(self, events):
        """Process events for UI elements."""
        for event in events:
            # Process UI element events
            for element in self.ui_elements:
                if hasattr(element, 'handle_event'):
                    element.handle_event(event)
    
    def update(self, dt):
        """Update UI elements."""
        # Update toasts
        for toast in self.toasts[:]:
            toast.update(dt)
            if toast.should_remove():
                self.toasts.remove(toast)
        
        # Get mouse state for buttons
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        
        # Update other UI elements
        for element in self.ui_elements:
            if hasattr(element, 'update'):
                # Buttons need mouse position and state
                if 'Button' in str(type(element)):
                    element.update(mouse_pos, mouse_pressed)
                else:
                    # Other elements just need dt
                    element.update(dt)
    
    def draw(self, screen):
        """Draw all UI elements."""
        # Draw UI elements
        for element in self.ui_elements:
            if hasattr(element, 'draw'):
                element.draw(screen)
        
        # Draw toasts
        self._draw_toasts(screen)
    
    def add_toast(self, message, duration=None, color=(255, 255, 255)):
        """Add a toast notification."""
        if duration is None:
            duration = self.toast_duration
        
        self.toasts.append(Toast(message, duration=duration, color=color))
    
    def _draw_toasts(self, screen):
        """Draw toast notifications."""
        # Calculate toast positions from bottom of screen
        y_pos = HEIGHT - 50
        padding = 10
        
        for toast in reversed(self.toasts):
            # Get toast dimensions
            text_width, text_height = toast.get_dimensions()
            
            # Position toast at the bottom of the screen, centered horizontally
            toast_x = (WIDTH - text_width) // 2
            toast_y = y_pos - text_height
            
            # Draw toast
            toast.draw(screen, (toast_x, toast_y))
            
            # Move up for next toast
            y_pos -= text_height + padding
    
    def create_energy_meter(self, screen, applied_force, position=(10, 560), width=100, height=10):
        """Create a visual energy meter when applying force."""
        from utils.constants import MAX_FORCE
        
        # Map force to a percentage (0-100%)
        percentage = min(100, applied_force / MAX_FORCE * 100)
        
        # Draw meter background
        meter_x, meter_y = position
        
        pygame.draw.rect(
            screen,
            (50, 50, 50),
            (meter_x, meter_y, width, height)
        )
        
        # Draw filled portion
        fill_width = int(width * percentage / 100)
        
        # Color varies from green to red based on percentage
        r = min(255, int(percentage * 2.55))
        g = min(255, int((100 - percentage) * 2.55))
        
        pygame.draw.rect(
            screen,
            (r, g, 0),
            (meter_x, meter_y, fill_width, height)
        )
    
    def _start_level(self, level):
        """Set up and start a level."""
        # Set up the level entities
        self.game.level_manager.setup_level(level)
        # Change game state to start the game
        self.game.state_manager.change_state(GameState.GAME) 