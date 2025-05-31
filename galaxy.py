# galaxy.py

import pygame
import random
import math
from config import SCREEN_WIDTH, SCREEN_HEIGHT, WORLD_RADIUS, WORLD_CENTER_X, WORLD_CENTER_Y, \
                   SUN_RADIUS, SUN_COLOR, NUM_SOLAR_SYSTEM_PLANETS, MIN_ORBIT_RADIUS, MAX_ORBIT_RADIUS

try:
    from config import CELL_SIZE
except ImportError:
    CELL_SIZE = 200

# --- Helper function for pixel art circle (used for planets) ---
def draw_pixel_circle(surface, color, center_x, center_y, radius):
    radius = int(radius)
    # Basic culling for the circle based on its bounding box
    # center_x and center_y are already screen coordinates here
    if center_x + radius < 0 or center_x - radius > SCREEN_WIDTH or \
       center_y + radius < 0 or center_y - radius > SCREEN_HEIGHT:
        return

    # Use pygame.draw.circle for performance.
    # For small radii, it will still look quite pixelated.
    pygame.draw.circle(surface, color, (int(center_x), int(center_y)), radius)


# --- Helper function for pixel art star ---
def draw_pixel_star(surface, screen_x, screen_y, base_color, size_category):
    core_size = 1
    if size_category == 'medium': core_size = 2
    elif size_category == 'large': core_size = random.choice([3, 4, 5])

    core_rect_x_float = screen_x - core_size // 2
    core_rect_y_float = screen_y - core_size // 2
    core_rect_x_int = int(core_rect_x_float)
    core_rect_y_int = int(core_rect_y_float)

    if core_rect_x_int + core_size < 0 or core_rect_x_int > SCREEN_WIDTH or \
       core_rect_y_int + core_size < 0 or core_rect_y_int > SCREEN_HEIGHT:
        return

    pygame.draw.rect(surface, base_color, (core_rect_x_int, core_rect_y_int, core_size, core_size))

    glow_alpha_value = random.randint(25, 75)
    r, g, b = base_color
    glow_color = (r, g, b, glow_alpha_value)

    if size_category == 'medium' or size_category == 'small':
        for dx_glow, dy_glow in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            gx_float, gy_float = screen_x + dx_glow, screen_y + dy_glow
            gx_int, gy_int = int(gx_float), int(gy_float)
            if 0 <= gx_int < SCREEN_WIDTH and 0 <= gy_int < SCREEN_HEIGHT:
                glow_pixel_surface = pygame.Surface((1,1), pygame.SRCALPHA)
                glow_pixel_surface.fill(glow_color)
                surface.blit(glow_pixel_surface, (gx_int, gy_int))
    elif size_category == 'large':
        glow_radius = core_size
        for dx_glow in range(-glow_radius, glow_radius + 1):
            for dy_glow in range(-glow_radius, glow_radius + 1):
                if abs(dx_glow) + abs(dy_glow) > 0 and abs(dx_glow) + abs(dy_glow) <= glow_radius :
                    if random.random() < 0.4:
                        gx_float, gy_float = screen_x + dx_glow, screen_y + dy_glow
                        gx_int, gy_int = int(gx_float), int(gy_float)
                        if 0 <= gx_int < SCREEN_WIDTH and 0 <= gy_int < SCREEN_HEIGHT:
                            glow_pixel_surface = pygame.Surface((1,1), pygame.SRCALPHA)
                            glow_pixel_surface.fill(glow_color)
                            surface.blit(glow_pixel_surface, (gx_int, gy_int))

