# main.py

import pygame
import os
import math
import random
import json # Import the json module

from config import (SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN, ROTATION_SPEED, THRUST_MAGNITUDE,
                    WORLD_RADIUS, WORLD_CENTER_X, WORLD_CENTER_Y,
                    SUN_RADIUS, SUN_COLOR, DESIRED_SIZE, NUM_SOLAR_SYSTEM_PLANETS)
from spaceship import SpaceShip
from galaxy import Background
from garbage import Garbage # Import Garbage to re-instantiate on load

SAVE_FILE = "savegame.txt" # Name of the save file

# Game States
STATE_LOADING_PROMPT = 3 # Initial state for Load/New Game choice
STATE_READY_TO_START = 0
STATE_PLAYING = 1
STATE_GAME_OVER = 2


# UI Constants
UI_FONT_SIZE = 50
TITLE_FONT_SIZE = 90 # For "GREENSPACE.IO"
UI_TEXT_COLOR = (220, 220, 255)
TITLE_TEXT_COLOR = (100, 255, 150) # A greenish, bright color for the title
UI_TEXT_HOVER_COLOR = (255, 255, 150)
SCORE_TEXT_COLOR = (200, 255, 200)
GAMEOVER_TEXT_COLOR = UI_TEXT_COLOR
RESTART_BUTTON_BG_COLOR = (50, 50, 100)
RESTART_BUTTON_BG_HOVER_COLOR = (80, 80, 150)
RESTART_TEXT_COLOR = UI_TEXT_COLOR
CRASH_TIMER_TEXT_COLOR = (255, 180, 180)
CRASH_COUNT_TEXT_COLOR = (255, 100, 100) # Color for crash count

# Minimap Variables
MINIMAP_SIZE_RADIUS = 80
MINIMAP_MARGIN = 15
MINIMAP_CENTER_X_ON_SCREEN = SCREEN_WIDTH - MINIMAP_SIZE_RADIUS - MINIMAP_MARGIN
MINIMAP_CENTER_Y_ON_SCREEN = MINIMAP_SIZE_RADIUS + MINIMAP_MARGIN
MINIMAP_BG_COLOR = (20, 20, 40, 180) # Semi-transparent background.
MINIMAP_BORDER_COLOR = (100, 100, 120, 200)
SHIP_MINIMAP_COLOR = (255, 255, 0)  # Yellow for ship.
GARBAGE_MINIMAP_COLOR = (0, 255, 0) # Green for garbage.

# Global game variables
main_game_background = None
all_garbage_objects = []
spaceShip = None
camera_x, camera_y = 0.0, 0.0
score = 0
game_time = 0.0
crash_time_elapsed = 0.0
ship_crash_count = 0
current_state = STATE_LOADING_PROMPT # Start with loading prompt

# UI Font instances
pygame.font.init()
ui_font = pygame.font.SysFont('Arial', UI_FONT_SIZE, bold=True)
title_font = pygame.font.SysFont('Arial', TITLE_FONT_SIZE, bold=True) # Font for game title
debug_font = pygame.font.SysFont('Arial', 24) # For garbage count.
score_font = pygame.font.SysFont('Arial', 30, bold=True) # For score display.
game_over_font = ui_font # Consistent font for "GAME OVER" message.
restart_button_font = pygame.font.SysFont('Arial', 35, bold=True)
crash_timer_font = pygame.font.SysFont('Arial', 28, bold=True) # Font for crash timer.
crash_count_font = pygame.font.SysFont('Arial', 28, bold=True) # Font for crash count
prompt_font = pygame.font.SysFont('Arial', 40, bold=True) # Font for load prompt

# Respawn button Rect
respawn_button_text_surface = restart_button_font.render("Respawn", True, RESTART_TEXT_COLOR)
padding_x = 30 # Horizontal padding for the button.
padding_y = 15 # Vertical padding for the button.
respawn_button_rect_inner = respawn_button_text_surface.get_rect(
    center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150) # Positioned below new counters
)
respawn_button_rect_outer = respawn_button_rect_inner.inflate(padding_x * 2, padding_y * 2)


