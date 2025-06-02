# main.py

import pygame
import os
import math
import random

from config import (SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN, ROTATION_SPEED, THRUST_MAGNITUDE,
                    WORLD_RADIUS, WORLD_CENTER_X, WORLD_CENTER_Y,
                    SUN_RADIUS, SUN_COLOR, DESIRED_SIZE)
from spaceship import SpaceShip
from galaxy import Background

# --- Game States ---
STATE_READY_TO_START = 0
STATE_PLAYING = 1
STATE_GAME_OVER = 2
STATE_WIN = 3

# --- UI Constants ---
UI_FONT_SIZE = 50
UI_TEXT_COLOR = (220, 220, 255)
UI_TEXT_HOVER_COLOR = (255, 255, 150)
SCORE_TEXT_COLOR = (200, 255, 200) # Color for the score display

# --- Minimap Variables ---
MINIMAP_SIZE_RADIUS = 80
MINIMAP_MARGIN = 15
MINIMAP_CENTER_X_ON_SCREEN = SCREEN_WIDTH - MINIMAP_SIZE_RADIUS - MINIMAP_MARGIN
MINIMAP_CENTER_Y_ON_SCREEN = MINIMAP_SIZE_RADIUS + MINIMAP_MARGIN
MINIMAP_BG_COLOR = (20, 20, 40, 180)
MINIMAP_BORDER_COLOR = (100, 100, 120, 200)
SHIP_MINIMAP_COLOR = (255, 255, 0)
GARBAGE_MINIMAP_COLOR = (0, 255, 0, 200)

# Helper function to find a safe spawn position for the spaceship.
def get_safe_spawn_position(background_obj, ship_radius_approx):
    max_attempts = 100
    for attempt in range(max_attempts):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(WORLD_RADIUS * 0.2, WORLD_RADIUS * 0.6) # Spawn somewhat away from center
        spawn_x = WORLD_CENTER_X + dist * math.cos(angle)
        spawn_y = WORLD_CENTER_Y + dist * math.sin(angle)

        if hasattr(background_obj, 'sun_data') and background_obj.sun_data:
            sun_dist = math.hypot(spawn_x - background_obj.sun_data['world_pos'][0],
                                  spawn_y - background_obj.sun_data['world_pos'][1])
            if sun_dist < background_obj.sun_data['radius'] + ship_radius_approx + 100: # Increased buffer
                continue

        safe_from_planets = True
        if hasattr(background_obj, 'solar_system_planets'):
            for planet in background_obj.solar_system_planets:
                # Using current planet positions for check; initial would be more robust but complex
                planet_dist = math.hypot(spawn_x - planet['world_pos'][0],
                                          spawn_y - planet['world_pos'][1])
                if planet_dist < planet['radius'] + ship_radius_approx + 100: # Increased buffer
                    safe_from_planets = False
                    break
        if safe_from_planets:
            return float(spawn_x), float(spawn_y)

    print("Warning: Could not find a perfectly safe spawn point. Spawning near world center with offset.")
    return float(WORLD_CENTER_X + random.uniform(SUN_RADIUS + 200, SUN_RADIUS + 400)), \
           float(WORLD_CENTER_Y + random.uniform(SUN_RADIUS + 200, SUN_RADIUS + 400))

