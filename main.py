# main.py

import pygame
import os
import math
import random
import json

from config import (SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN, ROTATION_SPEED, THRUST_MAGNITUDE,
                    WORLD_RADIUS, WORLD_CENTER_X, WORLD_CENTER_Y,
                    SUN_RADIUS, SUN_COLOR, DESIRED_SIZE, NUM_SOLAR_SYSTEM_PLANETS,
                    SHIP_MAGNET_RANGE)
from spaceship import SpaceShip
from galaxy import Background
from garbage import Garbage

SAVE_FILE = "savegame.txt"

# Game States
STATE_LOADING_PROMPT = 3
STATE_READY_TO_START = 0
STATE_PLAYING = 1
STATE_GAME_OVER = 2
STATE_WIN = 4

# UI Constants
UI_FONT_SIZE = 50
TITLE_FONT_SIZE = 90
UI_TEXT_COLOR = (220, 220, 255)
TITLE_TEXT_COLOR = (100, 255, 150)
UI_TEXT_HOVER_COLOR = (255, 255, 150)
SCORE_TEXT_COLOR = (200, 255, 200)
GAMEOVER_TEXT_COLOR = UI_TEXT_COLOR
RESTART_BUTTON_BG_COLOR = (50, 50, 100)
RESTART_BUTTON_BG_HOVER_COLOR = (80, 80, 150)
RESTART_TEXT_COLOR = UI_TEXT_COLOR
CRASH_TIMER_TEXT_COLOR = (255, 180, 180)
CRASH_COUNT_TEXT_COLOR = (255, 100, 100)
WIN_TEXT_COLOR = (150, 255, 150)
WIN_INFO_COLOR = (200, 220, 255)

# Autopilot Indicator Constants
AUTOPILOT_FONT_SIZE = 30
AUTOPILOT_ON_COLOR = (0, 255, 0)  # Color for autopilot 'ON' indicator.
AUTOPILOT_OFF_COLOR = (255, 0, 0) # Color for autopilot 'OFF' indicator.

# World Boundary Warning Constants
WORLD_BOUNDARY_WARN_COLOR = (255, 0, 0, 150) # Color for the world boundary warning (includes alpha).
WORLD_BOUNDARY_WARN_THICKNESS = 15
BOUNDARY_PROXIMITY_THRESHOLD = 0.90

# Minimap Variables
MINIMAP_SIZE_RADIUS = 80; MINIMAP_MARGIN = 15
MINIMAP_CENTER_X_ON_SCREEN = SCREEN_WIDTH - MINIMAP_SIZE_RADIUS - MINIMAP_MARGIN
MINIMAP_CENTER_Y_ON_SCREEN = MINIMAP_SIZE_RADIUS + MINIMAP_MARGIN
MINIMAP_BG_COLOR = (20,20,40,180); MINIMAP_BORDER_COLOR = (100,100,120,200)
SHIP_MINIMAP_COLOR = (255,255,0); GARBAGE_MINIMAP_COLOR = (0,255,0)

# Autopilot Constants
AUTOPILOT_SHIP_RADIUS_APPROX = max(DESIRED_SIZE) / 2.0 if DESIRED_SIZE else 50.0
AUTOPILOT_DANGER_PROXIMITY_OBSTACLE = 550
AUTOPILOT_DANGER_PROXIMITY_BOUNDARY = 600
AUTOPILOT_GARBAGE_SEEK_RADIUS = SHIP_MAGNET_RANGE * 2.0
AUTOPILOT_ARRIVE_SLOWDOWN_RADIUS = 360
AUTOPILOT_WANDER_CHANGE_DIR_INTERVAL = 3.0
AUTOPILOT_WANDER_CONE_ANGLE = 90

# Global game variables
main_game_background = None
all_garbage_objects = []
spaceShip = None
camera_x, camera_y = 0.0, 0.0
score = 0; game_time = 0.0; crash_time_elapsed = 0.0; ship_crash_count = 0
autopilot_on = False
current_state = STATE_LOADING_PROMPT

# Autopilot global state variables
autopilot_wander_timer = 0.0
autopilot_target_wander_heading = 0.0
autopilot_first_wander_decision = True

pygame.font.init()
ui_font = pygame.font.SysFont('Arial', UI_FONT_SIZE, bold=True)
title_font = pygame.font.SysFont('Arial', TITLE_FONT_SIZE, bold=True)
debug_font = pygame.font.SysFont('Arial', 24)
score_font = pygame.font.SysFont('Arial', 30, bold=True)
game_over_font = ui_font
restart_button_font = pygame.font.SysFont('Arial', 35, bold=True)
crash_timer_font = pygame.font.SysFont('Arial', 28, bold=True)
crash_count_font = pygame.font.SysFont('Arial', 28, bold=True)
prompt_font = pygame.font.SysFont('Arial', 40, bold=True)
autopilot_font = pygame.font.SysFont('Arial', AUTOPILOT_FONT_SIZE, bold=True)