def get_safe_spawn_position(bg_obj, ship_radius_approx):
    """Attempts to find a spawn position for the ship away from the sun and planets."""
    max_attempts = 100
    for _ in range(max_attempts):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(WORLD_RADIUS * 0.3, WORLD_RADIUS * 0.7)
        spawn_x = WORLD_CENTER_X + dist * math.cos(angle)
        spawn_y = WORLD_CENTER_Y + dist * math.sin(angle)
        sun_dist_sq = (spawn_x - WORLD_CENTER_X)**2 + (spawn_y - WORLD_CENTER_Y)**2
        if sun_dist_sq < (SUN_RADIUS + ship_radius_approx + 200)**2:
            continue
        safe = True
        # Check if bg_obj and solar_system_planets exist and list is not empty
        if hasattr(bg_obj, 'solar_system_planets') and bg_obj.solar_system_planets:
            for p_data in bg_obj.solar_system_planets:
                p_x, p_y = p_data['world_pos']
                p_r = p_data['radius']
                planet_dist_sq = (spawn_x - p_x)**2 + (spawn_y - p_y)**2
                if planet_dist_sq < (p_r + ship_radius_approx + 200)**2:
                    safe = False; break
        if safe:
            return float(spawn_x), float(spawn_y)
    print("Warning: Fallback spawn position used.")
    return float(WORLD_CENTER_X + random.uniform(SUN_RADIUS + 300, SUN_RADIUS + 500)), \
           float(WORLD_CENTER_Y + random.uniform(SUN_RADIUS + 300, SUN_RADIUS + 500))

def draw_minimap(surface, current_ship, bg_obj, cam_x, cam_y, garbage_list):
    """Renders the minimap interface on the game screen."""
    minimap_render_surface = pygame.Surface((MINIMAP_SIZE_RADIUS * 2, MINIMAP_SIZE_RADIUS * 2), pygame.SRCALPHA)
    minimap_render_surface.fill((0,0,0,0))
    pygame.draw.circle(minimap_render_surface, MINIMAP_BG_COLOR, (MINIMAP_SIZE_RADIUS, MINIMAP_SIZE_RADIUS), MINIMAP_SIZE_RADIUS)
    pygame.draw.circle(minimap_render_surface, MINIMAP_BORDER_COLOR, (MINIMAP_SIZE_RADIUS, MINIMAP_SIZE_RADIUS), MINIMAP_SIZE_RADIUS, 2)
    scale = float(MINIMAP_SIZE_RADIUS) / WORLD_RADIUS
    if hasattr(bg_obj, 'sun_data'):
        sx, sy = bg_obj.sun_data['world_pos']
        msx = MINIMAP_SIZE_RADIUS + (sx - WORLD_CENTER_X) * scale
        msy = MINIMAP_SIZE_RADIUS + (sy - WORLD_CENTER_Y) * scale
        msr = max(1, int(bg_obj.sun_data['radius'] * scale))
        pygame.draw.circle(minimap_render_surface, bg_obj.sun_data['color'], (int(msx), int(msy)), msr)
    if hasattr(bg_obj, 'solar_system_planets') and bg_obj.solar_system_planets:
        for p in bg_obj.solar_system_planets:
            px, py = p['world_pos']
            mpx = MINIMAP_SIZE_RADIUS + (px - WORLD_CENTER_X) * scale
            mpy = MINIMAP_SIZE_RADIUS + (py - WORLD_CENTER_Y) * scale
            mpr = max(1, int(p['radius'] * scale))
            pygame.draw.circle(minimap_render_surface, p['color'], (int(mpx), int(mpy)), mpr)
    for G_item in garbage_list:
        g_world_x, g_world_y = G_item.world_x, G_item.world_y
        g_minimap_x = MINIMAP_SIZE_RADIUS + (g_world_x - WORLD_CENTER_X) * scale
        g_minimap_y = MINIMAP_SIZE_RADIUS + (g_world_y - WORLD_CENTER_Y) * scale
        if math.hypot(g_minimap_x - MINIMAP_SIZE_RADIUS, g_minimap_y - MINIMAP_SIZE_RADIUS) <= MINIMAP_SIZE_RADIUS:
            pygame.draw.circle(minimap_render_surface, GARBAGE_MINIMAP_COLOR, (int(g_minimap_x), int(g_minimap_y)), 1)
    if current_ship and current_ship.alive:
        shx, shy = current_ship.x, current_ship.y
        mshx = MINIMAP_SIZE_RADIUS + (shx - WORLD_CENTER_X) * scale
        mshy = MINIMAP_SIZE_RADIUS + (shy - WORLD_CENTER_Y) * scale
        cs = 4
        pygame.draw.line(minimap_render_surface, SHIP_MINIMAP_COLOR, (int(mshx-cs), int(mshy)), (int(mshx+cs), int(mshy)), 1)
        pygame.draw.line(minimap_render_surface, SHIP_MINIMAP_COLOR, (int(mshx), int(mshy-cs)), (int(mshx), int(mshy+cs)), 1)
    surface.blit(minimap_render_surface, (MINIMAP_CENTER_X_ON_SCREEN - MINIMAP_SIZE_RADIUS, MINIMAP_CENTER_Y_ON_SCREEN - MINIMAP_SIZE_RADIUS))