class Background:
    def __init__(self):
        self.bg_color = (15, 0, 30)
        self.world_min_x = WORLD_CENTER_X - WORLD_RADIUS
        self.world_min_y = WORLD_CENTER_Y - WORLD_RADIUS
        self.world_width = WORLD_RADIUS * 2
        self.world_height = WORLD_RADIUS * 2
        self.grid_cols = math.ceil(self.world_width / CELL_SIZE)
        self.grid_rows = math.ceil(self.world_height / CELL_SIZE)
        self.grid = [[[] for _ in range(self.grid_cols)] for _ in range(self.grid_rows)]

        self._all_stars_data = []
        self._all_galactic_gas_data = []
        self._all_dust_lanes_data = []
        self._all_distant_planets_data = []
        self.solar_system_planets = []

        self.sun_data = {
            'type': 'sun',
            'world_pos': (WORLD_CENTER_X, WORLD_CENTER_Y),
            'radius': SUN_RADIUS,
            'color': SUN_COLOR
        }

        self._generate_solar_system_orbiting_planets()
        self._generate_galactic_band_data()
        self._generate_outer_stars_data()
        self._generate_distant_planets_data()

        self._populate_grid()

        self.stars = self._all_stars_data
        self.galactic_gas = self._all_galactic_gas_data
        self.dust_lanes = self._all_dust_lanes_data
        self.planets = self._all_distant_planets_data

    def _get_grid_coords(self, world_x, world_y):
        grid_x = int((world_x - self.world_min_x) / CELL_SIZE)
        grid_y = int((world_y - self.world_min_y) / CELL_SIZE)
        grid_x = max(0, min(grid_x, self.grid_cols - 1))
        grid_y = max(0, min(grid_y, self.grid_rows - 1))
        return grid_x, grid_y

    def _populate_grid(self):
        # Add sun to the grid
        gx, gy = self._get_grid_coords(self.sun_data['world_pos'][0], self.sun_data['world_pos'][1])
        self.grid[gy][gx].append(self.sun_data)

        # Static elements are added to the grid
        all_static_elements = self._all_stars_data + self._all_galactic_gas_data + \
                              self._all_dust_lanes_data + self._all_distant_planets_data
        for item in all_static_elements:
            gx, gy = self._get_grid_coords(item['world_pos'][0], item['world_pos'][1])
            self.grid[gy][gx].append(item)

        # Orbiting solar_system_planets are NOT added to the static grid here,
        # as their positions change. They will be drawn from their dedicated list.

    def _generate_element_in_world_circle(self, radius_factor=1.0):
        while True:
            angle = random.uniform(0, 2 * math.pi)
            r = math.sqrt(random.random()) * WORLD_RADIUS * radius_factor
            x = WORLD_CENTER_X + r * math.cos(angle)
            y = WORLD_CENTER_Y + r * math.sin(angle)
            if math.hypot(x - WORLD_CENTER_X, y - WORLD_CENTER_Y) <= WORLD_RADIUS * radius_factor:
                return int(x), int(y)

    def _generate_solar_system_orbiting_planets(self):
        planet_colors_ss = [
            (150, 100, 50), (100, 150, 100), (100, 100, 200),
            (200, 150, 100), (180, 180, 180)
        ]
        current_orbit_radius = MIN_ORBIT_RADIUS
        for i in range(NUM_SOLAR_SYSTEM_PLANETS):
            orbit_radius = current_orbit_radius + random.uniform(0, (MAX_ORBIT_RADIUS - MIN_ORBIT_RADIUS) / (NUM_SOLAR_SYSTEM_PLANETS * 0.8 if NUM_SOLAR_SYSTEM_PLANETS > 0 else 1) )
            if orbit_radius > MAX_ORBIT_RADIUS: orbit_radius = MAX_ORBIT_RADIUS

            current_orbit_angle = random.uniform(0, 2 * math.pi)
            orbit_speed = random.uniform(0.02, 0.1) / (1 + (orbit_radius / MAX_ORBIT_RADIUS)*2) # Slower speeds

            planet_radius = random.randint(150, 1000)
            color = random.choice(planet_colors_ss)

            world_x = WORLD_CENTER_X + orbit_radius * math.cos(current_orbit_angle)
            world_y = WORLD_CENTER_Y + orbit_radius * math.sin(current_orbit_angle)

            self.solar_system_planets.append({
                'type': 'solar_system_planet', # Important for minimap and potential future logic
                'world_pos': [world_x, world_y],
                'radius': planet_radius,
                'color': color,
                'orbit_radius': orbit_radius,
                'orbit_speed': orbit_speed,
                'current_orbit_angle': current_orbit_angle
            })
            current_orbit_radius = orbit_radius + planet_radius * 2 + random.uniform(50,150)

    def _generate_galactic_band_data(self):
        # Your existing values are preserved
        num_segments = 32; path_points = []; path_start_x = WORLD_CENTER_X - WORLD_RADIUS*0.8; path_end_x = WORLD_CENTER_X + WORLD_RADIUS*0.8
        current_y = WORLD_CENTER_Y + random.randint(-WORLD_RADIUS//4, WORLD_RADIUS//4); path_points.append((path_start_x, current_y))
        for i in range(1,num_segments+1):
            px = path_start_x+(i/num_segments)*(path_end_x-path_start_x); py_offset_scale=WORLD_RADIUS/2.5
            py_offset=math.sin(i/num_segments*math.pi*random.uniform(1.5,2.5)+random.uniform(-0.5,0.5))*py_offset_scale
            py_drift=random.randint(-WORLD_RADIUS//15, WORLD_RADIUS//15); current_y=current_y+py_drift/num_segments; py=current_y+py_offset
            py=max(WORLD_CENTER_Y-WORLD_RADIUS*0.4,min(WORLD_CENTER_Y+WORLD_RADIUS*0.4,py)); path_points.append((int(px),int(py)))
        path_points.append((path_end_x,WORLD_CENTER_Y+random.randint(-WORLD_RADIUS//4,WORLD_RADIUS//4)))
        band_colors=[(255,220,180),(255,200,150),(240,180,120),(255,150,100),(230,120,80)]; num_gas_blobs=20000
        band_thickness=WORLD_RADIUS/random.uniform(4.0,6.0)
        for i in range(len(path_points)-1):
            p1,p2=pygame.math.Vector2(path_points[i]),pygame.math.Vector2(path_points[i+1]); segment_length=p1.distance_to(p2)
            if segment_length==0:continue
            segment_blobs=int((num_gas_blobs/(num_segments-1 if num_segments > 1 else 1))*(segment_length/((WORLD_RADIUS*2)/(num_segments if num_segments > 0 else 1))))
            for _ in range(segment_blobs):
                t=random.random();current_path_pos=p1.lerp(p2,t)
                dist_from_center=random.normalvariate(0,band_thickness/2.5);dist_from_center=max(-band_thickness*0.8,min(band_thickness*0.8,dist_from_center))
                perp_vec=(p2-p1).rotate(90).normalize() if (p2-p1).length_squared()>0 else pygame.math.Vector2(0,1)
                blob_pos_vec=current_path_pos+perp_vec*dist_from_center+pygame.math.Vector2(random.uniform(-10,10),random.uniform(-10,10))
                blob_size=random.randint(5,15);alpha=random.randint(10,40);color=random.choice(band_colors)
                blob_surface=pygame.Surface((blob_size,blob_size),pygame.SRCALPHA);blob_surface.fill((color[0],color[1],color[2],alpha))
                self._all_galactic_gas_data.append({'type':'gas_blob','surface':blob_surface,'world_pos':(int(blob_pos_vec.x),int(blob_pos_vec.y))})
        num_band_stars=20000; star_colors_band=[(255,255,240),(255,240,220),(255,200,200),(200,220,255)]
        for i in range(len(path_points)-1):
            p1,p2=pygame.math.Vector2(path_points[i]),pygame.math.Vector2(path_points[i+1]); segment_length=p1.distance_to(p2)
            if segment_length==0:continue
            segment_stars=int((num_band_stars/(num_segments-1 if num_segments > 1 else 1))*(segment_length/((WORLD_RADIUS*2)/(num_segments if num_segments > 0 else 1))))
            for _ in range(segment_stars):
                t=random.random();current_path_pos=p1.lerp(p2,t)
                dist_from_center=random.normalvariate(0,band_thickness/1.5);dist_from_center=max(-band_thickness*1.2,min(band_thickness*1.2,dist_from_center))
                perp_vec=(p2-p1).rotate(90).normalize() if (p2-p1).length_squared()>0 else pygame.math.Vector2(0,1)
                star_pos_vec=current_path_pos+perp_vec*dist_from_center+pygame.math.Vector2(random.uniform(-30,30),random.uniform(-30,30))
                if math.hypot(star_pos_vec.x-WORLD_CENTER_X,star_pos_vec.y-WORLD_CENTER_Y)<=WORLD_RADIUS:
                    size_cat=random.choice(['small','medium','medium','large']);base_c=random.choice(star_colors_band)
                    brightness_mod=random.uniform(0.8,1.2);final_c=(min(255,int(base_c[0]*brightness_mod)),min(255,int(base_c[1]*brightness_mod)),min(255,int(base_c[2]*brightness_mod)))
                    self._all_stars_data.append({'type':'star','world_pos':(int(star_pos_vec.x),int(star_pos_vec.y)),'color':final_c,'size_cat':size_cat})
        num_dust_lanes=60000; dust_color=(20,15,10)
        for i in range(len(path_points)-1):
            p1,p2=pygame.math.Vector2(path_points[i]),pygame.math.Vector2(path_points[i+1]); segment_length=p1.distance_to(p2)
            if segment_length==0:continue
            segment_dust=int((num_dust_lanes/(num_segments-1 if num_segments > 1 else 1))*(segment_length/((WORLD_RADIUS*2)/(num_segments if num_segments > 0 else 1))))
            for _ in range(segment_dust):
                t=random.random();current_path_pos=p1.lerp(p2,t)
                dist_from_center=random.normalvariate(0,band_thickness/2.5);dist_from_center=max(-band_thickness*0.7,min(band_thickness*0.7,dist_from_center))
                perp_vec=(p2-p1).rotate(random.choice([-80,-90,-100,80,90,100])).normalize() if (p2-p1).length_squared()>0 else pygame.math.Vector2(0,1)
                dust_pos_vec=current_path_pos+perp_vec*dist_from_center+pygame.math.Vector2(random.uniform(-15,15),random.uniform(-15,15))
                if math.hypot(dust_pos_vec.x-WORLD_CENTER_X,dust_pos_vec.y-WORLD_CENTER_Y)<=WORLD_RADIUS:
                    blob_size=random.randint(8,25);alpha=random.randint(50,120)
                    blob_surface=pygame.Surface((blob_size,blob_size),pygame.SRCALPHA);blob_surface.fill((dust_color[0],dust_color[1],dust_color[2],alpha))
                    self._all_dust_lanes_data.append({'type':'dust_blob','surface':blob_surface,'world_pos':(int(dust_pos_vec.x),int(dust_pos_vec.y))})

    def _generate_outer_stars_data(self):
        num_outer_stars = 200000 # Your value
        star_colors_outer = [(200,200,220), (180,180,200), (220,220,255)]
        for _ in range(num_outer_stars):
            angle=random.uniform(0,2*math.pi);r_norm=1.0-math.sqrt(1.0-random.random());r=WORLD_RADIUS*r_norm
            if r < WORLD_RADIUS:r=WORLD_RADIUS*(0.4+(1.0-0.4)*math.sqrt(random.random()))
            x=int(WORLD_CENTER_X+r*math.cos(angle));y=int(WORLD_CENTER_Y+r*math.sin(angle))
            if math.hypot(x-WORLD_CENTER_X,y-WORLD_CENTER_Y)<=WORLD_RADIUS:
                size_cat=random.choice(['small','small','medium']);base_c=random.choice(star_colors_outer)
                brightness_mod=random.uniform(0.5,0.9);final_c=(min(255,int(base_c[0]*brightness_mod)),min(255,int(base_c[1]*brightness_mod)),min(255,int(base_c[2]*brightness_mod)))
                self._all_stars_data.append({'type':'star','world_pos':(x,y),'color':final_c,'size_cat':size_cat})

    def _generate_distant_planets_data(self):
        num_planets = 6000 # Your value
        planet_colors = [(80,80,110),(110,80,80),(80,110,80),(110,110,80)]
        for _ in range(num_planets):
            x,y=self._generate_element_in_world_circle(0.95)
            radius=random.randint(3,7)
            path_y_range=(WORLD_CENTER_Y-WORLD_RADIUS*0.2,WORLD_CENTER_Y+WORLD_RADIUS*0.2)
            if path_y_range[0]<y<path_y_range[1]:
                if random.random() < 0.7:continue
            color=random.choice(planet_colors)
            self._all_distant_planets_data.append({'type':'distant_planet','world_pos':(x,y),'radius':radius,'color':color})

    def update(self, dt):
        for planet_data in self.solar_system_planets:
            planet_data['current_orbit_angle'] += planet_data['orbit_speed'] * dt
            planet_data['world_pos'][0] = WORLD_CENTER_X + planet_data['orbit_radius'] * math.cos(planet_data['current_orbit_angle'])
            planet_data['world_pos'][1] = WORLD_CENTER_Y + planet_data['orbit_radius'] * math.sin(planet_data['current_orbit_angle'])

    def draw(self, surface, camera_x, camera_y):
        surface.fill(self.bg_color)

        cam_min_gx = int((camera_x - self.world_min_x) / CELL_SIZE)
        cam_max_gx = int(((camera_x + SCREEN_WIDTH) - self.world_min_x) / CELL_SIZE)
        cam_min_gy = int((camera_y - self.world_min_y) / CELL_SIZE)
        cam_max_gy = int(((camera_y + SCREEN_HEIGHT) - self.world_min_y) / CELL_SIZE)

        start_col = max(0, cam_min_gx); end_col = min(self.grid_cols - 1, cam_max_gx)
        start_row = max(0, cam_min_gy); end_row = min(self.grid_rows - 1, cam_max_gy)

        visible_gas = []; visible_dust = []; visible_stars = []; visible_distant_planets = []
        # Note: solar_system_planets will be drawn separately from their own list

        for gy in range(start_row, end_row + 1):
            for gx in range(start_col, end_col + 1):
                for item in self.grid[gy][gx]:
                    item_type = item.get('type')
                    if item_type == 'gas_blob': visible_gas.append(item)
                    elif item_type == 'dust_blob': visible_dust.append(item)
                    elif item_type == 'star': visible_stars.append(item)
                    elif item_type == 'distant_planet': visible_distant_planets.append(item)
                    # Sun and solar_system_planets are not retrieved from grid for drawing here

        for gas_blob in visible_gas:
            screen_x = gas_blob['world_pos'][0] - camera_x; screen_y = gas_blob['world_pos'][1] - camera_y
            blob_surf = gas_blob['surface']; blob_s = blob_surf.get_size()
            if screen_x + blob_s[0] > 0 and screen_x < SCREEN_WIDTH and screen_y + blob_s[1] > 0 and screen_y < SCREEN_HEIGHT:
                surface.blit(blob_surf, (screen_x, screen_y))
        for dust_blob in visible_dust:
            screen_x = dust_blob['world_pos'][0] - camera_x; screen_y = dust_blob['world_pos'][1] - camera_y
            blob_surf = dust_blob['surface']; blob_s = blob_surf.get_size()
            if screen_x + blob_s[0] > 0 and screen_x < SCREEN_WIDTH and screen_y + blob_s[1] > 0 and screen_y < SCREEN_HEIGHT:
                surface.blit(blob_surf, (screen_x, screen_y))
        for star_data in visible_stars:
            screen_x = star_data['world_pos'][0] - camera_x; screen_y = star_data['world_pos'][1] - camera_y
            draw_pixel_star(surface, screen_x, screen_y, star_data['color'], star_data['size_cat'])

        # Draw Distant Planets (the 6000 tiny ones from the grid)
        for planet_data in visible_distant_planets:
            planet_world_pos = planet_data['world_pos']
            radius = planet_data['radius']
            screen_x = planet_world_pos[0] - camera_x
            screen_y = planet_world_pos[1] - camera_y
            draw_pixel_circle(surface, planet_data['color'], screen_x, screen_y, radius)

        # Draw Solar System Planets (orbiting ones) - from their own list
        for planet_data in self.solar_system_planets:
            planet_world_pos = planet_data['world_pos']
            radius = planet_data['radius']
            screen_x = planet_world_pos[0] - camera_x
            screen_y = planet_world_pos[1] - camera_y
            # Culling for solar system planets
            if not (screen_x + radius < 0 or screen_x - radius > SCREEN_WIDTH or \
                    screen_y + radius < 0 or screen_y - radius > SCREEN_HEIGHT):
                draw_pixel_circle(surface, planet_data['color'], screen_x, screen_y, radius)

        sun_screen_x = self.sun_data['world_pos'][0] - camera_x
        sun_screen_y = self.sun_data['world_pos'][1] - camera_y
        if not (sun_screen_x + SUN_RADIUS < 0 or sun_screen_x - SUN_RADIUS > SCREEN_WIDTH or \
                sun_screen_y + SUN_RADIUS < 0 or sun_screen_y - SUN_RADIUS > SCREEN_HEIGHT):
            pygame.draw.circle(surface, self.sun_data['color'], (int(sun_screen_x), int(sun_screen_y)), self.sun_data['radius'])