# Win Screen UI elements
win_title_main_font = pygame.font.SysFont('Arial', TITLE_FONT_SIZE + 10, bold=True)
win_info_font = pygame.font.SysFont('Arial', UI_FONT_SIZE - 15, bold=True)
win_text_surface = win_title_main_font.render("YOU WIN!", True, WIN_TEXT_COLOR)
win_text_rect = win_text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3 - 20))

play_again_button_font = restart_button_font
play_again_button_text_surface = play_again_button_font.render("Play Again", True, RESTART_TEXT_COLOR)
play_again_button_rect_inner = play_again_button_text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 180))
padding_x_button = 40; padding_y_button = 20
play_again_button_rect_outer = play_again_button_rect_inner.inflate(padding_x_button * 2, padding_y_button * 2)

respawn_button_text_surface = restart_button_font.render("Respawn",True,RESTART_TEXT_COLOR)
padding_x = 30; padding_y = 15
respawn_button_rect_inner = respawn_button_text_surface.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2+150))
respawn_button_rect_outer = respawn_button_rect_inner.inflate(padding_x*2, padding_y*2)


# --- Autopilot Helper Functions ---
def angle_to_target(current_x, current_y, target_x, target_y):
    """Calculates the angle in degrees from current to target point.
    Matches the spaceship's angle convention (0 East, 90 North/Up).
    """
    delta_x = target_x - current_x
    delta_y = target_y - current_y
    # -delta_y because ship's "up" (angle 90) corresponds to decreasing world Y coordinate
    angle_rad = math.atan2(-delta_y, delta_x)
    return (math.degrees(angle_rad) + 360) % 360

def normalize_angle_degrees_180(angle):
    """Normalizes an angle to the range [-180, 180] degrees."""
    angle = (angle + 180) % 360 - 180
    return angle

# --- Autopilot Decision Function ---
def get_autopilot_decision(ship, sun_data, planets_list, garbage_items_list, world_r, world_cx, world_cy, current_dt):
    """Determines autopilot actions (desired heading and thrust) based on game state."""
    global autopilot_wander_timer, autopilot_target_wander_heading, autopilot_first_wander_decision

    ship_x, ship_y = ship.x, ship.y
    ship_current_heading = ship.current_angle

    desired_heading = ship_current_heading # Default: maintain current heading
    should_thrust = False                  # Default: no thrust

    # Priority 1: Avoid Imminent Danger
    obstacles_to_check = [{'x': sun_data['world_pos'][0], 'y': sun_data['world_pos'][1], 'radius': sun_data['radius'], 'type': 'sun'}]
    for p in planets_list:
        obstacles_to_check.append({'x': p['world_pos'][0], 'y': p['world_pos'][1], 'radius': p['radius'], 'type': 'planet'})

    closest_obstacle_surface_dist = float('inf')
    action_flee = False

    for obs in obstacles_to_check:
        dist_to_obs_center = math.hypot(ship_x - obs['x'], ship_y - obs['y'])
        surface_dist = dist_to_obs_center - obs['radius'] - AUTOPILOT_SHIP_RADIUS_APPROX
        if surface_dist < AUTOPILOT_DANGER_PROXIMITY_OBSTACLE:
            if surface_dist < closest_obstacle_surface_dist: # Prioritize closest threat
                closest_obstacle_surface_dist = surface_dist
                desired_heading = (angle_to_target(obs['x'], obs['y'], ship_x, ship_y) + 360) % 360 # Flee from obstacle center
                should_thrust = True
                action_flee = True

    dist_from_world_center = math.hypot(ship_x - world_cx, ship_y - world_cy)
    dist_to_boundary = world_r - (dist_from_world_center + AUTOPILOT_SHIP_RADIUS_APPROX) # Distance from ship edge to boundary
    if dist_to_boundary < AUTOPILOT_DANGER_PROXIMITY_BOUNDARY:
        if not action_flee or dist_to_boundary < closest_obstacle_surface_dist: # If boundary is a more pressing danger
            desired_heading = (angle_to_target(ship_x, ship_y, world_cx, world_cy) + 360) % 360 # Flee towards world center
            should_thrust = True
            action_flee = True

    if action_flee:
        autopilot_first_wander_decision = True # Reset wander state if fleeing
        return desired_heading, should_thrust

    # Priority 2: Collect Garbage
    closest_garbage_obj = None
    min_dist_sq_to_garbage = AUTOPILOT_GARBAGE_SEEK_RADIUS ** 2

    for g_item in garbage_items_list:
        dx_g = ship_x - g_item.world_x
        dy_g = ship_y - g_item.world_y
        dist_sq = dx_g*dx_g + dy_g*dy_g
        if dist_sq < min_dist_sq_to_garbage:
            min_dist_sq_to_garbage = dist_sq
            closest_garbage_obj = g_item

    if closest_garbage_obj:
        autopilot_first_wander_decision = True # Reset wander state
        dist_to_garbage = math.sqrt(min_dist_sq_to_garbage)
        desired_heading = angle_to_target(ship_x, ship_y, closest_garbage_obj.world_x, closest_garbage_obj.world_y)

        # Thrust logic based on proximity, with some randomness
        should_thrust_normally = dist_to_garbage > AUTOPILOT_ARRIVE_SLOWDOWN_RADIUS
        if not should_thrust_normally: # Close to target
            should_thrust = random.random() < 0.2 # Low chance of pulsing thrust
        else: # Further from target
            should_thrust = random.random() < 0.4 # Moderate chance of thrusting
        return desired_heading, should_thrust

    # Priority 3: Wander
    autopilot_wander_timer += current_dt
    if autopilot_first_wander_decision or autopilot_wander_timer >= AUTOPILOT_WANDER_CHANGE_DIR_INTERVAL:
        autopilot_first_wander_decision = False
        autopilot_wander_timer = 0.0
        wander_offset = random.uniform(-AUTOPILOT_WANDER_CONE_ANGLE / 2, AUTOPILOT_WANDER_CONE_ANGLE / 2)
        autopilot_target_wander_heading = (ship_current_heading + wander_offset + 360) % 360

    desired_heading = autopilot_target_wander_heading
    should_thrust = random.random() < 0.7 # Probabilistic thrust during wander

    return desired_heading, should_thrust


