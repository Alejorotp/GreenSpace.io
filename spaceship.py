# spaceship.py

import pygame

from config import SCREEN_WIDTH, SCREEN_HEIGHT

IMAGE = pygame.image.load("spaceshipSprite.png").convert_alpha()
DESIRED_SIZE = (100, 100)
IMAGE = pygame.transform.scale(IMAGE, DESIRED_SIZE)

class SpaceShip:
    def __init__(self):
        self.size = 20
        self.x = SCREEN_WIDTH - self.size
        self.y = SCREEN_HEIGHT - self.size
        self.vx = 0
        self.vy = 0
        self.original_image = IMAGE
        self.image = self.original_image
        self.sprite = self.image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.current_angle = 0

    def draw(self, surface, angle_changed):
        if (angle_changed):
            self.image = pygame.transform.rotate(self.original_image, self.current_angle)
            self.sprite = self.image.get_rect(center=self.sprite.center)
        surface.blit(self.image, self.sprite)