# Draws the minimap on the screen.
def draw_minimap(surface, game_ship, game_background, camera_x, camera_y, current_garbage_list):
    minimap_render_surface = pygame.Surface((MINIMAP_SIZE_RADIUS * 2, MINIMAP_SIZE_RADIUS * 2), pygame.SRCALPHA)
    minimap_render_surface.fill((0,0,0,0))
    pygame.draw.circle(minimap_render_surface, MINIMAP_BG_COLOR, (MINIMAP_SIZE_RADIUS, MINIMAP_SIZE_RADIUS), MINIMAP_SIZE_RADIUS)
    pygame.draw.circle(minimap_render_surface, MINIMAP_BORDER_COLOR, (MINIMAP_SIZE_RADIUS, MINIMAP_SIZE_RADIUS), MINIMAP_SIZE_RADIUS, 2)
    scale_to_minimap = float(MINIMAP_SIZE_RADIUS) / WORLD_RADIUS

    # Draw some garbage items on minimap (can be slow if too many)
    for i, G_item in enumerate(current_garbage_list):
        #if i % 50 == 0: # Draw 1 in 50 garbage items to reduce clutter
        g_world_x, g_world_y = G_item.world_x, G_item.world_y
        g_minimap_x = MINIMAP_SIZE_RADIUS + (g_world_x - WORLD_CENTER_X) * scale_to_minimap
        g_minimap_y = MINIMAP_SIZE_RADIUS + (g_world_y - WORLD_CENTER_Y) * scale_to_minimap
        if math.hypot(g_minimap_x - MINIMAP_SIZE_RADIUS, g_minimap_y - MINIMAP_SIZE_RADIUS) <= MINIMAP_SIZE_RADIUS:
            pygame.draw.circle(minimap_render_surface, GARBAGE_MINIMAP_COLOR, (int(g_minimap_x), int(g_minimap_y)), 1)

    if hasattr(game_background, 'sun_data') and game_background.sun_data:
        sun_world_x, sun_world_y = game_background.sun_data['world_pos']
        sun_minimap_x = MINIMAP_SIZE_RADIUS + (sun_world_x - WORLD_CENTER_X) * scale_to_minimap
        sun_minimap_y = MINIMAP_SIZE_RADIUS + (sun_world_y - WORLD_CENTER_Y) * scale_to_minimap
        sun_minimap_radius = max(1, int(game_background.sun_data['radius'] * scale_to_minimap))
        if math.hypot(sun_minimap_x - MINIMAP_SIZE_RADIUS, sun_minimap_y - MINIMAP_SIZE_RADIUS) <= MINIMAP_SIZE_RADIUS + sun_minimap_radius:
            pygame.draw.circle(minimap_render_surface, game_background.sun_data['color'], (int(sun_minimap_x), int(sun_minimap_y)), sun_minimap_radius)
    if hasattr(game_background, 'solar_system_planets'):
        for planet_data in game_background.solar_system_planets:
            world_pos_x, world_pos_y = planet_data['world_pos']
            minimap_x = MINIMAP_SIZE_RADIUS + (world_pos_x - WORLD_CENTER_X) * scale_to_minimap
            minimap_y = MINIMAP_SIZE_RADIUS + (world_pos_y - WORLD_CENTER_Y) * scale_to_minimap
            planet_minimap_radius = max(1, int(planet_data['radius'] * scale_to_minimap))
            if math.hypot(minimap_x - MINIMAP_SIZE_RADIUS, minimap_y - MINIMAP_SIZE_RADIUS) <= MINIMAP_SIZE_RADIUS + planet_minimap_radius:
                pygame.draw.circle(minimap_render_surface, planet_data['color'], (int(minimap_x), int(minimap_y)), planet_minimap_radius)

    ship_minimap_x = MINIMAP_SIZE_RADIUS + (game_ship.x - WORLD_CENTER_X) * scale_to_minimap
    ship_minimap_y = MINIMAP_SIZE_RADIUS + (game_ship.y - WORLD_CENTER_Y) * scale_to_minimap
    ship_minimap_x_int, ship_minimap_y_int = int(ship_minimap_x), int(ship_minimap_y)
    if math.hypot(ship_minimap_x - MINIMAP_SIZE_RADIUS, ship_minimap_y - MINIMAP_SIZE_RADIUS) <= MINIMAP_SIZE_RADIUS:
        cross_size = 4
        pygame.draw.line(minimap_render_surface, SHIP_MINIMAP_COLOR, (ship_minimap_x_int - cross_size, ship_minimap_y_int), (ship_minimap_x_int + cross_size, ship_minimap_y_int), 1)
        pygame.draw.line(minimap_render_surface, SHIP_MINIMAP_COLOR, (ship_minimap_x_int, ship_minimap_y_int - cross_size), (ship_minimap_x_int, ship_minimap_y_int + cross_size), 1)
    surface.blit(minimap_render_surface, (MINIMAP_CENTER_X_ON_SCREEN - MINIMAP_SIZE_RADIUS, MINIMAP_CENTER_Y_ON_SCREEN - MINIMAP_SIZE_RADIUS))