# --- Game State Functions ---
def get_safe_spawn_position(bg_obj, ship_radius_approx):
    max_attempts = 100
    for _ in range(max_attempts):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(WORLD_RADIUS*0.3, WORLD_RADIUS*0.7) # Spawn between 30% and 70% of world radius
        spawn_x = WORLD_CENTER_X + dist * math.cos(angle)
        spawn_y = WORLD_CENTER_Y + dist * math.sin(angle)
        sun_dist_sq = (spawn_x - WORLD_CENTER_X)**2 + (spawn_y - WORLD_CENTER_Y)**2
        if sun_dist_sq < (SUN_RADIUS + ship_radius_approx + 200)**2: continue # Min distance from Sun
        safe = True
        if hasattr(bg_obj, 'solar_system_planets') and bg_obj.solar_system_planets:
            for p_data in bg_obj.solar_system_planets:
                p_x, p_y, p_r = p_data['world_pos'][0], p_data['world_pos'][1], p_data['radius']
                if (spawn_x - p_x)**2 + (spawn_y - p_y)**2 < (p_r + ship_radius_approx + 200)**2: # Min distance from planets
                    safe = False; break
        if safe: return float(spawn_x), float(spawn_y)
    print("Warning: Fallback spawn position used.")
    return float(WORLD_CENTER_X + random.uniform(SUN_RADIUS+300, SUN_RADIUS+500)), float(WORLD_CENTER_Y + random.uniform(SUN_RADIUS+300, SUN_RADIUS+500))

def draw_minimap(surface, current_ship, bg_obj, cam_x, cam_y, garbage_list):
    minimap_render_surface = pygame.Surface((MINIMAP_SIZE_RADIUS*2, MINIMAP_SIZE_RADIUS*2), pygame.SRCALPHA)
    minimap_render_surface.fill((0,0,0,0))
    pygame.draw.circle(minimap_render_surface, MINIMAP_BG_COLOR, (MINIMAP_SIZE_RADIUS,MINIMAP_SIZE_RADIUS), MINIMAP_SIZE_RADIUS)
    pygame.draw.circle(minimap_render_surface, MINIMAP_BORDER_COLOR, (MINIMAP_SIZE_RADIUS,MINIMAP_SIZE_RADIUS), MINIMAP_SIZE_RADIUS, 2)
    scale = float(MINIMAP_SIZE_RADIUS) / WORLD_RADIUS if WORLD_RADIUS > 0 else 0.001
    # Draw Sun on minimap
    if hasattr(bg_obj, 'sun_data'):
        sx,sy,sr = bg_obj.sun_data['world_pos'][0],bg_obj.sun_data['world_pos'][1],bg_obj.sun_data['radius']
        msx,msy,msr = MINIMAP_SIZE_RADIUS+(sx-WORLD_CENTER_X)*scale, MINIMAP_SIZE_RADIUS+(sy-WORLD_CENTER_Y)*scale, max(1,int(sr*scale))
        pygame.draw.circle(minimap_render_surface, bg_obj.sun_data['color'], (int(msx),int(msy)), msr)
    # Draw planets on minimap
    if hasattr(bg_obj, 'solar_system_planets') and bg_obj.solar_system_planets:
        for p in bg_obj.solar_system_planets:
            px,py,pr = p['world_pos'][0],p['world_pos'][1],p['radius']
            mpx,mpy,mpr = MINIMAP_SIZE_RADIUS+(px-WORLD_CENTER_X)*scale, MINIMAP_SIZE_RADIUS+(py-WORLD_CENTER_Y)*scale, max(1,int(pr*scale))
            pygame.draw.circle(minimap_render_surface, p['color'], (int(mpx),int(mpy)), mpr)
    # Draw garbage on minimap
    for G_item in garbage_list:
        gx,gy = G_item.world_x, G_item.world_y
        mgx,mgy = MINIMAP_SIZE_RADIUS+(gx-WORLD_CENTER_X)*scale, MINIMAP_SIZE_RADIUS+(gy-WORLD_CENTER_Y)*scale
        if math.hypot(mgx-MINIMAP_SIZE_RADIUS, mgy-MINIMAP_SIZE_RADIUS) <= MINIMAP_SIZE_RADIUS:
            pygame.draw.circle(minimap_render_surface, GARBAGE_MINIMAP_COLOR, (int(mgx),int(mgy)), 1)
    # Draw ship on minimap
    if current_ship and current_ship.alive:
        shx,shy = current_ship.x, current_ship.y
        mshx,mshy = MINIMAP_SIZE_RADIUS+(shx-WORLD_CENTER_X)*scale, MINIMAP_SIZE_RADIUS+(shy-WORLD_CENTER_Y)*scale
        cs=4; pygame.draw.line(minimap_render_surface,SHIP_MINIMAP_COLOR,(int(mshx-cs),int(mshy)),(int(mshx+cs),int(mshy)),1)
        pygame.draw.line(minimap_render_surface,SHIP_MINIMAP_COLOR,(int(mshx),int(mshy-cs)),(int(mshx),int(mshy+cs)),1)
    surface.blit(minimap_render_surface, (MINIMAP_CENTER_X_ON_SCREEN-MINIMAP_SIZE_RADIUS, MINIMAP_CENTER_Y_ON_SCREEN-MINIMAP_SIZE_RADIUS))

