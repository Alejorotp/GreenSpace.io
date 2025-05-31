# main.py

import pygame
import os
import math
import random

from config import SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN, ROTATION_SPEED, THRUST_MAGNITUDE, \
                   WORLD_RADIUS, WORLD_CENTER_X, WORLD_CENTER_Y, \
                   SUN_RADIUS, SUN_COLOR, DESIRED_SIZE
from spaceship import SpaceShip
from galaxy import Background

# --- Game States ---
STATE_READY_TO_START = 0 # New initial state
STATE_PLAYING = 1
STATE_GAME_OVER = 2
STATE_WIN = 3
# STATE_START_MENU is no longer needed

# --- UI Constants ---
UI_FONT_SIZE = 50
UI_TEXT_COLOR = (220, 220, 255)
UI_TEXT_HOVER_COLOR = (255, 255, 150)

# --- Minimap Variables ---
MINIMAP_SIZE_RADIUS = 80
MINIMAP_MARGIN = 15
MINIMAP_CENTER_X_ON_SCREEN = SCREEN_WIDTH - MINIMAP_SIZE_RADIUS - MINIMAP_MARGIN
MINIMAP_CENTER_Y_ON_SCREEN = MINIMAP_SIZE_RADIUS + MINIMAP_MARGIN
MINIMAP_BG_COLOR = (20, 20, 40, 180)
MINIMAP_BORDER_COLOR = (100, 100, 120, 200)
SHIP_MINIMAP_COLOR = (255, 255, 0)

# --- Helper Functions (get_safe_spawn_position, draw_minimap - no changes from your version) ---
def get_safe_spawn_position(background_obj, ship_radius_approx):
    max_attempts = 100
    for attempt in range(max_attempts):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(WORLD_RADIUS * 0.2, WORLD_RADIUS * 0.6)
        spawn_x = WORLD_CENTER_X + dist * math.cos(angle)
        spawn_y = WORLD_CENTER_Y + dist * math.sin(angle)

        if hasattr(background_obj, 'sun_data') and background_obj.sun_data:
             sun_dist = math.hypot(spawn_x - background_obj.sun_data['world_pos'][0],
                                   spawn_y - background_obj.sun_data['world_pos'][1])
             if sun_dist < background_obj.sun_data['radius'] + ship_radius_approx + 50:
                 continue

        safe_from_planets = True
        if hasattr(background_obj, 'solar_system_planets'):
            for planet in background_obj.solar_system_planets:
                planet_dist = math.hypot(spawn_x - planet['world_pos'][0],
                                         spawn_y - planet['world_pos'][1])
                if planet_dist < planet['radius'] + ship_radius_approx + 50:
                    safe_from_planets = False
                    break
        if safe_from_planets:
            return float(spawn_x), float(spawn_y)

    print("Warning: Could not find a perfectly safe spawn point. Spawning near world center with offset.")
    return float(WORLD_CENTER_X + random.uniform(SUN_RADIUS + 100, SUN_RADIUS + 300)), \
           float(WORLD_CENTER_Y + random.uniform(SUN_RADIUS + 100, SUN_RADIUS + 300))

def draw_minimap(surface, game_ship, game_background, camera_x, camera_y):
    minimap_render_surface = pygame.Surface((MINIMAP_SIZE_RADIUS * 2, MINIMAP_SIZE_RADIUS * 2), pygame.SRCALPHA)
    minimap_render_surface.fill((0,0,0,0))
    pygame.draw.circle(minimap_render_surface, MINIMAP_BG_COLOR, (MINIMAP_SIZE_RADIUS, MINIMAP_SIZE_RADIUS), MINIMAP_SIZE_RADIUS)
    pygame.draw.circle(minimap_render_surface, MINIMAP_BORDER_COLOR, (MINIMAP_SIZE_RADIUS, MINIMAP_SIZE_RADIUS), MINIMAP_SIZE_RADIUS, 2)
    scale_to_minimap = float(MINIMAP_SIZE_RADIUS) / WORLD_RADIUS
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


