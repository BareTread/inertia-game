import enum
from typing import List, Optional

class GameState(enum.Enum):
    MAIN_MENU = 0
    LEVEL_SELECT = 1
    SETTINGS = 2
    GAME = 3
    PAUSED = 4
    LEVEL_COMPLETE = 5
    GAME_OVER = 6
    CREDITS = 7

class StateManager:
    def __init__(self, initial_state=GameState.MAIN_MENU):
        """Initialize the state manager with initial state but without game instance."""
        self.game = None  # Will be set later via set_game
        self.state_stack: List[GameState] = [initial_state]
        self.history: List[GameState] = []
        self.transitions = {
            GameState.MAIN_MENU: self._handle_main_menu_transition,
            GameState.LEVEL_SELECT: self._handle_level_select_transition,
            GameState.SETTINGS: self._handle_settings_transition,
            GameState.GAME: self._handle_game_transition,
            GameState.PAUSED: self._handle_paused_transition,
            GameState.LEVEL_COMPLETE: self._handle_level_complete_transition,
            GameState.GAME_OVER: self._handle_game_over_transition,
            GameState.CREDITS: self._handle_credits_transition,
        }

    def set_game(self, game):
        """Set the game reference after initialization."""
        self.game = game

    @property
    def current_state(self) -> GameState:
        """Get the current game state."""
        return self.state_stack[-1] if self.state_stack else GameState.MAIN_MENU

    def change_state(self, new_state: GameState) -> None:
        """Change to a new state, replacing the current one."""
        # Clear all UI elements before changing state
        if self.game and hasattr(self.game, 'ui_manager'):
            self.game.ui_manager.clear_ui_elements()
        
        # Save current state to history
        if self.state_stack:
            self.history.append(self.state_stack.pop())
        
        # Add new state
        self.state_stack.append(new_state)
        
        # Call transition handler if available
        self._handle_transition(new_state)
        
        # Reset any game objects that should be reset on state change
        if self.game and hasattr(self.game, 'reset_for_state_change'):
            self.game.reset_for_state_change(new_state)
        
        # Update UI for the new state
        if self.game and hasattr(self.game, 'ui_manager'):
            self.game.ui_manager.setup_for_state(new_state)
            
        print(f"State changed to {new_state}")

    def push_state(self, new_state: GameState) -> None:
        """Push a new state onto the stack without removing the current one."""
        # Add current state to history
        if self.state_stack:
            self.history.append(self.current_state)
        
        # Add new state
        self.state_stack.append(new_state)
        
        # Call transition handler
        self._handle_transition(new_state)
        
        # Update UI for the new state
        if self.game and hasattr(self.game, 'ui_manager'):
            self.game.ui_manager.setup_for_state(new_state)

    def pop_state(self) -> Optional[GameState]:
        """Pop the current state off the stack and return to the previous one."""
        if len(self.state_stack) > 1:
            old_state = self.state_stack.pop()
            self.history.append(old_state)
            
            # Call transition handler for the now-current state
            self._handle_transition(self.current_state)
            
            # Update UI for the now-current state
            if self.game and hasattr(self.game, 'ui_manager'):
                self.game.ui_manager.setup_for_state(self.current_state)
            
            return old_state
        return None

    def return_to_previous(self) -> None:
        """Return to the previous state in history."""
        if self.history:
            old_state = self.state_stack.pop() if self.state_stack else None
            new_state = self.history.pop()
            
            # Add the old state to the beginning of history
            if old_state:
                self.history.insert(0, old_state)
            
            # Set the new state
            self.state_stack.append(new_state)
            
            # Call transition handler
            self._handle_transition(new_state)
            
            # Update UI for the new state
            if self.game and hasattr(self.game, 'ui_manager'):
                self.game.ui_manager.setup_for_state(new_state)

    def _handle_transition(self, state: GameState) -> None:
        """Handle state transition actions."""
        handler = self.transitions.get(state)
        if handler:
            handler()

    def _handle_main_menu_transition(self) -> None:
        """Handle transition to the main menu state."""
        # Reset game-related states
        if self.game and hasattr(self.game, 'level_manager'):
            pass  # Any cleanup needed

    def _handle_level_select_transition(self) -> None:
        """Handle transition to the level select state."""
        # Load level data if needed
        if self.game and hasattr(self.game, 'level_manager'):
            self.game.level_manager.load_levels_data()

    def _handle_settings_transition(self) -> None:
        """Handle transition to the settings state."""
        # Load current settings
        pass

    def _handle_game_transition(self) -> None:
        """Handle transition to the game state."""
        # Start or resume the game
        pass

    def _handle_paused_transition(self) -> None:
        """Handle transition to the paused state."""
        # Pause game logic and sounds
        pass

    def _handle_level_complete_transition(self) -> None:
        """Handle transition to the level complete state."""
        # Calculate stars, save progress
        if self.game and hasattr(self.game, 'level_manager'):
            current_level = self.game.level_manager.current_level
            if isinstance(current_level, int):
                # Save level completion data
                self.game.level_manager.save_level_completion(current_level)
                # Unlock next level if needed
                unlocked = self.game.level_manager.levels_data.get("unlocked", 1)
                if current_level == unlocked:
                    self.game.level_manager.levels_data["unlocked"] = current_level + 1
                    self.game.level_manager.save_levels_data()

    def _handle_game_over_transition(self) -> None:
        """Handle transition to the game over state."""
        # Reset level or handle game over logic
        pass

    def _handle_credits_transition(self) -> None:
        """Handle transition to the credits state."""
        pass 