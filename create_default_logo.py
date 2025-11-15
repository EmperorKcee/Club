from PIL import Image, ImageDraw, ImageFont
import os

def create_default_logo():
    # Create a 200x200 image with a blue background
    img = Image.new('RGB', (200, 200), color='#1a3e72')
    d = ImageDraw.Draw(img)
    
    # Draw a white circle
    d.ellipse((10, 10, 190, 190), outline='white', width=4)
    
    # Add text
    try:
        # Try to use a nice font if available, otherwise use default
        font = ImageFont.truetype("arialbd.ttf", 24)
    except IOError:
        font = ImageFont.load_default()
    
    # Draw text in the center
    text = "TEAM"
    text_width = d.textlength(text, font=font)
    d.text(((200 - text_width) // 2, 80), text, fill='white', font=font)
    
    # Create the directory if it doesn't exist
    os.makedirs('static/img', exist_ok=True)
    
    # Save the image
    img.save('static/img/default-team-logo.png')
    print("Default team logo created at static/img/default-team-logo.png")

if __name__ == '__main__':
    create_default_logo()
