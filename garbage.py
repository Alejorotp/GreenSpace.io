# garbage.py

import pygame
import random
import math
from config import GARBAGE_ITEM_SIZE_RANGE, GARBAGE_ITEM_COLOR, SCREEN_WIDTH, SCREEN_HEIGHT

class Garbage:
    # Represents a piece of collectable garbage.
    def __init__(self, world_x, world_y):
        self.world_x = float(world_x)
        self.world_y = float(world_y)

        self.size = random.randint(GARBAGE_ITEM_SIZE_RANGE[0], GARBAGE_ITEM_SIZE_RANGE[1])

        # Slightly vary color for visual diversity
        color_r_offset = random.randint(-10, 10)
        color_g_offset = random.randint(-10, 10)
        color_b_offset = random.randint(-10, 10)
        self.color = (
            max(0, min(255, GARBAGE_ITEM_COLOR[0] + color_r_offset)),
            max(0, min(255, GARBAGE_ITEM_COLOR[1] + color_g_offset)),
            max(0, min(255, GARBAGE_ITEM_COLOR[2] + color_b_offset))
        )

        # For simplicity, garbage is a circle. Could be a sprite or complex shape.
        # No pre-rendered surface needed if just drawing a circle.
        self.rect = pygame.Rect(self.world_x - self.size // 2, self.world_y - self.size // 2, self.size, self.size)
        self.type = 'garbage' # For identification

    # Draws the garbage item on the screen if visible.
    def draw(self, surface, camera_x, camera_y):
        screen_x = self.world_x - camera_x
        screen_y = self.world_y - camera_y

        # Culling: Check if the garbage item is within screen bounds
        if screen_x + self.size < 0 or screen_x - self.size > SCREEN_WIDTH or \
           screen_y + self.size < 0 or screen_y - self.size > SCREEN_HEIGHT:
            return

        pygame.draw.circle(surface, self.color, (int(screen_x), int(screen_y)), self.size // 2)

    # Returns a pygame.Rect in world coordinates for collision detection.
    def get_collider(self):
        # Collider is a bit larger than visual for easier collection
        collider_size = self.size * 1.1
        return pygame.Rect(
            self.world_x - collider_size / 2,
            self.world_y - collider_size / 2,
            collider_size,
            collider_size
        )
