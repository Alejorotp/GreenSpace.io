# spaceship.py

import pygame
import math
import random

from config import (SCREEN_WIDTH, SCREEN_HEIGHT, DESIRED_SIZE,
                    SHIP_COLLISION_PARTICLE_COUNT, SHIP_COLLISION_PARTICLE_LIFESPAN_RANGE,
                    SHIP_COLLISION_PARTICLE_SPEED_RANGE, SHIP_COLLISION_PARTICLE_COLORS,
                    SHIP_COLLISION_PARTICLE_SIZE_RANGE)

# Attempt to load and scale the spaceship sprite.
# If loading fails, a fallback polygonal shape is created.
try:
    ORIGINAL_LOADED_IMAGE = pygame.image.load("spaceshipSprite.png").convert_alpha()
    SCALED_SPACESHIP_IMAGE = pygame.transform.scale(ORIGINAL_LOADED_IMAGE, DESIRED_SIZE)
except pygame.error as e:
    print(f"Error loading or scaling spaceshipSprite.png: {e}")
    SCALED_SPACESHIP_IMAGE = pygame.Surface(DESIRED_SIZE, pygame.SRCALPHA)
    SCALED_SPACESHIP_IMAGE.fill((0,0,0,0)) # Fallback uses transparent background.
    # Draw a simple triangle as the fallback sprite.
    pygame.draw.polygon(SCALED_SPACESHIP_IMAGE, (255, 255, 255),
                        [(DESIRED_SIZE[0] // 2, 10), # Top point.
                         (10, DESIRED_SIZE[1] - 10), # Bottom-left point.
                         (DESIRED_SIZE[0] - 10, DESIRED_SIZE[1] - 10)]) # Bottom-right point.

class SpaceShip:
    """
    Manages the player's spaceship, including its physics, rendering,
    and particle effects for thrust and destruction.
    """
    def __init__(self, initial_x, initial_y):
        self.x = float(initial_x)  # World x-coordinate.
        self.y = float(initial_y)  # World y-coordinate.

        # Velocity components:
        # vx_0, vy_0: current persistent velocity vector.
        # vx_1, vy_1: velocity change to be applied in the current frame due to thrust.
        self.vx_0 = 0.0
        self.vy_0 = 0.0
        self.vx_1 = 0.0
        self.vy_1 = 0.0

        self.original_image = SCALED_SPACESHIP_IMAGE # Base scaled image of the spaceship.
        self.image_to_draw = self.original_image    # Current image to draw (potentially rotated).
        self.current_angle = 90.0  # Spaceship's orientation in degrees (90.0 conventionally means facing 'up').

        self.rect = self.image_to_draw.get_rect(center=(self.x, self.y)) # Pygame Rect for rendering position.

        self.is_thrusting = False    # True if the ship is currently thrusting.
        self.particles = []          # List to store active particles (for thrust and explosion).
        self.particle_emit_cooldown = 0 # Cooldown timer to regulate thrust particle emission rate.
        self.PARTICLE_EMIT_DELAY = 2    # Delay in frames between consecutive thrust particle emissions.

        self.alive = True            # True if the spaceship is operational, False if destroyed.

    def _emit_particles(self):
        """Generates thrust particles when the ship is accelerating."""
        if not self.is_thrusting or not self.alive:
            return

        self.particle_emit_cooldown -= 1
        if self.particle_emit_cooldown > 0:
            return
        self.particle_emit_cooldown = self.PARTICLE_EMIT_DELAY

        num_particles_to_emit = random.randint(15, 31)
        emit_offset_distance = DESIRED_SIZE[1] / 4.5 # Distance from ship's center to particle emission point.
        emit_direction_rad = math.radians(self.current_angle) # Ship's current facing direction.

        # Calculate particle spawn point, offset from ship's center, appearing from the rear.
        # The -1 multiplier for cos and +1 for sin (with Pygame's Y-down) positions particles behind the ship.
        base_emit_x = self.x + -1 * emit_offset_distance * math.cos(emit_direction_rad)
        base_emit_y = self.y + emit_offset_distance * math.sin(emit_direction_rad)

        for _ in range(num_particles_to_emit):
            particle_angle_offset = random.uniform(-25, 25) # Introduces a spread to the particle stream.
            # Particles are emitted in the general direction the ship is facing, with some spread.
            particle_actual_direction_rad = math.radians(self.current_angle + particle_angle_offset)
            particle_speed = random.uniform(1.5, 3.5)
            inherit_factor = 0.3 # Factor of ship's current velocity inherited by particles.

            particle_vx = (particle_speed * math.cos(particle_actual_direction_rad)) + self.vx_0 * inherit_factor
            particle_vy = (particle_speed * math.sin(particle_actual_direction_rad)) + self.vy_0 * inherit_factor

            lifespan = random.randint(15, 40) # Particle lifespan in frames.
            size = random.randint(2, 5)       # Particle size in pixels.
            color_choice = random.choice([(255, 100, 0), (255, 150, 0), (255, 200, 50), (255, 50, 0)]) # Orange/Yellow hues.

            # Final particle spawn position with a slight random jitter.
            px = base_emit_x + random.uniform(-5, 5)
            py = base_emit_y + random.uniform(-5, 5)
            self.particles.append({
                'world_x': px, 'world_y': py, 'vx': particle_vx, 'vy': particle_vy,
                'lifespan': lifespan, 'max_lifespan': lifespan, # max_lifespan for effects like fading.
                'color': color_choice, 'size': size, 'type': 'thrust'
            })

    def explode(self):
        """Handles the ship's explosion, creating numerous particles."""
        if not self.alive: return # Prevent multiple explosion calls.
        self.alive = False
        self.is_thrusting = False # Stop thrusting effects.

        for _ in range(SHIP_COLLISION_PARTICLE_COUNT):
            angle_rad = random.uniform(0, 2 * math.pi) # Particles scatter in all directions.
            speed = random.uniform(SHIP_COLLISION_PARTICLE_SPEED_RANGE[0], SHIP_COLLISION_PARTICLE_SPEED_RANGE[1])
            particle_vx = math.cos(angle_rad) * speed
            particle_vy = math.sin(angle_rad) * speed
            lifespan = random.randint(SHIP_COLLISION_PARTICLE_LIFESPAN_RANGE[0], SHIP_COLLISION_PARTICLE_LIFESPAN_RANGE[1])
            size = random.randint(SHIP_COLLISION_PARTICLE_SIZE_RANGE[0], SHIP_COLLISION_PARTICLE_SIZE_RANGE[1])
            color_choice = random.choice(SHIP_COLLISION_PARTICLE_COLORS)

            self.particles.append({
                'world_x': self.x + random.uniform(-5,5), # Spawn particles around the ship's last position.
                'world_y': self.y + random.uniform(-5,5),
                'vx': particle_vx, 'vy': particle_vy,
                'lifespan': lifespan, 'max_lifespan': lifespan,
                'color': color_choice, 'size': size, 'type': 'explosion'
            })

    def update(self):
        """Updates the spaceship's state including physics and particles each frame."""
        if self.alive:
            if self.is_thrusting:
                self._emit_particles()
            else:
                self.particle_emit_cooldown = 0 # Reset cooldown if not thrusting.

            # Apply thrust acceleration to current velocity.
            self.vx_0 += self.vx_1
            self.vy_0 += self.vy_1

            # Apply friction/drag to gradually slow down the ship.
            self.vx_0 *= 0.99
            self.vy_0 *= 0.99

            # Update position based on velocity.
            self.x += self.vx_0
            self.y -= self.vy_0 # Positive vy_0 moves ship 'up' (decreases y-coordinate in Pygame screen sense).

            # Reset per-frame thrust acceleration; it's applied anew each frame based on input.
            self.vx_1 = 0.0
            self.vy_1 = 0.0

        # Update all active particles (both thrust and explosion types).
        new_particles = []
        for p in self.particles:
            p['world_x'] += p['vx']
            p['world_y'] += p['vy'] # Positive vy makes particle move 'down' (increases y-coordinate).
            p['lifespan'] -= 1
            if p['lifespan'] > 0:
                new_particles.append(p)
        self.particles = new_particles

    def draw(self, surface, camera_x, camera_y):
        """Draws the spaceship and its particles onto the given surface, adjusted for camera."""
        # Draw all active particles.
        for p in self.particles:
            # Convert particle world to screen coordinates.
            screen_px = p['world_x'] - camera_x
            screen_py = p['world_y'] - camera_y

            # Particle size may decrease over its lifespan for a fading effect.
            current_size = int(p['size'] * (p['lifespan'] / p['max_lifespan']))
            if current_size < 1: current_size = 1 # Ensure minimum size of 1 pixel.

            # Basic culling for particles: only draw if on or near the screen.
            if screen_px + current_size > 0 and screen_px - current_size < SCREEN_WIDTH and \
               screen_py + current_size > 0 and screen_py - current_size < SCREEN_HEIGHT:
                pygame.draw.rect(surface, p['color'],
                                 (int(screen_px - current_size / 2),
                                  int(screen_py - current_size / 2),
                                  current_size, current_size))

        if self.alive:
            # Rotate the ship's image based on its current angle.
            # The '- 90' offset is used to align the sprite's visual 'up' (if designed pointing right)
            # or to correct for angle conventions if current_angle = 0 is right.
            self.image_to_draw = pygame.transform.rotate(self.original_image, self.current_angle - 90)

            screen_draw_x = self.x - camera_x
            screen_draw_y = self.y - camera_y

            # Update the drawing rectangle's center for accurate blitting post-rotation.
            self.rect = self.image_to_draw.get_rect(center=(screen_draw_x, screen_draw_y))
            surface.blit(self.image_to_draw, self.rect)

    def get_collider_world(self):
        """
        Returns a pygame.Rect in world coordinates for collision detection.
        The collider is intentionally made smaller than the visual sprite for gameplay forgiveness.
        """
        collider_width = DESIRED_SIZE[0] * 0.7 # 70% of the visual width.
        collider_height = DESIRED_SIZE[1] * 0.7# 70% of the visual height.
        # Center the collider rect on ship's world position.
        return pygame.Rect(
            self.x - collider_width / 2.0,
            self.y - collider_height / 2.0,
            collider_width,
            collider_height
        )
