import pygame
import os

# Initialize the mixer for sound
pygame.mixer.init()

# Sound cache
sounds = {}
current_music = None
sound_volume = 1.0
music_volume = 0.5

def load_sounds():
    """Load all game sounds from the sounds directory."""
    global sounds
    
    # Create sounds directory if it doesn't exist
    os.makedirs("sounds", exist_ok=True)
    
    # Load sound files if they exist
    sound_files = {
        "collision": "collision.wav",
        "powerup": "powerup.wav",
        "teleport": "teleport.wav",
        "level_complete": "level_complete.wav",
        "energy_low": "energy_low.wav"
    }
    
    for name, filename in sound_files.items():
        path = os.path.join("sounds", filename)
        if os.path.exists(path):
            try:
                sounds[name] = pygame.mixer.Sound(path)
            except Exception as e:
                print(f"Error loading sound {name}: {e}")

def play_sound(sound_name, volume_scale=1.0):
    """Play a sound effect with the given volume scale."""
    if sound_name in sounds:
        volume = sound_volume * volume_scale
        sounds[sound_name].set_volume(volume)
        sounds[sound_name].play()

def set_sound_volume(volume):
    """Set the global sound effect volume."""
    global sound_volume
    sound_volume = volume

def set_music_volume(volume):
    """Set the music volume."""
    global music_volume
    music_volume = volume
    pygame.mixer.music.set_volume(volume)

def play_music(music_name, loop=True):
    """
    Play background music.
    Set loop to True to loop indefinitely.
    """
    global current_music
    
    if music_name == current_music:
        return  # Already playing this music
    
    current_music = music_name
    
    # For future music implementation
    path = os.path.join("sounds", f"{music_name}.wav")
    if os.path.exists(path):
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(music_volume)
            pygame.mixer.music.play(-1 if loop else 0)
        except Exception as e:
            print(f"Error playing music {music_name}: {e}")

def stop_music():
    """Stop the currently playing music."""
    global current_music
    current_music = None
    pygame.mixer.music.stop()

def pause_music():
    """Pause the currently playing music."""
    pygame.mixer.music.pause()

def unpause_music():
    """Unpause the currently playing music."""
    pygame.mixer.music.unpause() 