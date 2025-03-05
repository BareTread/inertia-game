import os
import requests
import shutil
import zipfile
from io import BytesIO

def download_font():
    """Download and save a free font for our game."""
    # Create fonts directory if it doesn't exist
    os.makedirs("assets/fonts", exist_ok=True)
    
    # URL for a free font (Press Start 2P from Google Fonts)
    url = "https://fonts.google.com/download?family=Press%20Start%202P"
    
    try:
        print("Downloading font...")
        response = requests.get(url)
        if response.status_code == 200:
            # Extract the zip file
            with zipfile.ZipFile(BytesIO(response.content)) as z:
                # List all files in the zip
                font_files = [f for f in z.namelist() if f.endswith('.ttf')]
                
                # Extract font files
                for font_file in font_files:
                    z.extract(font_file, "assets/fonts")
                    # Rename to simpler name
                    font_name = os.path.basename(font_file)
                    os.rename(
                        os.path.join("assets/fonts", font_file),
                        os.path.join("assets/fonts", font_name)
                    )
                
                print(f"Successfully downloaded {len(font_files)} font files to assets/fonts/")
                
                # Clean up extracted directories
                for item in os.listdir("assets/fonts"):
                    item_path = os.path.join("assets/fonts", item)
                    if os.path.isdir(item_path) and item != "fonts":
                        shutil.rmtree(item_path)
        else:
            print(f"Failed to download font: {response.status_code}")
            # If failed, create a fallback solution
            create_fallback_fonts()
            
    except Exception as e:
        print(f"Error downloading font: {e}")
        # If an error occurs, create a fallback solution
        create_fallback_fonts()

def create_fallback_fonts():
    """Create a text file instructing how to add fonts."""
    os.makedirs("assets/fonts", exist_ok=True)
    with open("assets/fonts/README.txt", "w") as f:
        f.write("To add fonts to your game:\n")
        f.write("1. Download free fonts from Google Fonts or another source\n")
        f.write("2. Place .ttf files in this directory\n")
        f.write("3. Update the game code to use these font files\n")
    print("Created fallback instructions in assets/fonts/README.txt")

if __name__ == "__main__":
    # Try to download the font
    if not os.path.exists("assets/fonts"):
        download_font()
    else:
        # Check if directory is empty
        if not os.listdir("assets/fonts"):
            download_font()
        else:
            print("Fonts directory already contains files, skipping download.") 