# Main game execution function.
def main_program():
    pygame.init()
    screen = SCREEN
    clock = pygame.time.Clock()
    ui_font = pygame.font.SysFont('Arial', UI_FONT_SIZE, bold=True)
    debug_font = pygame.font.SysFont('Arial', 24) # Adjusted size for debug
    score_font = pygame.font.SysFont('Arial', 30, bold=True) # Font for score

    print("Generating game world background (this may take a moment)...")
    main_game_background = Background()
    # Get the list of all garbage items from the background object
    all_garbage_objects = main_game_background.all_garbage_items
    print(f"Game world background generated. Total garbage items: {len(all_garbage_objects)}")

    spaceShip = None
    camera_x, camera_y = 0, 0
    game_time = 0
    is_game_paused = False
    score = 0 # Initialize score

    start_text_render = ui_font.render("Click or Press Enter to Start", True, UI_TEXT_COLOR)
    start_text_rect = start_text_render.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
    start_text_hover_render = ui_font.render("Click or Press Enter to Start", True, UI_TEXT_HOVER_COLOR)

    paused_text_render = ui_font.render("PAUSED (Click or P to Resume)", True, UI_TEXT_COLOR)
    paused_text_rect = paused_text_render.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    paused_text_hover_render = ui_font.render("PAUSED (Click or P to Resume)", True, UI_TEXT_HOVER_COLOR)

    current_state = STATE_READY_TO_START

    ship_spawn_check_radius = max(DESIRED_SIZE) / 2 if DESIRED_SIZE else 50
    initial_ship_x, initial_ship_y = get_safe_spawn_position(main_game_background, ship_spawn_check_radius)
    spaceShip = SpaceShip(initial_ship_x, initial_ship_y)
    camera_x = spaceShip.x - SCREEN_WIDTH // 2
    camera_y = spaceShip.y - SCREEN_HEIGHT // 2
    spaceShip.is_thrusting = False

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                if current_state == STATE_READY_TO_START:
                    if event.key == pygame.K_RETURN:
                        current_state = STATE_PLAYING
                        game_time = 0
                        score = 0 # Reset score on new game
                elif current_state == STATE_PLAYING:
                    if event.key == pygame.K_p:
                        is_game_paused = not is_game_paused

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if current_state == STATE_READY_TO_START and start_text_rect.collidepoint(mouse_pos):
                        current_state = STATE_PLAYING
                        game_time = 0
                        score = 0 # Reset score
                    elif current_state == STATE_PLAYING and is_game_paused and paused_text_rect.collidepoint(mouse_pos):
                        is_game_paused = False

        if current_state == STATE_PLAYING:
            if not is_game_paused:
                spaceShip.is_thrusting = False
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LEFT]:
                    spaceShip.current_angle += ROTATION_SPEED
                    spaceShip.current_angle %= 360
                if keys[pygame.K_RIGHT]:
                    spaceShip.current_angle -= ROTATION_SPEED
                    spaceShip.current_angle %= 360

                spaceShip.vx_1 = 0.0
                spaceShip.vy_1 = 0.0
                if keys[pygame.K_UP]:
                    spaceShip.is_thrusting = True
                    thrust_angle_rad = math.radians(spaceShip.current_angle)
                    spaceShip.vx_1 = THRUST_MAGNITUDE * math.cos(thrust_angle_rad)
                    spaceShip.vy_1 = THRUST_MAGNITUDE * math.sin(thrust_angle_rad) # Original vy_1 logic
                    max_vel_component = 8.0
                    if spaceShip.vx_0 + spaceShip.vx_1 > max_vel_component : spaceShip.vx_1 = max(0, max_vel_component - spaceShip.vx_0)
                    if spaceShip.vx_0 + spaceShip.vx_1 < -max_vel_component: spaceShip.vx_1 = min(0, -max_vel_component - spaceShip.vx_0)
                    if spaceShip.vy_0 + spaceShip.vy_1 > max_vel_component : spaceShip.vy_1 = max(0, max_vel_component - spaceShip.vy_0)
                    if spaceShip.vy_0 + spaceShip.vy_1 < -max_vel_component: spaceShip.vy_1 = min(0, -max_vel_component - spaceShip.vy_0)

                spaceShip.update() # Updates ship position and particles
                main_game_background.update(dt) # Updates planet positions

                camera_x = spaceShip.x - SCREEN_WIDTH // 2
                camera_y = spaceShip.y - SCREEN_HEIGHT // 2
                game_time += dt

                # Collision detection: Spaceship with Garbage
                ship_collider = spaceShip.get_collider_world()
                collected_indices = []
                for i, G_item in enumerate(all_garbage_objects):
                    if ship_collider.colliderect(G_item.get_collider()):
                        collected_indices.append(i)
                        score += 1 # Increment score for each collected item

                # Remove collected garbage (iterate backwards to avoid index errors)
                for i in sorted(collected_indices, reverse=True):
                    all_garbage_objects.pop(i)


        main_game_background.draw(SCREEN, camera_x, camera_y)

        # Draw all garbage items
        for G_item in all_garbage_objects:
            G_item.draw(SCREEN, camera_x, camera_y)

        spaceShip.draw(SCREEN, camera_x, camera_y)

        if current_state == STATE_READY_TO_START:
            if start_text_rect.collidepoint(mouse_pos):
                SCREEN.blit(start_text_hover_render, start_text_rect)
            else:
                SCREEN.blit(start_text_render, start_text_rect)
        elif current_state == STATE_PLAYING:
            if is_game_paused:
                if paused_text_rect.collidepoint(mouse_pos):
                    SCREEN.blit(paused_text_hover_render, paused_text_rect)
                else:
                    SCREEN.blit(paused_text_render, paused_text_rect)
            else:
                # Display Score
                score_surface = score_font.render(f"Score: {score}", True, SCORE_TEXT_COLOR)
                score_rect = score_surface.get_rect(topleft=(20, 20))
                SCREEN.blit(score_surface, score_rect)

                # Display remaining garbage count
                garbage_count_text = f"Garbage Left: {len(all_garbage_objects)}"
                garbage_count_surface = debug_font.render(garbage_count_text, True, (200, 200, 255))
                garbage_count_rect = garbage_count_surface.get_rect(topleft=(20, score_rect.bottom + 5))
                SCREEN.blit(garbage_count_surface, garbage_count_rect)

                # Original debug text for coordinates (if needed, can be re-enabled or kept)
                # debug_text_surface = debug_font.render(f"World X: {spaceShip.x:.0f} Y: {spaceShip.y:.0f}", True, (200, 200, 255))
                # debug_text_rect = debug_text_surface.get_rect(topleft=(20, garbage_count_rect.bottom + 5))
                # SCREEN.blit(debug_text_surface, debug_text_rect)


        if current_state != STATE_READY_TO_START:
            draw_minimap(SCREEN, spaceShip, main_game_background, camera_x, camera_y, all_garbage_objects)

        pygame.display.flip()

    pygame.quit()

if __name__ == '__main__':
    main_program()
