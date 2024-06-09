import pygame
import math
import imageio
import sys
import imageio_freeimage
from PIL import Image
import pathlib

pygame.init()

sprite = pygame.image.load(sys.argv[1])
depth_map = pygame.image.load(sys.argv[2])  # Load as grayscale
sprite_width, sprite_height = sprite.get_size()
screen = pygame.display.set_mode((sprite_width * 2, sprite_height * 2))

def rotate_point(x, y, z, angle, cx, cy, cz):
    # translate point to origin
    x -= cx
    y -= cy
    z -= cz

    # apply rotation
    cos_ang = math.cos(angle)
    sin_ang = math.sin(angle)
    x_new = x * cos_ang - z * sin_ang
    z_new = x * sin_ang + z * cos_ang

    # translate point back
    x_new += cx
    y += cy
    z_new += cz

    return x_new, y, z_new



frames = []
running = True
angle = 0
frame_count = 360

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((0, 0, 0))
    rotated_sprite = pygame.Surface((sprite_width, sprite_height), pygame.SRCALPHA)

    for y in range(sprite_height):
        for x in range(sprite_width):
            depth_value = depth_map.get_at((x, y))
            z = (depth_value.normalize()[0] + depth_value.normalize()[1] + depth_value.normalize()[2]) * 5
            if(angle > 360):
                angle = 0
            x_new, y_new, z_new = rotate_point(x, y, z, math.radians(angle), sprite_width // 2, y, 0)
            x_new = int(x_new + sprite_width // 2 - sprite_width // 2)
            y_new = int(y_new + sprite_height // 2 - sprite_height // 2)
            if 0 <= x_new < sprite_width and 0 <= y_new < sprite_height:
                rotated_sprite.set_at((x_new, y_new), sprite.get_at((x, y)))

    # fill in missing pixels only if surrounded
    for y in range(sprite_height):
        for x in range(sprite_width):
            if rotated_sprite.get_at((x, y)) == (0, 0, 0, 0):  # assuming transparency for missing pixels
                neighbors = []
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < sprite_width and 0 <= ny < sprite_height:
                            neighbor = rotated_sprite.get_at((nx, ny))
                            if neighbor != (0, 0, 0, 0):
                                neighbors.append(neighbor)

                if len(neighbors) >= 4:  # require at least 4 surrounding pixels
                    avg_color = tuple(sum(c) // len(neighbors) for c in zip(*neighbors))
                    rotated_sprite.set_at((x, y), avg_color)


    screen.blit(rotated_sprite, (sprite_width // 2, sprite_height // 2))
    angle += 1  # Increment angle for continuous rotation
    pygame.display.flip()
    if(frame_count % 10 == 0 and frame_count > 0):
        frame = pygame.surfarray.array3d(screen)
        frame = frame.swapaxes(0, 1)  # swap axes to match imageio format
        frames.append(frame)
    
    frame_count -= 1
    print(frame_count)
    #pygame.time.wait(1)

pygame.quit()
print(len(frames), frame_count)
imageio.mimwrite(uri=pathlib.Path("animation.gif"), ims=frames, format="GIF-FI", duration=0.01, loop = 0)