# --- Main Program Loop ---
def main_program():
    pygame.init()
    screen = SCREEN
    clock = pygame.time.Clock()
    ui_font = pygame.font.SysFont('Arial', UI_FONT_SIZE, bold=True) # Font for UI elements
    debug_font = pygame.font.SysFont('Arial', 36) # For debug text like coordinates

    print("Generating game world background (this may take a moment)...")
    main_game_background = Background()
    print("Game world background generated.")

    # --- Game Variables (initialized once, or reset when a new game starts) ---
    spaceShip = None
    camera_x, camera_y = 0, 0
    game_time = 0
    is_game_paused = False # This is the in-game pause, not the ready_to_start state

    # --- UI Elements ---
    # For "Ready to Start" screen
    start_text_render = ui_font.render("Click or Press Enter to Start", True, UI_TEXT_COLOR)
    start_text_rect = start_text_render.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
    start_text_hover_render = ui_font.render("Click or Press Enter to Start", True, UI_TEXT_HOVER_COLOR)

    # For in-game pause
    paused_text_render = ui_font.render("PAUSED (Click or P to Resume)", True, UI_TEXT_COLOR)
    paused_text_rect = paused_text_render.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    paused_text_hover_render = ui_font.render("PAUSED (Click or P to Resume)", True, UI_TEXT_HOVER_COLOR)


    current_state = STATE_READY_TO_START

    # Initialize ship and camera for the first time for STATE_READY_TO_START
    ship_spawn_check_radius = max(DESIRED_SIZE) / 2 if DESIRED_SIZE else 50
    initial_ship_x, initial_ship_y = get_safe_spawn_position(main_game_background, ship_spawn_check_radius)
    spaceShip = SpaceShip(initial_ship_x, initial_ship_y)
    camera_x = spaceShip.x - SCREEN_WIDTH // 2
    camera_y = spaceShip.y - SCREEN_HEIGHT // 2
    spaceShip.is_thrusting = False # Ensure no thrust particles initially

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
                        game_time = 0 # Reset game time

                elif current_state == STATE_PLAYING:
                    if event.key == pygame.K_p:
                        is_game_paused = not is_game_paused

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    if current_state == STATE_READY_TO_START and start_text_rect.collidepoint(mouse_pos):
                        current_state = STATE_PLAYING
                        game_time = 0 # Reset game time
                    elif current_state == STATE_PLAYING and is_game_paused and paused_text_rect.collidepoint(mouse_pos):
                        is_game_paused = False

        # --- Game Logic based on State ---
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
                    spaceShip.vy_1 = THRUST_MAGNITUDE * math.sin(thrust_angle_rad)
                    max_vel_component = 8.0
                    if spaceShip.vx_0 + spaceShip.vx_1 > max_vel_component : spaceShip.vx_1 = max(0, max_vel_component - spaceShip.vx_0)
                    if spaceShip.vx_0 + spaceShip.vx_1 < -max_vel_component: spaceShip.vx_1 = min(0, -max_vel_component - spaceShip.vx_0)
                    if spaceShip.vy_0 + spaceShip.vy_1 > max_vel_component : spaceShip.vy_1 = max(0, max_vel_component - spaceShip.vy_0)
                    if spaceShip.vy_0 + spaceShip.vy_1 < -max_vel_component: spaceShip.vy_1 = min(0, -max_vel_component - spaceShip.vy_0)

                spaceShip.update()
                main_game_background.update(dt)
                camera_x = spaceShip.x - SCREEN_WIDTH // 2
                camera_y = spaceShip.y - SCREEN_HEIGHT // 2
                game_time += dt # Use dt for game_time

        # --- Drawing ---
        main_game_background.draw(SCREEN, camera_x, camera_y)
        spaceShip.draw(SCREEN, camera_x, camera_y) # Ship is drawn even in READY_TO_START

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
                # Draw debug text only when playing and not paused
                debug_text_surface = debug_font.render(f"World X: {spaceShip.x:.0f} Y: {spaceShip.y:.0f}", True, (200, 200, 255))
                debug_text_rect = debug_text_surface.get_rect(topleft=(20, 20))
                SCREEN.blit(debug_text_surface, debug_text_rect)

        if current_state != STATE_READY_TO_START: # Don't draw minimap on initial ready screen if too cluttered
             draw_minimap(SCREEN, spaceShip, main_game_background, camera_x, camera_y)

        pygame.display.flip()

    pygame.quit()

if __name__ == '__main__':
    main_program()
