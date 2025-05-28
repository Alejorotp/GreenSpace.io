# main.py

import pygame
import os

# Objects
from config import SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN, ROTATION_SPEED
from spaceship import SpaceShip
from galaxy import Background
def main():
    os.environ['SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS'] = '0'

    pygame.init()

    font = pygame.font.SysFont('Arial', 72)

    pygame.display.set_caption("Persistent Fullscreen Game")

    running = True
    is_paused = False
    clock = pygame.time.Clock()

    paused_text_surface = font.render("PAUSED (Click to Resume)", True, (200, 200, 0))
    paused_text_rect = paused_text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

    game_time = 0
    circle_pos_x = SCREEN_WIDTH // 2
    circle_radius = 50

    # Object initialization
    spaceShip = SpaceShip()
    background = Background()

    while running:
        angle_changed = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                if event.key == pygame.K_p:
                    is_paused = not is_paused

            if is_paused and event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    is_paused = False

        # --- Handle continuous key presses ---
        if not is_paused:
            keys = pygame.key.get_pressed() # Get states of all keys
            angle_changed = False

            if keys[pygame.K_LEFT]:
                spaceShip.current_angle += ROTATION_SPEED
                spaceShip.current_angle %= 360
                angle_changed = True
            if keys[pygame.K_RIGHT]:
                spaceShip.current_angle -= ROTATION_SPEED
                spaceShip.current_angle %= 360
                angle_changed = True

        if not is_paused:
            game_time += 1
            circle_pos_x = (SCREEN_WIDTH // 2) + int(pygame.math.Vector2(150, 0).rotate(game_time).x)

        SCREEN.fill((30, 30, 50))

        if is_paused:
            SCREEN.blit(paused_text_surface, paused_text_rect)
        else:
            background.draw(SCREEN)
            spaceShip.draw(SCREEN, angle_changed)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == '__main__':
    main()
