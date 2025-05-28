# galaxy.py
import pygame
import random
import math
from config import SCREEN_WIDTH, SCREEN_HEIGHT

# --- Helper function for pixel art circle (used for planets) ---
def draw_pixel_circle(surface, color, center_x, center_y, radius):
    # Ensure radius is an integer for range function
    radius = int(radius)
    for y in range(-radius, radius + 1):
        for x in range(-radius, radius + 1):
            if x*x + y*y <= radius*radius:
                px = center_x + x
                py = center_y + y
                if 0 <= px < SCREEN_WIDTH and 0 <= py < SCREEN_HEIGHT:
                    surface.set_at((px, py), color)

# --- Helper function for pixel art star ---
def draw_pixel_star(surface, center_x, center_y, base_color, size_category):
    core_size = 1
    if size_category == 'medium':
        core_size = 2
    elif size_category == 'large':
        core_size = random.choice([3, 4, 5])

    core_rect_x = center_x - core_size // 2
    core_rect_y = center_y - core_size // 2
    if 0 <= core_rect_x < SCREEN_WIDTH and \
       0 <= core_rect_y < SCREEN_HEIGHT and \
       core_rect_x + core_size <= SCREEN_WIDTH and \
       core_rect_y + core_size <= SCREEN_HEIGHT:
        pygame.draw.rect(surface, base_color, (core_rect_x, core_rect_y, core_size, core_size))

    glow_alpha_value = random.randint(25, 75)
    r, g, b = base_color
    glow_color = (r, g, b, glow_alpha_value)

    if size_category == 'medium' or size_category == 'small':
        for dx_glow, dy_glow in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            gx, gy = center_x + dx_glow, center_y + dy_glow
            if 0 <= gx < SCREEN_WIDTH and 0 <= gy < SCREEN_HEIGHT:
                glow_pixel_surface = pygame.Surface((1,1), pygame.SRCALPHA)
                glow_pixel_surface.fill(glow_color)
                surface.blit(glow_pixel_surface, (gx, gy))
    elif size_category == 'large':
        glow_radius = core_size
        for dx_glow in range(-glow_radius, glow_radius + 1):
            for dy_glow in range(-glow_radius, glow_radius + 1):
                if abs(dx_glow) + abs(dy_glow) > 0 and abs(dx_glow) + abs(dy_glow) <= glow_radius :
                    if random.random() < 0.4:
                        gx, gy = center_x + dx_glow, center_y + dy_glow
                        if 0 <= gx < SCREEN_WIDTH and 0 <= gy < SCREEN_HEIGHT:
                            glow_pixel_surface = pygame.Surface((1,1), pygame.SRCALPHA)
                            glow_pixel_surface.fill(glow_color)
                            surface.blit(glow_pixel_surface, (gx, gy))


