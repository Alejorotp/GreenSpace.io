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
WORLD_RADIUS = 20000
WORLD_CENTER_X = 0
WORLD_CENTER_Y = 0

# Sun Configuration
SUN_RADIUS = 2000
SUN_COLOR = (255, 230, 100)

# Solar System Planets Configuration (the new orbiting ones)
NUM_SOLAR_SYSTEM_PLANETS = 8
MIN_ORBIT_RADIUS = SUN_RADIUS + 800
MAX_ORBIT_RADIUS = WORLD_RADIUS * 0.75

# Galaxy Generation
CELL_SIZE = 200 # For spatial grid optimization
