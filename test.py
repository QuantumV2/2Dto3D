import pygame
import math
import imageio
import sys
from PIL import Image
import pathlib

from numba import jit, cuda 

pygame.init()

sprite = pygame.image.load(sys.argv[1])
depth_map = pygame.image.load(sys.argv[2])  # Load as grayscale
sprite_width, sprite_height = sprite.get_size()
screen = pygame.display.set_mode((sprite_width * 2, sprite_height * 2))
fillinpixels = (sys.argv[3] == 'True') if len(sys.argv) > 3 else False

@jit(target_backend='cuda')  
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

@jit(target_backend='cuda')  
def rotate_calc(depth_value_normal, x,y,angle,sprite_width,sprite_height):
    z = (depth_value_normal[0] + depth_value_normal[1] + depth_value_normal[2]) * 10
    if(angle > 360):
        angle = 0
    x_new, y_new, z_new = rotate_point(x, y, z, math.radians(angle), sprite_width // 2, y, 0)
    x_new = int(x_new + sprite_width // 2 - sprite_width // 2)
    y_new = int(y_new + sprite_height // 2 - sprite_height // 2)
    return x_new, y_new, z_new

@jit(target_backend='cuda')  
def loop_neighbors(x, y):
    nxy = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx = x + dx
            ny = y + dy
            nxy.append([nx, ny])
    return nxy

frames = []
running = True
angle = 0
frame_count = 360

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((0, 0, 0))
    rotated_sprite = pygame.Surface((sprite_width, sprite_height))


    for y in range(sprite_height):
        for x in range(sprite_width):
            depth_value = depth_map.get_at((x, y))
            depth_value_normal = depth_value.normalize()

            if(depth_value_normal != [0.0,0.0,0.0,1.0] and depth_value_normal != [0.0,0.0,0.0,0.0]):
                x_new, y_new, z_new = rotate_calc(depth_value_normal,x,y,angle,sprite_width, sprite_height)
                if 0 <= x_new < sprite_width and 0 <= y_new < sprite_height:
                    rotated_sprite.set_at((x_new, y_new), sprite.get_at((x, y)))

    if fillinpixels:
        for y in range(sprite_height):
            for x in range(sprite_width):
                #print(rotated_sprite.get_at((x, y)))
                if rotated_sprite.get_at((x, y)) == (0, 0, 0, 255):  # assuming transparency for missing pixels
                    neighbors = []
                    nxy= loop_neighbors(x,y)
                    for i in range(len(nxy) - 1):
                        nx = nxy[i][0]
                        ny = nxy[i][1]
                        if 0 <= nx < sprite_width and 0 <= ny < sprite_height:
                            neighbor = rotated_sprite.get_at((nx, ny))
                            #print(neighbor)
                            if neighbor != (0, 0, 0, 255):
                                neighbors.append(neighbor)

                    if len(neighbors) >= 4:  # require at least 4 surrounding pixels
                        
                        avg_color = tuple(sum(c) // len(neighbors) for c in zip(*neighbors))
                        rotated_sprite.set_at((x, y), avg_color)


    screen.blit(rotated_sprite, (sprite_width // 2, sprite_height // 2))
    angle += 1  # Increment angle for continuous rotation
    pygame.display.flip()
    if(frame_count % 5 == 0 and frame_count > 0):
        frame = pygame.surfarray.array3d(screen)
        frame = frame.swapaxes(0, 1)  # swap axes to match imageio format
        frames.append(frame)
    
    frame_count -= 1
    #pygame.time.wait(1)

pygame.quit()
imageio.mimwrite(uri=pathlib.Path("animation.gif"), ims=frames, format="GIF", duration=0.01, loop = 0)