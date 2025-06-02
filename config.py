# config.py

import pygame
import os

# So it does not close when alt tabbing
os.environ['SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS'] = '0'

# Initialize Pygame
pygame.init()

# Get screen dimensions after initializing display
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h

# Initialize screeen
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)

# Constants
ROTATION_SPEED = 2
THRUST_MAGNITUDE = 0.3
DESIRED_SIZE = (100, 100) # Spaceship's desired scaled size

# World Configuration
WORLD_RADIUS = 60000
WORLD_CENTER_X = 0
WORLD_CENTER_Y = 0

# Sun Configuration
SUN_RADIUS = 20000
SUN_COLOR = (255, 230, 100)

# Solar System Planets Configuration
NUM_SOLAR_SYSTEM_PLANETS = 8
MIN_ORBIT_RADIUS = SUN_RADIUS + 2000
MAX_ORBIT_RADIUS = WORLD_RADIUS * 0.85

# Galaxy Generation
CELL_SIZE = 200 # For spatial grid optimization

# Garbage Configuration
NUM_GENERAL_GARBAGE = 300 # Number of garbage items spread randomly in the galaxy
GARBAGE_PER_PLANET_CLUSTER = 150 # Number of garbage items per planet
PLANET_GARBAGE_ZONE_RADIUS_FACTOR = 3.0 # Multiplier of planet radius for garbage spawn zone
MIN_DIST_GARBAGE_FROM_PLANET_SURFACE = 50 # Min distance from planet surface
GARBAGE_ITEM_SIZE_RANGE = (8, 20) # Min and max visual size for a garbage item
GARBAGE_ITEM_COLOR = (0, 255, 0) # Base color for garbage items