def reset_game_state():
    global main_game_background, all_garbage_objects, spaceShip, camera_x, camera_y, score, game_time, ship_crash_count, crash_time_elapsed, autopilot_on
    global autopilot_wander_timer, autopilot_target_wander_heading, autopilot_first_wander_decision
    print("Resetting game state for a new game...")
    main_game_background = Background()
    all_garbage_objects = main_game_background.all_garbage_items # Link to the newly generated garbage
    ship_radius = max(DESIRED_SIZE)/2.0 if DESIRED_SIZE else 50.0
    init_ship_x, init_ship_y = get_safe_spawn_position(main_game_background, ship_radius)
    spaceShip = SpaceShip(init_ship_x, init_ship_y)
    camera_x=spaceShip.x-SCREEN_WIDTH//2; camera_y=spaceShip.y-SCREEN_HEIGHT//2
    score=0; game_time=0.0; ship_crash_count=0; crash_time_elapsed=0.0
    autopilot_on = False # Default autopilot to off

    autopilot_wander_timer = 0.0
    autopilot_target_wander_heading = spaceShip.current_angle if spaceShip else 90.0
    autopilot_first_wander_decision = True

def respawn_ship():
    global spaceShip, camera_x, camera_y
    global autopilot_wander_timer, autopilot_target_wander_heading, autopilot_first_wander_decision
    print("Respawning ship...")
    ship_radius = max(DESIRED_SIZE)/2.0 if DESIRED_SIZE else 50.0
    init_ship_x, init_ship_y = get_safe_spawn_position(main_game_background, ship_radius)
    spaceShip = SpaceShip(init_ship_x, init_ship_y)
    camera_x=spaceShip.x-SCREEN_WIDTH//2; camera_y=spaceShip.y-SCREEN_HEIGHT//2
    # Score, game_time, crash_count, background and garbage persist

    autopilot_wander_timer = 0.0
    autopilot_target_wander_heading = spaceShip.current_angle
    autopilot_first_wander_decision = True

def save_game():
    global spaceShip, score, game_time, ship_crash_count, main_game_background, all_garbage_objects, autopilot_on
    if not spaceShip or not main_game_background: print("Cannot save: core objects not ready."); return
    print(f"Saving game to {SAVE_FILE}...")
    game_data = {"spaceship": {"x": spaceShip.x, "y": spaceShip.y, "vx_0": spaceShip.vx_0, "vy_0": spaceShip.vy_0, "current_angle": spaceShip.current_angle},
        "game_progress": {"score": score, "game_time": game_time, "ship_crash_count": ship_crash_count, "autopilot_on": autopilot_on},
        "solar_system_planets_state": [{'world_pos': p['world_pos'][:], 'radius': p['radius'], 'color': p['color'], 'orbit_radius': p['orbit_radius'], 'orbit_speed': p['orbit_speed'], 'current_orbit_angle': p['current_orbit_angle']} for p in main_game_background.solar_system_planets],
        "remaining_garbage": [{"world_x": g.world_x, "world_y": g.world_y, "size": g.size} for g in all_garbage_objects]}
    try:
        with open(SAVE_FILE, 'w') as f: json.dump(game_data, f, indent=4)
        print("Game saved successfully.")
    except Exception as e: print(f"Error saving game: {e}")

