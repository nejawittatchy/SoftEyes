"""Generate the SoftEyes app icon."""
from PIL import Image, ImageDraw, ImageFont
import os

def create_app_icon(size=256):
    """Create the SoftEyes app icon with an eye symbol."""
    # Create a new image with a white background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Colors
    primary_color = (41, 128, 185)  # Blue
    accent_color = (52, 152, 219)   # Lighter blue
    
    # Draw outer circle
    margin = size * 0.1
    outer_radius = size // 2 - margin
    center = size // 2
    draw.ellipse(
        [center - outer_radius, center - outer_radius,
         center + outer_radius, center + outer_radius],
        fill=primary_color
    )
    
    # Draw inner eye shape
    eye_width = outer_radius * 1.4
    eye_height = outer_radius * 0.8
    eye_left = center - eye_width // 2
    eye_top = center - eye_height // 2
    draw.ellipse(
        [eye_left, eye_top,
         eye_left + eye_width, eye_top + eye_height],
        fill='white'
    )
    
    # Draw pupil
    pupil_radius = eye_height * 0.4
    draw.ellipse(
        [center - pupil_radius, center - pupil_radius,
         center + pupil_radius, center + pupil_radius],
        fill=accent_color
    )
    
    # Add highlight
    highlight_radius = pupil_radius * 0.3
    highlight_offset = pupil_radius * 0.3
    draw.ellipse(
        [center - highlight_radius + highlight_offset,
         center - highlight_radius - highlight_offset,
         center + highlight_radius + highlight_offset,
         center + highlight_radius - highlight_offset],
        fill='white'
    )
    
    return img

def save_app_icon():
    """Save the app icon in various sizes."""
    sizes = [16, 32, 48, 64, 128, 256]
    icon_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create icons directory if it doesn't exist
    icons_path = os.path.join(icon_dir, 'icons')
    os.makedirs(icons_path, exist_ok=True)
    
    # Generate and save icons in different sizes
    for size in sizes:
        icon = create_app_icon(size)
        icon_path = os.path.join(icons_path, f'app_icon_{size}.png')
        icon.save(icon_path, 'PNG')
        
        # Save 256x256 as the main icon
        if size == 256:
            icon.save(os.path.join(icon_dir, 'app_icon.png'), 'PNG')

if __name__ == '__main__':
    save_app_icon()