# config.py

import pygame
import os

# IMPORTANT: Set SDL hints like this BEFORE pygame.init() or display.set_mode()
os.environ['SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS'] = '0'

# Initialize all Pygame modules (including display, font, etc.)
pygame.init()

# Get screen dimensions after initializing display
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h

SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)

# Constants
ROTATION_SPEED = 1