def reset_game_state():
    """Resets all necessary game variables for a brand new game session (full restart)."""
    global main_game_background, all_garbage_objects, spaceShip, camera_x, camera_y
    global score, game_time, ship_crash_count, crash_time_elapsed
    print("Resetting game state for a new game...")
    main_game_background = Background()
    all_garbage_objects = main_game_background.all_garbage_items
    ship_spawn_radius = max(DESIRED_SIZE) / 2.0 if DESIRED_SIZE else 50.0
    initial_ship_x, initial_ship_y = get_safe_spawn_position(main_game_background, ship_spawn_radius)
    spaceShip = SpaceShip(initial_ship_x, initial_ship_y)
    camera_x = spaceShip.x - SCREEN_WIDTH // 2
    camera_y = spaceShip.y - SCREEN_HEIGHT // 2
    score = 0
    game_time = 0.0
    ship_crash_count = 0
    crash_time_elapsed = 0.0

def respawn_ship():
    """Respawns the ship in the current world without resetting game progress."""
    global spaceShip, camera_x, camera_y
    print("Respawning ship...")
    ship_spawn_radius = max(DESIRED_SIZE) / 2.0 if DESIRED_SIZE else 50.0
    initial_ship_x, initial_ship_y = get_safe_spawn_position(main_game_background, ship_spawn_radius)
    spaceShip = SpaceShip(initial_ship_x, initial_ship_y)
    camera_x = spaceShip.x - SCREEN_WIDTH // 2
    camera_y = spaceShip.y - SCREEN_HEIGHT // 2

def save_game():
    """Saves the current game state to a file."""
    global spaceShip, score, game_time, ship_crash_count, main_game_background, all_garbage_objects
    if not spaceShip or not main_game_background:
        print("Cannot save game: core game objects not initialized.")
        return
    print(f"Saving game to {SAVE_FILE}...")
    game_data = {
        "spaceship": {
            "x": spaceShip.x, "y": spaceShip.y,
            "vx_0": spaceShip.vx_0, "vy_0": spaceShip.vy_0,
            "current_angle": spaceShip.current_angle
        },
        "game_progress": {
            "score": score, "game_time": game_time,
            "ship_crash_count": ship_crash_count
        },
        "solar_system_planets_state": [
            {'world_pos': p['world_pos'][:], 'radius': p['radius'], 'color': p['color'],
             'orbit_radius': p['orbit_radius'], 'orbit_speed': p['orbit_speed'],
             'current_orbit_angle': p['current_orbit_angle']}
            for p in main_game_background.solar_system_planets
        ],
        "remaining_garbage": [
            {"world_x": g.world_x, "world_y": g.world_y, "size": g.size}
            for g in all_garbage_objects
        ]
    }
    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump(game_data, f, indent=4)
        print("Game saved successfully.")
    except Exception as e:
        print(f"Error saving game: {e}")

