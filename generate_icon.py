import math
from PIL import Image, ImageDraw

# Create high-res 512x512 icon
size = (512, 512)
img = Image.new("RGBA", size, (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Draw rounded square background with gradient effect
for r in range(256, 0, -1):
    alpha = int(255 * (r / 256.0))
    # Background glow
    draw.rounded_rectangle([32, 32, 480, 480], radius=110, fill=(18, 22, 38, 255), outline=(139, 92, 246, 180), width=4)

# Draw glowing shield / lightning bolt
shield_poly = [
    (256, 90),
    (400, 150),
    (380, 320),
    (256, 420),
    (132, 320),
    (112, 150)
]
draw.polygon(shield_poly, fill=(26, 32, 58, 240), outline=(236, 72, 153, 255))

# Draw neon purple lightning bolt inside
bolt_poly = [
    (280, 140),
    (180, 260),
    (250, 260),
    (230, 370),
    (340, 230),
    (270, 230)
]
draw.polygon(bolt_poly, fill=(139, 92, 246, 255), outline=(255, 255, 255, 220))

img.save("/home/harshit/Desktop/cr-remover/cr_icon.png", "PNG")
print("Icon generated successfully!")
