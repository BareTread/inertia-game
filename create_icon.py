import pygame
import os

# Initialize pygame
pygame.init()

# Create a simple icon
icon_size = 32
icon = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)

# Draw a simple ball (circle) as the icon
pygame.draw.circle(icon, (255, 165, 0), (icon_size//2, icon_size//2), icon_size//2-2)
pygame.draw.circle(icon, (255, 255, 255), (icon_size//2, icon_size//2), icon_size//2-2, 2)

# Make sure the directory exists
os.makedirs("assets/images", exist_ok=True)

# Save the icon
pygame.image.save(icon, "assets/images/icon.png")

print("Icon created successfully at assets/images/icon.png")
pygame.quit() 