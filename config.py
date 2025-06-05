# config.py

import pygame
import os

# Prevents the game window from minimizing when focus is lost (e.g., alt-tabbing).
os.environ['SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS'] = '0'

pygame.init()

# Dynamically get current screen dimensions for fullscreen mode.
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h

# Initialize the main screen surface in fullscreen.
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)

# Gameplay Constants
ROTATION_SPEED = 2          # Angular speed of the spaceship in degrees per frame.
THRUST_MAGNITUDE = 0.2      # Acceleration magnitude when the spaceship is thrusting.
DESIRED_SIZE = (100, 100)   # Target scaled dimensions for the spaceship sprite.

# World Configuration
WORLD_RADIUS = 18000        # Radius of the playable game world.
WORLD_CENTER_X = 0          # World center X-coordinate.
WORLD_CENTER_Y = 0          # World center Y-coordinate.

# Sun Configuration
SUN_RADIUS = 6000           # Radius of the sun.
SUN_COLOR = (255, 230, 100) # Color of the sun.

# Solar System Planets Configuration
NUM_SOLAR_SYSTEM_PLANETS = 3 # Number of planets to generate in the solar system.
MIN_ORBIT_RADIUS = SUN_RADIUS + 2000 # Minimum orbit radius for planets, relative to sun's edge.
MAX_ORBIT_RADIUS = WORLD_RADIUS * 0.85 # Maximum orbit radius for planets, within world bounds.

# Galaxy Generation
CELL_SIZE = 200             # Size of cells in the spatial grid for rendering optimization.

# Garbage Configuration
NUM_GENERAL_GARBAGE = 50       # Number of garbage items to scatter generally in space.
GARBAGE_PER_PLANET_CLUSTER = 50 # Number of garbage items to cluster around each solar system planet.
PLANET_GARBAGE_ZONE_RADIUS_FACTOR = 3.0 # Factor of planet's radius to define its garbage cluster zone.
MIN_DIST_GARBAGE_FROM_PLANET_SURFACE = 50 # Minimum distance garbage should spawn from a planet's surface.
GARBAGE_SIZE_RANGE = (40, 120)  # Range (min, max) for the size of garbage items.
GARBAGE_SPRITE_FILE = "garbageSprite.png" # Filename for the garbage sprite.
SHIP_MAGNET_RANGE = 800         # Range of the spaceship's garbage collection magnet.
BASE_MAGNET_STRENGTH = 2000000    # Base strength of the magnet's pull.
MIN_GARBAGE_ATTRACTION_SPEED_FACTOR = 0.1 # Minimum speed factor for garbage under magnet influence.

# Spaceship Collision / Game Over Effects
SHIP_COLLISION_PARTICLE_COUNT = 1500    # Number of particles in the ship's explosion.
SHIP_COLLISION_PARTICLE_LIFESPAN_RANGE = (70, 140) # Lifespan range for explosion particles.
SHIP_COLLISION_PARTICLE_SPEED_RANGE = (2, 7)     # Speed range for explosion particles.
SHIP_COLLISION_PARTICLE_SIZE_RANGE = (2, 6)      # Size range for explosion particles.
SHIP_COLLISION_PARTICLE_COLORS = [(255,0,0), (255,100,0), (200,200,200), (255,255,100)] # Possible colors for explosion particles.
