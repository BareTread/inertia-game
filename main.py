import pygame
import sys
import traceback
import os
from game import Game

def main():
    """Main entry point for the game."""
    try:
        # Initialize pygame
        pygame.init()
        
        # Set window title and icon
        pygame.display.set_caption("Inertia Deluxe")
        
        # Try to load icon
        try:
            icon = pygame.image.load(os.path.join("assets", "images", "icon.png"))
            pygame.display.set_icon(icon)
        except:
            print("Warning: Could not load icon.")
            
        # Create and run the game
        game = Game()
        game.run()
        
    except Exception as e:
        # Print error details and exit
        print("Error:", str(e))
        traceback.print_exc()
        
        # Try to quit pygame in case of error
        try:
            pygame.quit()
        except:
            pass
        
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())