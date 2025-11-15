from PIL import Image, ImageDraw, ImageFont
import os

def create_default_player_image():
    # Create a 200x200 image with a light gray background
    img = Image.new('RGB', (200, 200), color=(240, 240, 240))
    d = ImageDraw.Draw(img)
    
    # Draw a circle
    d.ellipse([(10, 10), (190, 190)], outline=(200, 200, 200), width=2)
    
    # Add text (initials)
    try:
        # Try to use a nice font if available
        font = ImageFont.truetype("arial.ttf", 80)
    except IOError:
        # Fall back to default font
        font = ImageFont.load_default()
    
    text = "?"
    text_bbox = d.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # Position text in the center
    position = ((200 - text_width) // 2, (200 - text_height) // 2 - 10)
    d.text(position, text, fill=(180, 180, 180), font=font)
    
    # Create the img directory if it doesn't exist
    os.makedirs('static/img', exist_ok=True)
    
    # Save the image
    img.save('static/img/default-player.png')
    print("Created default player image at static/img/default-player.png")

if __name__ == "__main__":
    create_default_player_image()