def load_game():
    """Loads the game state from a file."""
    global main_game_background, all_garbage_objects, spaceShip, camera_x, camera_y
    global score, game_time, ship_crash_count, current_state, crash_time_elapsed
    print(f"Attempting to load game from {SAVE_FILE}...")
    try:
        with open(SAVE_FILE, 'r') as f:
            data = json.load(f)

        main_game_background = Background() # Static visuals (stars, nebula) will be fresh.

        ship_data = data['spaceship']
        spaceShip = SpaceShip(ship_data['x'], ship_data['y'])
        spaceShip.vx_0 = ship_data['vx_0']; spaceShip.vy_0 = ship_data['vy_0']
        spaceShip.current_angle = ship_data['current_angle']; spaceShip.alive = True

        game_progress = data['game_progress']
        score = game_progress['score']; game_time = game_progress['game_time']
        ship_crash_count = game_progress['ship_crash_count']; crash_time_elapsed = 0.0

        main_game_background.solar_system_planets.clear()
        for p_state in data['solar_system_planets_state']:
            main_game_background.solar_system_planets.append({
                'type': 'solar_system_planet',
                'world_pos': list(p_state['world_pos']),
                'radius': p_state['radius'], 'color': tuple(p_state['color']),
                'orbit_radius': p_state['orbit_radius'], 'orbit_speed': p_state['orbit_speed'],
                'current_orbit_angle': p_state['current_orbit_angle']
            })

        all_garbage_objects.clear()
        main_game_background.all_garbage_items = all_garbage_objects
        for g_data in data['remaining_garbage']:
            new_garbage = Garbage(g_data['world_x'], g_data['world_y'], loaded_size=g_data['size'])
            all_garbage_objects.append(new_garbage)

        camera_x = spaceShip.x - SCREEN_WIDTH // 2
        camera_y = spaceShip.y - SCREEN_HEIGHT // 2
        current_state = STATE_PLAYING
        print("Game loaded successfully.")
        return True
    except FileNotFoundError: print(f"Save file '{SAVE_FILE}' not found. Starting new game."); return False
    except Exception as e: print(f"Error loading game: {e}. Starting new game."); return False