def load_game():
    global main_game_background, all_garbage_objects, spaceShip, camera_x, camera_y, score, game_time, ship_crash_count, current_state, crash_time_elapsed, autopilot_on
    global autopilot_wander_timer, autopilot_target_wander_heading, autopilot_first_wander_decision
    print(f"Attempting to load game from {SAVE_FILE}...")
    try:
        with open(SAVE_FILE, 'r') as f: data = json.load(f)
        # Re-initialize background before loading planets, so it doesn't double-generate its own set
        main_game_background = Background()
        # Clear default generated items from the new Background instance
        main_game_background.solar_system_planets.clear()
        main_game_background.all_garbage_items.clear()

        ship_data = data['spaceship']
        spaceShip = SpaceShip(ship_data['x'], ship_data['y'])
        spaceShip.vx_0=ship_data['vx_0']; spaceShip.vy_0=ship_data['vy_0']; spaceShip.current_angle=ship_data['current_angle']; spaceShip.alive=True

        game_progress = data['game_progress']
        score=game_progress['score']; game_time=game_progress['game_time']; ship_crash_count=game_progress['ship_crash_count']
        autopilot_on = game_progress.get("autopilot_on", False)
        crash_time_elapsed=0.0

        for p_state in data['solar_system_planets_state']: # Load saved planet states
            main_game_background.solar_system_planets.append({'type':'solar_system_planet','world_pos':list(p_state['world_pos']),'radius':p_state['radius'],'color':tuple(p_state['color']),'orbit_radius':p_state['orbit_radius'],'orbit_speed':p_state['orbit_speed'],'current_orbit_angle':p_state['current_orbit_angle']})

        all_garbage_objects.clear() # Clear any existing garbage in the global list
        for g_data in data['remaining_garbage']: # Load saved garbage
            all_garbage_objects.append(Garbage(g_data['world_x'],g_data['world_y'],loaded_size=g_data['size']))
        main_game_background.all_garbage_items = all_garbage_objects # Ensure Background uses the loaded garbage

        camera_x=spaceShip.x-SCREEN_WIDTH//2; camera_y=spaceShip.y-SCREEN_HEIGHT//2
        current_state = STATE_PLAYING

        autopilot_wander_timer = 0.0
        autopilot_target_wander_heading = spaceShip.current_angle
        autopilot_first_wander_decision = True

        print("Game loaded successfully."); return True
    except FileNotFoundError: print(f"Save file '{SAVE_FILE}' not found. Starting new game."); return False
    except Exception as e: print(f"Error loading game: {e}. Starting new game."); return False

def draw_world_boundary_warning(surface, ship_pos_x, ship_pos_y, cam_x, cam_y):
    """Draws a red circle indicating world boundary if ship is close."""
    dist_to_center = math.hypot(ship_pos_x - WORLD_CENTER_X, ship_pos_y - WORLD_CENTER_Y)
    if dist_to_center > WORLD_RADIUS * BOUNDARY_PROXIMITY_THRESHOLD:
        boundary_screen_x = WORLD_CENTER_X - cam_x
        boundary_screen_y = WORLD_CENTER_Y - cam_y
        warn_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        warn_surface.fill((0,0,0,0))
        # This is a simplified check; more accurate would involve checking rect intersection.
        if abs(boundary_screen_x) < SCREEN_WIDTH + WORLD_RADIUS and \
           abs(boundary_screen_y) < SCREEN_HEIGHT + WORLD_RADIUS :
            pygame.draw.circle(warn_surface, WORLD_BOUNDARY_WARN_COLOR,
                               (int(boundary_screen_x), int(boundary_screen_y)),
                               int(WORLD_RADIUS), WORLD_BOUNDARY_WARN_THICKNESS)
            surface.blit(warn_surface, (0,0))

