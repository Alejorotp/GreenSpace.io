# spaceship.py

import pygame
import math
import random

# Import DESIRED_SIZE from config
from config import SCREEN_WIDTH, SCREEN_HEIGHT, WORLD_RADIUS, WORLD_CENTER_X, WORLD_CENTER_Y, DESIRED_SIZE

try:
    ORIGINAL_LOADED_IMAGE = pygame.image.load("spaceshipSprite.png").convert_alpha()
    SCALED_SPACESHIP_IMAGE = pygame.transform.scale(ORIGINAL_LOADED_IMAGE, DESIRED_SIZE)
except pygame.error as e:
    print(f"Error loading or scaling spaceshipSprite.png: {e}")
    SCALED_SPACESHIP_IMAGE = pygame.Surface(DESIRED_SIZE, pygame.SRCALPHA)
    SCALED_SPACESHIP_IMAGE.fill((0,0,0,0))
    pygame.draw.polygon(SCALED_SPACESHIP_IMAGE, (255, 255, 255),
                        [(DESIRED_SIZE[0] // 2, 10),
                         (10, DESIRED_SIZE[1] - 10),
                         (DESIRED_SIZE[0] - 10, DESIRED_SIZE[1] - 10)])

class SpaceShip:
    # Represents the player's spaceship.
    def __init__(self, initial_x, initial_y): # Accept initial position
        self.x = float(initial_x)
        self.y = float(initial_y)

        self.vx_0 = 0.0
        self.vy_0 = 0.0
        self.vx_1 = 0.0
        self.vy_1 = 0.0

        self.original_image = SCALED_SPACESHIP_IMAGE
        self.image_to_draw = self.original_image
        self.current_angle = 90.0

        self.rect = self.image_to_draw.get_rect(center=(self.x, self.y))

        self.is_thrusting = False
        self.particles = []
        self.particle_emit_cooldown = 0
        self.PARTICLE_EMIT_DELAY = 2

    # Emits particles when the ship is thrusting.
    def _emit_particles(self):
        if not self.is_thrusting:
            return

        self.particle_emit_cooldown -= 1
        if self.particle_emit_cooldown > 0:
            return

        self.particle_emit_cooldown = self.PARTICLE_EMIT_DELAY
        num_particles_to_emit = random.randint(15, 31)
        emit_offset_distance = DESIRED_SIZE[1] / 4.5

        emit_direction_rad = math.radians(self.current_angle)

        base_emit_x = self.x + -1 * emit_offset_distance * math.cos(emit_direction_rad)
        base_emit_y = self.y + emit_offset_distance * math.sin(emit_direction_rad)

        for _ in range(num_particles_to_emit):
            particle_angle_offset = random.uniform(-25, 25)
            particle_actual_direction_rad = math.radians(self.current_angle + particle_angle_offset)
            particle_speed = random.uniform(1.5, 3.5)
            inherit_factor = 0.3
            particle_vx = (particle_speed * math.cos(particle_actual_direction_rad)) + self.vx_0 * inherit_factor
            particle_vy = (particle_speed * math.sin(particle_actual_direction_rad)) + self.vy_0 * inherit_factor

            lifespan = random.randint(15, 40)
            size = random.randint(2, 5)
            color_choice = random.choice([(255, 100, 0), (255, 150, 0), (255, 200, 50), (255, 50, 0)])

            px = base_emit_x + random.uniform(-5, 5)
            py = base_emit_y + random.uniform(-5, 5)

            self.particles.append({
                'world_x': px, 'world_y': py,
                'vx': particle_vx, 'vy': particle_vy,
                'lifespan': lifespan, 'max_lifespan': lifespan,
                'color': color_choice, 'size': size
            })

    # Updates the spaceship's state.
    def update(self):
        if self.is_thrusting:
            self._emit_particles()
        else:
            self.particle_emit_cooldown = 0

        new_particles = []
        for p in self.particles:
            p['world_x'] += p['vx']
            p['world_y'] += p['vy']
            p['lifespan'] -= 1
            if p['lifespan'] > 0:
                new_particles.append(p)
        self.particles = new_particles

        self.vx_0 += self.vx_1
        self.vy_0 += self.vy_1

        self.x += self.vx_0
        self.y -= self.vy_0

        self.vx_0 *= 0.99
        self.vy_0 *= 0.99

        self.vx_1 = 0.0
        self.vy_1 = 0.0

        dist_from_world_center = math.hypot(self.x - WORLD_CENTER_X, self.y - WORLD_CENTER_Y)
        effective_world_radius = WORLD_RADIUS - max(DESIRED_SIZE) / 2
        if dist_from_world_center > effective_world_radius:
            if dist_from_world_center > 0:
                norm_x = (self.x - WORLD_CENTER_X) / dist_from_world_center
                norm_y = (self.y - WORLD_CENTER_Y) / dist_from_world_center
                self.x = WORLD_CENTER_X + norm_x * effective_world_radius
                self.y = WORLD_CENTER_Y + norm_y * effective_world_radius
                self.vx_0 *= -0.5
                self.vy_0 *= -0.5

    # Draws the spaceship and its particles.
    def draw(self, surface, camera_x, camera_y):
        for p in self.particles:
            screen_px = p['world_x'] - camera_x
            screen_py = p['world_y'] - camera_y
            current_size = int(p['size'] * (p['lifespan'] / p['max_lifespan']))
            if current_size < 1: current_size = 1

            if screen_px + current_size > 0 and screen_px - current_size < SCREEN_WIDTH and \
               screen_py + current_size > 0 and screen_py - current_size < SCREEN_HEIGHT:
                pygame.draw.rect(surface, p['color'],
                                 (int(screen_px - current_size / 2),
                                  int(screen_py - current_size / 2),
                                  current_size, current_size))

        self.image_to_draw = pygame.transform.rotate(self.original_image, self.current_angle - 90)
        screen_draw_x = self.x - camera_x
        screen_draw_y = self.y - camera_y
        self.rect = self.image_to_draw.get_rect(center=(screen_draw_x, screen_draw_y))
        surface.blit(self.image_to_draw, self.rect)

    # Returns a pygame.Rect in world coordinates for collision detection.
    def get_collider_world(self):
        # Centered on the spaceship's world coordinates.
        collider_width = DESIRED_SIZE[0] * 0.8 # Slightly smaller than visual for forgiveness
        collider_height = DESIRED_SIZE[1] * 0.8
        return pygame.Rect(
            self.x - collider_width / 2,
            self.y - collider_height / 2,
            collider_width,
            collider_height
        )
