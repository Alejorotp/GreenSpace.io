# garbage.py (Modified __init__ method)

import pygame
import random
import math
from config import (GARBAGE_SIZE_RANGE, GARBAGE_SPRITE_FILE, SCREEN_WIDTH, SCREEN_HEIGHT,
                    SHIP_MAGNET_RANGE, BASE_MAGNET_STRENGTH, MIN_GARBAGE_ATTRACTION_SPEED_FACTOR)

try:
    ORIGINAL_GARBAGE_IMAGE = pygame.image.load(GARBAGE_SPRITE_FILE).convert_alpha()
except pygame.error as e:
    print(f"Error loading {GARBAGE_SPRITE_FILE}: {e}")
    ORIGINAL_GARBAGE_IMAGE = pygame.Surface((50, 50), pygame.SRCALPHA)
    pygame.draw.circle(ORIGINAL_GARBAGE_IMAGE, (100, 100, 100), (25, 25), 25)

class Garbage:
    """
    Represents a single piece of collectable space garbage.
    It can be attracted to the spaceship by its magnet.
    """
    def __init__(self, world_x, world_y, loaded_size=None): # Added loaded_size parameter
        self.world_x = float(world_x)
        self.world_y = float(world_y)

        if loaded_size is not None:
            self.size = loaded_size  # Use provided size if loading
        else:
            # Otherwise, determine size randomly as before for new garbage
            self.size = random.randint(GARBAGE_SIZE_RANGE[0], GARBAGE_SIZE_RANGE[1])

        self.image = pygame.transform.smoothscale(ORIGINAL_GARBAGE_IMAGE, (self.size, self.size))
        self.rect = self.image.get_rect(center=(self.world_x, self.world_y))
        self.type = 'garbage'

    def update(self, ship_x, ship_y, dt):
        """
        Updates the garbage item's state, primarily handling its attraction
        towards the spaceship if within magnet range.
        """
        dx = ship_x - self.world_x
        dy = ship_y - self.world_y
        dist_sq = dx*dx + dy*dy

        if dist_sq < SHIP_MAGNET_RANGE**2 and dist_sq > 1e-6:
            dist = math.sqrt(dist_sq)
            size_range_delta = GARBAGE_SIZE_RANGE[1] - GARBAGE_SIZE_RANGE[0]
            if size_range_delta < 1e-5: size_range_delta = 1e-5
            size_factor_normalized = (GARBAGE_SIZE_RANGE[1] - self.size) / size_range_delta
            size_factor_normalized = max(0.0, min(1.0, size_factor_normalized))
            effective_strength_factor = (MIN_GARBAGE_ATTRACTION_SPEED_FACTOR + \
                                        (1.0 - MIN_GARBAGE_ATTRACTION_SPEED_FACTOR) * size_factor_normalized)
            target_speed_pps = (BASE_MAGNET_STRENGTH / (self.size * (dist + 10.0))) * effective_strength_factor
            target_speed_pps = min(target_speed_pps, SHIP_MAGNET_RANGE)
            move_dist_this_frame = target_speed_pps * dt
            self.world_x += (dx / dist) * move_dist_this_frame
            self.world_y += (dy / dist) * move_dist_this_frame
            self.rect.center = (self.world_x, self.world_y)

    def draw(self, surface, camera_x, camera_y):
        """Draws the garbage item on the screen if it's visible, adjusted for camera."""
        screen_x = self.world_x - camera_x
        screen_y = self.world_y - camera_y
        if screen_x + self.size < 0 or screen_x - self.size > SCREEN_WIDTH or \
           screen_y + self.size < 0 or screen_y - self.size > SCREEN_HEIGHT:
            return
        draw_rect = self.image.get_rect(center=(int(screen_x), int(screen_y)))
        surface.blit(self.image, draw_rect)

    def get_collider(self):
        """
        Returns a pygame.Rect in world coordinates for collision detection
        with the spaceship (e.g., for collection).
        Collider is smaller for harder recollection.
        """
        return pygame.Rect(
            self.world_x - self.size / 4.0, # Centered, but half width/height
            self.world_y - self.size / 4.0,
            self.size / 2.0,
            self.size / 2.0
        )