def main_program():
    global main_game_background, all_garbage_objects, spaceShip, camera_x, camera_y
    global score, game_time, current_state, crash_time_elapsed, ship_crash_count, autopilot_on
    global autopilot_wander_timer, autopilot_target_wander_heading, autopilot_first_wander_decision

    pygame.init()
    screen = SCREEN
    clock = pygame.time.Clock()

    menu_background_instance = Background()
    menu_ship_world_x = WORLD_CENTER_X + WORLD_RADIUS * 0.5
    menu_ship_world_y = WORLD_CENTER_Y + WORLD_RADIUS * 0.5
    menu_ship = SpaceShip(menu_ship_world_x, menu_ship_world_y)
    menu_ship.is_thrusting = True
    menu_ship_rotation_speed = 0.4
    menu_camera_x = menu_ship_world_x - SCREEN_WIDTH // 2
    menu_camera_y = menu_ship_world_y - SCREEN_HEIGHT // 2

    title_text_surface = title_font.render("GREENSPACE.IO", True, TITLE_TEXT_COLOR)
    title_text_rect = title_text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
    prompt_load_text = prompt_font.render("L: Load Game", True, UI_TEXT_COLOR)
    prompt_load_rect = prompt_load_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
    prompt_new_text = prompt_font.render("N: New Game", True, UI_TEXT_COLOR)
    prompt_new_rect = prompt_new_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120))

    start_text_render = ui_font.render("Click or Press Enter to Start", True, UI_TEXT_COLOR)
    start_text_rect = start_text_render.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2+100))
    start_text_hover_render = ui_font.render("Click or Press Enter to Start", True, UI_TEXT_HOVER_COLOR)
    paused_text_render = ui_font.render("PAUSED (Click or P to Resume)", True, UI_TEXT_COLOR)
    paused_text_rect = paused_text_render.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
    paused_text_hover_render = ui_font.render("PAUSED (Click or P to Resume)", True, UI_TEXT_HOVER_COLOR)

    is_game_paused = False
    running = True
    game_fully_initialized = False # Flag to ensure full setup before certain logic (like win check)

    while running:
        dt = clock.tick(60) / 1000.0
        if dt == 0: dt = 1/60.0 # Prevent dt=0 if game is frozen momentarily
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
                elif current_state == STATE_PLAYING and spaceShip and spaceShip.alive:
                    if event.key == pygame.K_p: is_game_paused = not is_game_paused
                    elif event.key == pygame.K_SPACE: autopilot_on = not autopilot_on
                elif current_state == STATE_GAME_OVER and event.key == pygame.K_RETURN:
                    respawn_ship(); current_state = STATE_PLAYING
                elif current_state == STATE_WIN:
                    if event.key == pygame.K_RETURN: # Play Again
                        reset_game_state()
                        current_state = STATE_LOADING_PROMPT
                        game_fully_initialized = True # Re-initialize for new game
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if current_state == STATE_READY_TO_START and start_text_rect.collidepoint(mouse_pos):
                    current_state = STATE_PLAYING
                elif current_state == STATE_PLAYING and spaceShip and spaceShip.alive and is_game_paused and paused_text_rect.collidepoint(mouse_pos):
                    is_game_paused = False
                elif current_state == STATE_GAME_OVER and respawn_button_rect_outer.collidepoint(mouse_pos):
                    respawn_ship(); current_state = STATE_PLAYING
                elif current_state == STATE_WIN and play_again_button_rect_outer.collidepoint(mouse_pos): # Play Again button
                     reset_game_state()
                     current_state = STATE_LOADING_PROMPT
                     game_fully_initialized = True # Re-initialize for new game

        # Initialize wander heading once ship is ready and if entering playing state
        if game_fully_initialized and spaceShip and current_state == STATE_PLAYING and \
           (previous_game_state != STATE_PLAYING or autopilot_first_wander_decision):
             autopilot_target_wander_heading = spaceShip.current_angle
             autopilot_first_wander_decision = False # Mark as initialized for this play session


        if current_state == STATE_LOADING_PROMPT:
            menu_background_instance.update(dt)
            menu_ship.current_angle = (menu_ship.current_angle + menu_ship_rotation_speed * (dt*60)) % 360
            menu_ship.update()
        elif current_state == STATE_PLAYING:
            if not spaceShip.alive:
                if previous_game_state == STATE_PLAYING: ship_crash_count += 1; crash_time_elapsed = 0.0
                current_state = STATE_GAME_OVER
            elif not is_game_paused:
                if autopilot_on:
                    # --- AUTOPILOT CONTROLS SHIP ---
                    if spaceShip and main_game_background: # Ensure objects are available
                        ai_desired_heading, ai_should_thrust = get_autopilot_decision(
                            spaceShip, main_game_background.sun_data, main_game_background.solar_system_planets,
                            all_garbage_objects, WORLD_RADIUS, WORLD_CENTER_X, WORLD_CENTER_Y, dt
                        )
                        angle_difference = normalize_angle_degrees_180(ai_desired_heading - spaceShip.current_angle)
                        rotation_step = ROTATION_SPEED
                        if abs(angle_difference) > 1.0: # Rotation deadzone
                            if angle_difference > 0: spaceShip.current_angle = (spaceShip.current_angle + rotation_step) % 360
                            else: spaceShip.current_angle = (spaceShip.current_angle - rotation_step + 360) % 360
                        else: spaceShip.current_angle = ai_desired_heading # Snap if very close

                        spaceShip.is_thrusting = ai_should_thrust
                        if spaceShip.is_thrusting:
                            thrust_rad = math.radians(spaceShip.current_angle)
                            spaceShip.vx_1 = THRUST_MAGNITUDE * math.cos(thrust_rad); spaceShip.vy_1 = THRUST_MAGNITUDE * math.sin(thrust_rad)
                            max_v = 8.0 # Velocity cap
                            if spaceShip.vx_0 + spaceShip.vx_1 > max_v: spaceShip.vx_1 = max(0, max_v - spaceShip.vx_0)
                            if spaceShip.vx_0 + spaceShip.vx_1 < -max_v: spaceShip.vx_1 = min(0, -max_v - spaceShip.vx_0)
                            if spaceShip.vy_0 + spaceShip.vy_1 > max_v: spaceShip.vy_1 = max(0, max_v - spaceShip.vy_0)
                            if spaceShip.vy_0 + spaceShip.vy_1 < -max_v: spaceShip.vy_1 = min(0, -max_v - spaceShip.vy_0)
                        else: spaceShip.vx_1, spaceShip.vy_1 = 0.0, 0.0
                else:
                    # --- MANUAL CONTROL ---
                    spaceShip.is_thrusting = False; keys = pygame.key.get_pressed()
                    if keys[pygame.K_LEFT]: spaceShip.current_angle = (spaceShip.current_angle + ROTATION_SPEED) % 360
                    if keys[pygame.K_RIGHT]: spaceShip.current_angle = (spaceShip.current_angle - ROTATION_SPEED + 360) % 360
                    spaceShip.vx_1, spaceShip.vy_1 = 0.0, 0.0
                    if keys[pygame.K_UP]:
                        spaceShip.is_thrusting = True; thrust_rad = math.radians(spaceShip.current_angle)
                        spaceShip.vx_1 = THRUST_MAGNITUDE*math.cos(thrust_rad); spaceShip.vy_1 = THRUST_MAGNITUDE*math.sin(thrust_rad)
                        max_v = 8.0
                        if spaceShip.vx_0+spaceShip.vx_1>max_v: spaceShip.vx_1=max(0,max_v-spaceShip.vx_0)
                        if spaceShip.vx_0+spaceShip.vx_1<-max_v: spaceShip.vx_1=min(0,-max_v-spaceShip.vx_0)
                        if spaceShip.vy_0+spaceShip.vy_1>max_v: spaceShip.vy_1=max(0,max_v-spaceShip.vy_0)
                        if spaceShip.vy_0+spaceShip.vy_1<-max_v: spaceShip.vy_1=min(0,-max_v-spaceShip.vy_0)

                # Common updates for playing state
                spaceShip.update(); main_game_background.update(dt)
                for G_item in all_garbage_objects: G_item.update(spaceShip.x, spaceShip.y, dt)
                camera_x=spaceShip.x-SCREEN_WIDTH//2; camera_y=spaceShip.y-SCREEN_HEIGHT//2; game_time += dt
                ship_collider = spaceShip.get_collider_world(); collected_indices = []
                for i,G_item in enumerate(all_garbage_objects):
                    if ship_collider.colliderect(G_item.get_collider()): collected_indices.append(i); score += 1
                for i in sorted(collected_indices, reverse=True): all_garbage_objects.pop(i)

                # Check for Win Condition
                if not all_garbage_objects and game_fully_initialized and (score > 0 or game_time > 2.0) : # Win if all garbage collected after some play
                    print("Win condition met!")
                    current_state = STATE_WIN
                    if spaceShip: # Ensure ship stops moving actively
                        spaceShip.is_thrusting = False
                        spaceShip.vx_1, spaceShip.vy_1 = 0.0, 0.0

                if spaceShip.alive: # Continue with collision checks only if alive
                    sr = spaceShip.get_collider_world().width / 2.2
                    if (spaceShip.x - WORLD_CENTER_X)**2 + (spaceShip.y - WORLD_CENTER_Y)**2 < (SUN_RADIUS + sr)**2: spaceShip.explode()
                    if spaceShip.alive:
                        for p in main_game_background.solar_system_planets:
                            if (spaceShip.x - p['world_pos'][0])**2 + (spaceShip.y - p['world_pos'][1])**2 < (p['radius'] + sr)**2:
                                spaceShip.explode(); break
                        if spaceShip.alive and math.hypot(spaceShip.x - WORLD_CENTER_X, spaceShip.y - WORLD_CENTER_Y) > WORLD_RADIUS - sr:
                            spaceShip.explode()
        elif current_state == STATE_GAME_OVER:
            crash_time_elapsed += dt
            if spaceShip: spaceShip.update() # Keep updating explosion particles
            if main_game_background: main_game_background.update(dt) # Keep planets orbiting
        elif current_state == STATE_WIN:
            if main_game_background: main_game_background.update(dt) # Keep background animated
            if spaceShip:
                spaceShip.is_thrusting = False # Ensure ship is not thrusting on win screen
                spaceShip.update() # Update particles if any from previous state

        # Drawing logic
        screen.fill((0,0,0))
        if current_state == STATE_LOADING_PROMPT:
            menu_background_instance.draw(screen, menu_camera_x, menu_camera_y)
            menu_ship.draw(screen, menu_camera_x, menu_camera_y)
            screen.blit(title_text_surface, title_text_rect)
            if not os.path.exists(SAVE_FILE):
                screen.blit(prompt_new_text, prompt_new_rect)
                no_save_text = prompt_font.render("No save file found.", True, UI_TEXT_COLOR)
                no_save_rect = no_save_text.get_rect(center=(SCREEN_WIDTH//2, prompt_load_rect.top - 60))
                screen.blit(no_save_text, no_save_rect)
            else:
                screen.blit(prompt_load_text, prompt_load_rect)
                screen.blit(prompt_new_text, prompt_new_rect)
        elif main_game_background and spaceShip: # Main drawing block for PLAYING, GAME_OVER, WIN
            main_game_background.draw(screen, camera_x, camera_y)
            if current_state == STATE_PLAYING: # Only draw boundary warning when actively playing
                draw_world_boundary_warning(screen, spaceShip.x, spaceShip.y, camera_x, camera_y)
            # Draw garbage if any (e.g. for game over screen or if win screen still shows them)
            for G_item in all_garbage_objects: G_item.draw(screen, camera_x, camera_y)
            spaceShip.draw(screen, camera_x, camera_y)

            if current_state == STATE_READY_TO_START:
                txt = start_text_hover_render if start_text_rect.collidepoint(mouse_pos) else start_text_render
                screen.blit(txt, start_text_rect)
            elif current_state == STATE_PLAYING:
                if is_game_paused:
                    txt = paused_text_hover_render if paused_text_rect.collidepoint(mouse_pos) else paused_text_render
                    screen.blit(txt, paused_text_rect)
                else: # In-game HUD elements
                    s_surf=score_font.render(f"Score: {score}",True,SCORE_TEXT_COLOR); screen.blit(s_surf,(20,20))
                    g_surf=debug_font.render(f"Garbage: {len(all_garbage_objects)}",True,UI_TEXT_COLOR); screen.blit(g_surf,(20,s_surf.get_height()+25))

                autopilot_text_str = "Automatic Pilot ON" if autopilot_on else "Automatic Pilot OFF"
                autopilot_text_color = AUTOPILOT_ON_COLOR if autopilot_on else AUTOPILOT_OFF_COLOR
                autopilot_surf = autopilot_font.render(autopilot_text_str, True, autopilot_text_color)
                autopilot_rect = autopilot_surf.get_rect(center=(SCREEN_WIDTH // 2, 30))
                screen.blit(autopilot_surf, autopilot_rect)

                if spaceShip: draw_minimap(screen,spaceShip,main_game_background,camera_x,camera_y,all_garbage_objects)
            elif current_state == STATE_GAME_OVER:
                go_surf=game_over_font.render("GAME OVER",True,GAMEOVER_TEXT_COLOR); go_r=go_surf.get_rect(center=(SCREEN_WIDTH//2,SCREEN_HEIGHT//2-120)); screen.blit(go_surf,go_r)
                fs_surf=score_font.render(f"Final Score: {score}",True,SCORE_TEXT_COLOR); fs_r=fs_surf.get_rect(center=(SCREEN_WIDTH//2,go_r.bottom+35)); screen.blit(fs_surf,fs_r)
                ct_surf=crash_timer_font.render(f"Time Since Crash: {crash_time_elapsed:.1f}s",True,CRASH_TIMER_TEXT_COLOR); ct_r=ct_surf.get_rect(center=(SCREEN_WIDTH//2,fs_r.bottom+35)); screen.blit(ct_surf,ct_r)
                cc_surf=crash_count_font.render(f"Crashes: {ship_crash_count}",True,CRASH_COUNT_TEXT_COLOR); cc_r=cc_surf.get_rect(center=(SCREEN_WIDTH//2,ct_r.bottom+35)); screen.blit(cc_surf,cc_r)
                btn_c = RESTART_BUTTON_BG_HOVER_COLOR if respawn_button_rect_outer.collidepoint(mouse_pos) else RESTART_BUTTON_BG_COLOR
                pygame.draw.rect(screen,btn_c,respawn_button_rect_outer,border_radius=10); screen.blit(respawn_button_text_surface,respawn_button_rect_inner)
                if spaceShip and main_game_background: draw_minimap(screen,spaceShip,main_game_background,camera_x,camera_y,all_garbage_objects)
            elif current_state == STATE_WIN:
                screen.blit(win_text_surface, win_text_rect)
                final_score_text = f"Final Score: {score}"
                final_score_surf = win_info_font.render(final_score_text, True, SCORE_TEXT_COLOR)
                final_score_rect = final_score_surf.get_rect(center=(SCREEN_WIDTH // 2, win_text_rect.bottom + 70))
                screen.blit(final_score_surf, final_score_rect)
                final_time_text = f"Clear Time: {game_time:.1f} seconds"
                final_time_surf = win_info_font.render(final_time_text, True, WIN_INFO_COLOR)
                final_time_rect = final_time_surf.get_rect(center=(SCREEN_WIDTH // 2, final_score_rect.bottom + 50))
                screen.blit(final_time_surf, final_time_rect)
                btn_bg_color_win = RESTART_BUTTON_BG_HOVER_COLOR if play_again_button_rect_outer.collidepoint(mouse_pos) else RESTART_BUTTON_BG_COLOR
                pygame.draw.rect(screen, btn_bg_color_win, play_again_button_rect_outer, border_radius=10)
                screen.blit(play_again_button_text_surface, play_again_button_rect_inner)
                if spaceShip and main_game_background: draw_minimap(screen,spaceShip,main_game_background,camera_x,camera_y,all_garbage_objects) # Minimap on win screen

        pygame.display.flip()

    if spaceShip and ((current_state == STATE_PLAYING and spaceShip.alive) or current_state == STATE_GAME_OVER):
        save_game()

    pygame.quit()

if __name__ == '__main__':
    main_program()