class Background:
    def __init__(self):
        self.bg_color = (15, 0, 30)

        self.stars = []
        self.galactic_gas = []
        self.dust_lanes = []
        self.planets = []

        self._generate_galactic_band()
        self._generate_outer_stars()
        self._generate_distant_planets()

    def _generate_galactic_band(self):
        num_segments = 32
        path_points = []

        start_y = random.randint(SCREEN_HEIGHT // 3, 2 * SCREEN_HEIGHT // 3)
        path_points.append((0, start_y))
        for i in range(1, num_segments + 1):
            px = (i / num_segments) * SCREEN_WIDTH
            py_offset = math.sin(i / num_segments * math.pi * 2 + random.uniform(-0.5, 0.5)) * (SCREEN_HEIGHT / random.uniform(3.5, 5))
            py = start_y + py_offset + random.randint(-SCREEN_HEIGHT // 10, SCREEN_HEIGHT // 10)
            py = max(SCREEN_HEIGHT // 4, min(3 * SCREEN_HEIGHT // 4, py))
            path_points.append((int(px), int(py)))
        path_points.append((SCREEN_WIDTH, random.randint(SCREEN_HEIGHT // 3, 2 * SCREEN_HEIGHT // 3)))

        band_colors = [
            (255, 220, 180), (255, 200, 150), (240, 180, 120),
            (255, 150, 100), (230, 120, 80)
        ]
        num_gas_blobs = 2500
        band_thickness = SCREEN_HEIGHT // random.uniform(3.5, 5.5)

        for i in range(len(path_points) - 1):
            p1 = path_points[i]
            p2 = path_points[i+1]

            steps = int(pygame.math.Vector2(p2[0]-p1[0], p2[1]-p1[1]).length() / 20)
            steps = max(1, steps)

            for step in range(steps):
                t = step / steps
                current_path_x = p1[0] + t * (p2[0] - p1[0])
                current_path_y = p1[1] + t * (p2[1] - p1[1])

                for _ in range(num_gas_blobs // (num_segments * steps) + 1):
                    dist_from_center = random.normalvariate(0, band_thickness / 2.5)
                    dist_from_center = max(-band_thickness * 0.8, min(band_thickness * 0.8, dist_from_center))
                    blob_x = int(current_path_x + random.uniform(-10, 10))
                    blob_y = int(current_path_y + dist_from_center)
                    blob_size = random.randint(1, 8)
                    alpha = random.randint(10, 50)
                    color = random.choice(band_colors)

                    blob_surface = pygame.Surface((blob_size, blob_size), pygame.SRCALPHA)
                    blob_surface.fill((color[0], color[1], color[2], alpha))
                    self.galactic_gas.append({'surface': blob_surface, 'pos': (blob_x, blob_y)})

        num_band_stars = 400
        star_colors_band = [
            (255, 255, 240), (255, 240, 220),
            (255, 200, 200), (200, 220, 255)
        ]
        for i in range(len(path_points) - 1):
            p1, p2 = path_points[i], path_points[i+1]
            for _ in range(num_band_stars // num_segments):
                t = random.random()
                current_path_x = p1[0] + t * (p2[0] - p1[0])
                current_path_y = p1[1] + t * (p2[1] - p1[1])
                dist_from_center = random.normalvariate(0, band_thickness / 2.0)
                dist_from_center = max(-band_thickness, min(band_thickness, dist_from_center))
                star_x = int(current_path_x + random.uniform(-20, 20))
                star_y = int(current_path_y + dist_from_center)

                if 0 <= star_x < SCREEN_WIDTH and 0 <= star_y < SCREEN_HEIGHT:
                    size_cat = random.choice(['small', 'medium', 'medium', 'large'])
                    base_c = random.choice(star_colors_band)
                    brightness_mod = random.uniform(0.8, 1.2)
                    final_c = (min(255, int(base_c[0]*brightness_mod)), min(255, int(base_c[1]*brightness_mod)), min(255, int(base_c[2]*brightness_mod)))
                    self.stars.append({'pos': (star_x, star_y), 'color': final_c, 'size_cat': size_cat})

        num_dust_lanes = 500
        dust_color = (20, 15, 10)
        for i in range(len(path_points) - 1):
            p1, p2 = path_points[i], path_points[i+1]
            for _ in range(num_dust_lanes // num_segments):
                t = random.random()
                current_path_x = p1[0] + t * (p2[0] - p1[0])
                current_path_y = p1[1] + t * (p2[1] - p1[1])
                dist_from_center = random.normalvariate(0, band_thickness / 3)
                dist_from_center = max(-band_thickness*0.6, min(band_thickness*0.6, dist_from_center))
                dust_x = int(current_path_x + random.uniform(-10,10))
                dust_y = int(current_path_y + dist_from_center + random.uniform(-band_thickness*0.1, band_thickness*0.1))
                blob_size = random.randint(5, 20)
                alpha = random.randint(40, 100)

                blob_surface = pygame.Surface((blob_size, blob_size), pygame.SRCALPHA)
                blob_surface.fill((dust_color[0], dust_color[1], dust_color[2], alpha))
                self.dust_lanes.append({'surface': blob_surface, 'pos': (dust_x, dust_y)})

    def _generate_outer_stars(self):
        num_outer_stars = 1500
        star_colors_outer = [(200,200,220), (180,180,200), (220,220,255)]
        for _ in range(num_outer_stars):
            x = random.randint(0, SCREEN_WIDTH - 1)
            y = random.randint(0, SCREEN_HEIGHT - 1)

            if SCREEN_HEIGHT // 3 < y < 2 * SCREEN_HEIGHT // 3 and random.random() < 0.7:
                 continue

            if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
                size_cat = random.choice(['small', 'small', 'medium'])
                base_c = random.choice(star_colors_outer)
                brightness_mod = random.uniform(0.6, 1.0)
                final_c = (min(255, int(base_c[0]*brightness_mod)), min(255, int(base_c[1]*brightness_mod)), min(255, int(base_c[2]*brightness_mod)))
                self.stars.append({'pos': (x, y), 'color': final_c, 'size_cat': size_cat})

    def _generate_distant_planets(self):
        num_planets = random.randint(20, 100)
        planet_colors = [
            (80, 80, 100), (100, 80, 80), (80, 100, 80),
            (90, 90, 70)
        ]
        for _ in range(num_planets):
            x = random.randint(0, SCREEN_WIDTH -1)
            y = random.randint(0, SCREEN_HEIGHT -1)
            radius = random.randint(3, 6)

            is_near_band = False
            if SCREEN_HEIGHT * 0.4 < y < SCREEN_HEIGHT * 0.6:
                if SCREEN_WIDTH * 0.2 < x < SCREEN_WIDTH * 0.8:
                    if random.random() < 0.8:
                        continue

            color = random.choice(planet_colors)
            self.planets.append({'pos': (x,y), 'radius': radius, 'color': color})


    def draw(self, surface):
        surface.fill(self.bg_color)

        for gas_blob in self.galactic_gas:
            surface.blit(gas_blob['surface'], gas_blob['pos'])

        for dust_blob in self.dust_lanes:
            surface.blit(dust_blob['surface'], dust_blob['pos'])

        for star_data in self.stars:
            draw_pixel_star(surface, star_data['pos'][0], star_data['pos'][1], star_data['color'], star_data['size_cat'])

        # Draw planets
        for planet_data in self.planets:
            center_coords = planet_data['pos']
            radius = planet_data['radius']
            color = planet_data['color']
            draw_pixel_circle(surface, color, center_coords[0], center_coords[1], radius)
