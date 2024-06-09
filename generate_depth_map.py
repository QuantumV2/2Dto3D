from PIL import Image, ImageFilter
import sys

sprite = Image.open(sys.argv[1]).convert('L')  # Convert to grayscale
sprite = sprite.filter(ImageFilter.GaussianBlur(radius=2))  # Apply Gaussian Blur

width, height = sprite.size
depth_map = Image.new('L', (width, height))

for y in range(height):
    for x in range(width):
        pixel_value = sprite.getpixel((x, y))
        depth_value = pixel_value  # Invert to make bright pixels higher
        depth_map.putpixel((x, y), depth_value)

depth_map.save('depth.png')