def main_program():
    global main_game_background, all_garbage_objects, spaceShip, camera_x, camera_y
    global score, game_time, current_state, crash_time_elapsed, ship_crash_count

    pygame.init()
    screen = SCREEN
    clock = pygame.time.Clock()

    # --- Menu Specific Assets ---
    menu_background_instance = Background() # Dedicated Background for menu visuals
    # Position menu ship and camera to showcase nebula rather than sun (often at 0,0)
    menu_ship_world_x = WORLD_CENTER_X + WORLD_RADIUS * 0.5 # Slightly off-center for interest
    menu_ship_world_y = WORLD_CENTER_Y + WORLD_RADIUS * 0.5
    menu_ship = SpaceShip(menu_ship_world_x, menu_ship_world_y)
    menu_ship.is_thrusting = True
    menu_ship_rotation_speed = 0.4 # Slightly faster rotation for visual appeal

    # Adjust camera to view a potentially interesting part of the generated menu background
    # These might need tuning based on your Background generation specifics
    menu_camera_x = menu_ship_world_x - SCREEN_WIDTH // 2
    menu_camera_y = menu_ship_world_y - SCREEN_HEIGHT // 2

    title_text_surface = title_font.render("GREENSPACE.IO", True, TITLE_TEXT_COLOR)
    title_text_rect = title_text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))

    prompt_load_text = prompt_font.render("L: Load Game", True, UI_TEXT_COLOR)
    prompt_load_rect = prompt_load_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
    prompt_new_text = prompt_font.render("N: New Game", True, UI_TEXT_COLOR)
    prompt_new_rect = prompt_new_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120))
    # --- End Menu Specific Assets ---

    start_text_render = ui_font.render("Click or Press Enter to Start", True, UI_TEXT_COLOR)
    start_text_rect = start_text_render.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
    start_text_hover_render = ui_font.render("Click or Press Enter to Start", True, UI_TEXT_HOVER_COLOR)
    paused_text_render = ui_font.render("PAUSED (Click or P to Resume)", True, UI_TEXT_COLOR)
    paused_text_rect = paused_text_render.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    paused_text_hover_render = ui_font.render("PAUSED (Click or P to Resume)", True, UI_TEXT_HOVER_COLOR)

    is_game_paused = False
    running = True
    game_fully_initialized = False # Ensures reset_game_state or load_game runs once

    while running:
        dt = clock.tick(60) / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        previous_game_state = current_state

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
                if current_state == STATE_LOADING_PROMPT:
                    if event.key == pygame.K_l:
                        if load_game(): game_fully_initialized = True
                        else: reset_game_state(); current_state = STATE_READY_TO_START; game_fully_initialized = True
                    elif event.key == pygame.K_n:
                        reset_game_state(); current_state = STATE_READY_TO_START; game_fully_initialized = True
                elif current_state == STATE_READY_TO_START and event.key == pygame.K_RETURN:
                    current_state = STATE_PLAYING
                elif current_state == STATE_PLAYING and spaceShip and spaceShip.alive and event.key == pygame.K_p:
                    is_game_paused = not is_game_paused
                elif current_state == STATE_GAME_OVER and event.key == pygame.K_RETURN:
                    respawn_ship(); current_state = STATE_PLAYING
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if current_state == STATE_READY_TO_START and start_text_rect.collidepoint(mouse_pos):
                    current_state = STATE_PLAYING
                elif current_state == STATE_PLAYING and spaceShip and spaceShip.alive and is_game_paused and paused_text_rect.collidepoint(mouse_pos):
                    is_game_paused = False
                elif current_state == STATE_GAME_OVER and respawn_button_rect_outer.collidepoint(mouse_pos):
                    respawn_ship(); current_state = STATE_PLAYING

        # --- Game Logic Update Phase ---
        if current_state == STATE_LOADING_PROMPT:
            menu_background_instance.update(dt)
            menu_ship.current_angle = (menu_ship.current_angle + menu_ship_rotation_speed * (dt*60)) % 360 # dt*60 for smoother anim
            menu_ship.update()
        elif current_state == STATE_PLAYING:
            if not spaceShip.alive:
                if previous_game_state == STATE_PLAYING:
                    ship_crash_count += 1; crash_time_elapsed = 0.0
                current_state = STATE_GAME_OVER
            elif not is_game_paused:
                spaceShip.is_thrusting = False; keys = pygame.key.get_pressed()
                if keys[pygame.K_LEFT]: spaceShip.current_angle = (spaceShip.current_angle + ROTATION_SPEED) % 360
                if keys[pygame.K_RIGHT]: spaceShip.current_angle = (spaceShip.current_angle - ROTATION_SPEED) % 360
                spaceShip.vx_1, spaceShip.vy_1 = 0.0, 0.0
                if keys[pygame.K_UP]:
                    spaceShip.is_thrusting = True; thrust_rad = math.radians(spaceShip.current_angle)
                    spaceShip.vx_1=THRUST_MAGNITUDE*math.cos(thrust_rad); spaceShip.vy_1=THRUST_MAGNITUDE*math.sin(thrust_rad)
                    max_v = 8.0
                    if spaceShip.vx_0+spaceShip.vx_1>max_v: spaceShip.vx_1=max(0,max_v-spaceShip.vx_0)
                    if spaceShip.vx_0+spaceShip.vx_1<-max_v: spaceShip.vx_1=min(0,-max_v-spaceShip.vx_0)
                    if spaceShip.vy_0+spaceShip.vy_1>max_v: spaceShip.vy_1=max(0,max_v-spaceShip.vy_0)
                    if spaceShip.vy_0+spaceShip.vy_1<-max_v: spaceShip.vy_1=min(0,-max_v-spaceShip.vy_0)
                spaceShip.update(); main_game_background.update(dt)
                for G_item in all_garbage_objects: G_item.update(spaceShip.x, spaceShip.y, dt)
                camera_x = spaceShip.x-SCREEN_WIDTH//2; camera_y = spaceShip.y-SCREEN_HEIGHT//2; game_time += dt
                ship_collider = spaceShip.get_collider_world(); collected_indices = []
                for i,G_item in enumerate(all_garbage_objects):
                    if ship_collider.colliderect(G_item.get_collider()): collected_indices.append(i); score += 1
                for i in sorted(collected_indices, reverse=True): all_garbage_objects.pop(i)
                if spaceShip.alive:
                    sr = spaceShip.get_collider_world().width/2.2
                    if (spaceShip.x-WORLD_CENTER_X)**2+(spaceShip.y-WORLD_CENTER_Y)**2 < (SUN_RADIUS+sr)**2: spaceShip.explode()
                    if spaceShip.alive:
                        for p in main_game_background.solar_system_planets:
                            if (spaceShip.x-p['world_pos'][0])**2+(spaceShip.y-p['world_pos'][1])**2 < (p['radius']+sr)**2:
                                spaceShip.explode(); break
                        if spaceShip.alive and math.hypot(spaceShip.x-WORLD_CENTER_X,spaceShip.y-WORLD_CENTER_Y) > WORLD_RADIUS-sr:
                            spaceShip.explode()
        elif current_state == STATE_GAME_OVER:
            crash_time_elapsed += dt
            if spaceShip: spaceShip.update()
            if main_game_background: main_game_background.update(dt)

        # --- Drawing Phase ---
        screen.fill((0,0,0))
        if current_state == STATE_LOADING_PROMPT:
            menu_background_instance.draw(screen, menu_camera_x, menu_camera_y)
            menu_ship.draw(screen, menu_camera_x, menu_camera_y) # Ship drawn relative to menu camera
            screen.blit(title_text_surface, title_text_rect)
            if not os.path.exists(SAVE_FILE):
                 screen.blit(prompt_new_text, prompt_new_rect)
                 no_save_text = prompt_font.render("No save file found.", True, UI_TEXT_COLOR)
                 no_save_rect = no_save_text.get_rect(center=(SCREEN_WIDTH//2, prompt_load_rect.top - 60))
                 screen.blit(no_save_text, no_save_rect)
            else:
                screen.blit(prompt_load_text, prompt_load_rect)
                screen.blit(prompt_new_text, prompt_new_rect)
        elif main_game_background and spaceShip:
            main_game_background.draw(screen, camera_x, camera_y)
            for G_item in all_garbage_objects: G_item.draw(screen, camera_x, camera_y)
            spaceShip.draw(screen, camera_x, camera_y)
            if current_state == STATE_READY_TO_START:
                txt = start_text_hover_render if start_text_rect.collidepoint(mouse_pos) else start_text_render
                screen.blit(txt, start_text_rect)
            elif current_state == STATE_PLAYING:
                if is_game_paused:
                    txt = paused_text_hover_render if paused_text_rect.collidepoint(mouse_pos) else paused_text_render
                    screen.blit(txt, paused_text_rect)
                else:
                    s_surf=score_font.render(f"Score: {score}",True,SCORE_TEXT_COLOR); screen.blit(s_surf,(20,20))
                    g_surf=debug_font.render(f"Garbage: {len(all_garbage_objects)}",True,UI_TEXT_COLOR); screen.blit(g_surf,(20,s_surf.get_height()+25))
                if spaceShip: draw_minimap(screen,spaceShip,main_game_background,camera_x,camera_y,all_garbage_objects)
            elif current_state == STATE_GAME_OVER:
                go_surf=game_over_font.render("GAME OVER",True,GAMEOVER_TEXT_COLOR); go_r=go_surf.get_rect(center=(SCREEN_WIDTH//2,SCREEN_HEIGHT//2-120)); screen.blit(go_surf,go_r)
                fs_surf=score_font.render(f"Final Score: {score}",True,SCORE_TEXT_COLOR); fs_r=fs_surf.get_rect(center=(SCREEN_WIDTH//2,go_r.bottom+35)); screen.blit(fs_surf,fs_r)
                ct_surf=crash_timer_font.render(f"Time Since Crash: {crash_time_elapsed:.1f}s",True,CRASH_TIMER_TEXT_COLOR); ct_r=ct_surf.get_rect(center=(SCREEN_WIDTH//2,fs_r.bottom+35)); screen.blit(ct_surf,ct_r)
                cc_surf=crash_count_font.render(f"Crashes: {ship_crash_count}",True,CRASH_COUNT_TEXT_COLOR); cc_r=cc_surf.get_rect(center=(SCREEN_WIDTH//2,ct_r.bottom+35)); screen.blit(cc_surf,cc_r)
                btn_c = RESTART_BUTTON_BG_HOVER_COLOR if respawn_button_rect_outer.collidepoint(mouse_pos) else RESTART_BUTTON_BG_COLOR
                pygame.draw.rect(screen,btn_c,respawn_button_rect_outer,border_radius=10); screen.blit(respawn_button_text_surface,respawn_button_rect_inner)
                if spaceShip and main_game_background: draw_minimap(screen,spaceShip,main_game_background,camera_x,camera_y,all_garbage_objects)

        pygame.display.flip()

    if (current_state == STATE_PLAYING and spaceShip and spaceShip.alive) or \
       (current_state == STATE_GAME_OVER and spaceShip):
        save_game()

    pygame.quit()

if __name__ == '__main__':
    main_program()
