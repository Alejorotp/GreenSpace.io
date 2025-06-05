# galaxy.py

import pygame
import random
import math
from config import (SCREEN_WIDTH, SCREEN_HEIGHT, WORLD_RADIUS, WORLD_CENTER_X, WORLD_CENTER_Y,
                    SUN_RADIUS, SUN_COLOR, NUM_SOLAR_SYSTEM_PLANETS, MIN_ORBIT_RADIUS,
                    MAX_ORBIT_RADIUS, CELL_SIZE,
                    NUM_GENERAL_GARBAGE, GARBAGE_PER_PLANET_CLUSTER,
                    PLANET_GARBAGE_ZONE_RADIUS_FACTOR, MIN_DIST_GARBAGE_FROM_PLANET_SURFACE,
                    GARBAGE_SIZE_RANGE)
from garbage import Garbage

# Helper function to draw a filled circle, with basic off-screen culling.
def draw_pixel_circle(surface, color, center_x, center_y, radius):
    radius = int(radius)
    # Cull if entirely off-screen.
    if center_x + radius < 0 or center_x - radius > SCREEN_WIDTH or \
       center_y + radius < 0 or center_y - radius > SCREEN_HEIGHT:
        return
    pygame.draw.circle(surface, color, (int(center_x), int(center_y)), radius)

# Helper function to draw a 'pixel art' style star with a simple glow effect.
def draw_pixel_star(surface, screen_x, screen_y, base_color, size_category):
    core_size = 1
    if size_category == 'medium': core_size = 2
    elif size_category == 'large': core_size = random.choice([3, 4, 5])

    core_rect_x_int = int(screen_x - core_size // 2)
    core_rect_y_int = int(screen_y - core_size // 2)

    # Cull if core is off-screen.
    if core_rect_x_int + core_size < 0 or core_rect_x_int > SCREEN_WIDTH or \
       core_rect_y_int + core_size < 0 or core_rect_y_int > SCREEN_HEIGHT:
        return

    pygame.draw.rect(surface, base_color, (core_rect_x_int, core_rect_y_int, core_size, core_size))

    glow_alpha_value = random.randint(25, 75)
    r, g, b = base_color
    glow_color = (r, g, b, glow_alpha_value)

    if size_category == 'medium' or size_category == 'small': # Simpler cross-shaped glow.
        for dx_glow, dy_glow in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            gx_int, gy_int = int(screen_x + dx_glow), int(screen_y + dy_glow)
            if 0 <= gx_int < SCREEN_WIDTH and 0 <= gy_int < SCREEN_HEIGHT:
                glow_pixel_surface = pygame.Surface((1,1), pygame.SRCALPHA)
                glow_pixel_surface.fill(glow_color)
                surface.blit(glow_pixel_surface, (gx_int, gy_int))
    elif size_category == 'large': # More spread-out glow.
        glow_radius = core_size
        for dx_glow in range(-glow_radius, glow_radius + 1):
            for dy_glow in range(-glow_radius, glow_radius + 1):
                if abs(dx_glow) + abs(dy_glow) > 0 and abs(dx_glow) + abs(dy_glow) <= glow_radius:
                    if random.random() < 0.4: # Sparsely populate glow.
                        gx_int, gy_int = int(screen_x + dx_glow), int(screen_y + dy_glow)
                        if 0 <= gx_int < SCREEN_WIDTH and 0 <= gy_int < SCREEN_HEIGHT:
                            glow_pixel_surface = pygame.Surface((1,1), pygame.SRCALPHA)
                            glow_pixel_surface.fill(glow_color)
                            surface.blit(glow_pixel_surface, (gx_int, gy_int))

class Background:
    """
    Manages procedural generation and rendering of the game's environment,
    including celestial bodies, decorative elements, and initial garbage distribution.
    """
    def __init__(self):
        self.bg_color = (15, 0, 30) # Deep space color.

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
        self.all_garbage_items = [] # Master list of all garbage, populated by generation methods

        self.sun_data = {
            'type': 'sun', 'world_pos': (WORLD_CENTER_X, WORLD_CENTER_Y),
            'radius': SUN_RADIUS, 'color': SUN_COLOR
        }
        # Max radius a garbage item can have (half of its max size), for boundary checks.
        self.max_garbage_radius = GARBAGE_SIZE_RANGE[1] / 2.0


        self._generate_solar_system_orbiting_planets()
        self._generate_galactic_band_data()
        self._generate_outer_stars_data()
        self._generate_distant_planets_data()
        self._generate_general_garbage()
        self._populate_grid() # Populates grid with static elements for efficient rendering


    def _get_grid_coords(self, world_x, world_y):
        """Converts world coordinates to grid cell indices, clamping to grid bounds."""
        grid_x = int((world_x - self.world_min_x) / CELL_SIZE)
        grid_y = int((world_y - self.world_min_y) / CELL_SIZE)
        grid_x = max(0, min(grid_x, self.grid_cols - 1))
        grid_y = max(0, min(grid_y, self.grid_rows - 1))
        return grid_x, grid_y

    def _populate_grid(self):
        """Adds static background elements (stars, gas, dust, distant planets) to the spatial grid."""
        # Sun and orbiting planets are dynamic or drawn separately, not added to this static grid.
        all_static_elements = self._all_stars_data + self._all_galactic_gas_data + \
                              self._all_dust_lanes_data + self._all_distant_planets_data
        for item in all_static_elements:
            gx, gy = self._get_grid_coords(item['world_pos'][0], item['world_pos'][1])
            # The _get_grid_coords clamps, so indices should be valid.
            self.grid[gy][gx].append(item)

    def _is_position_colliding_with_celestial(self, x, y, item_radius):
        """Checks if a circular item at (x,y) with item_radius would overlap the sun or solar system planets."""
        sun_dist_sq = (x - WORLD_CENTER_X)**2 + (y - WORLD_CENTER_Y)**2
        if sun_dist_sq < (SUN_RADIUS + item_radius)**2:
            return True
        for p_data in self.solar_system_planets: # Assumes solar_system_planets are generated before this is heavily used by garbage
            planet_x, planet_y = p_data['world_pos']
            planet_radius = p_data['radius']
            dist_sq_to_planet = (x - planet_x)**2 + (y - planet_y)**2
            if dist_sq_to_planet < (planet_radius + item_radius)**2:
                return True
        return False

    def _generate_element_in_world_circle(self, radius_factor=1.0, min_radius_factor=0.0):
        """Generates a random (x, y) position within a specified annulus of the world, uniformly distributed by area."""
        angle = random.uniform(0, 2 * math.pi)
        # Square root of uniform random for radius squared ensures uniform area distribution.
        r_norm = math.sqrt(random.uniform(min_radius_factor**2, radius_factor**2))
        r = WORLD_RADIUS * r_norm
        x = WORLD_CENTER_X + r * math.cos(angle)
        y = WORLD_CENTER_Y + r * math.sin(angle)
        return int(x), int(y)

    def _generate_garbage_around_point(self, center_x, center_y, object_radius, count):
        """Generates a cluster of garbage items in an annulus around a central point (e.g., a planet)."""
        for _ in range(count):
            for attempt in range(20): # Try a few times to place each garbage item
                min_r_from_center = object_radius + MIN_DIST_GARBAGE_FROM_PLANET_SURFACE
                max_r_from_center = object_radius + object_radius * PLANET_GARBAGE_ZONE_RADIUS_FACTOR

                if max_r_from_center <= min_r_from_center: # Ensure a valid range for distance generation
                    max_r_from_center = min_r_from_center + 100

                angle = random.uniform(0, 2 * math.pi)
                distance = math.sqrt(random.uniform(min_r_from_center**2, max_r_from_center**2)) # Uniform area distribution

                gx = center_x + distance * math.cos(angle)
                gy = center_y + distance * math.sin(angle)

                # Boundary Check: Ensure new garbage is fully within WORLD_RADIUS
                dist_from_world_core = math.hypot(gx - WORLD_CENTER_X, gy - WORLD_CENTER_Y)
                if dist_from_world_core + self.max_garbage_radius >= WORLD_RADIUS:
                    continue # Position is too close to or outside world boundary; try new position

                # Celestial Collision Check (using max garbage radius for conservative placement)
                if not self._is_position_colliding_with_celestial(gx, gy, self.max_garbage_radius):
                    self.all_garbage_items.append(Garbage(gx, gy))
                    break # Successfully placed, move to next garbage item

    def _generate_solar_system_orbiting_planets(self):
        """Generates planets that orbit the central sun, ensuring unique orbital radii."""
        planet_colors_ss = [(150,100,50), (100,150,100), (100,100,200), (200,150,100), (180,180,180)]
        min_planet_radius, max_planet_radius = 800, 2000
        available_orbital_span = MAX_ORBIT_RADIUS - MIN_ORBIT_RADIUS

        num_planets_for_spacing = NUM_SOLAR_SYSTEM_PLANETS if NUM_SOLAR_SYSTEM_PLANETS > 0 else 1
        avg_spacing_needed = available_orbital_span / num_planets_for_spacing
        if avg_spacing_needed <= 0 and NUM_SOLAR_SYSTEM_PLANETS > 0 : # Handle case where MAX_ORBIT_RADIUS is too small
             avg_spacing_needed = (min_planet_radius + max_planet_radius) # Fallback reasonable spacing

        current_orbit_base = MIN_ORBIT_RADIUS
        generated_orbit_radii_info = []

        for i in range(NUM_SOLAR_SYSTEM_PLANETS):
            planet_radius = random.randint(min_planet_radius, max_planet_radius)
            chosen_orbit_radius = -1

            for _ in range(20): # Attempts to find a non-colliding orbit for the current planet
                # Define a potential orbital segment for this planet
                seg_start = current_orbit_base + i * avg_spacing_needed
                seg_end = current_orbit_base + (i + 1) * avg_spacing_needed - (planet_radius * 2.5) # Buffer for next planet

                seg_end = min(seg_end, MAX_ORBIT_RADIUS - planet_radius) # Orbit must be within max_orbit_radius
                seg_start = min(seg_start, seg_end - 100) # Ensure seg_start is meaningfully less than seg_end
                seg_start = max(seg_start, MIN_ORBIT_RADIUS + planet_radius) # Orbit must be beyond min_orbit_radius

                test_r = random.uniform(seg_start, seg_end) if seg_start < seg_end else current_orbit_base + planet_radius + random.uniform(100,300)

                test_r = max(MIN_ORBIT_RADIUS + planet_radius, test_r) # Clamp to lower bound considering planet size
                test_r = min(MAX_ORBIT_RADIUS - planet_radius, test_r) # Clamp to upper bound considering planet size

                is_too_close = False
                for prev_info in generated_orbit_radii_info:
                    min_dist_between_planets = prev_info['radius'] + planet_radius + 300 # Minimum separation buffer
                    if abs(test_r - prev_info['orbit_radius']) < min_dist_between_planets:
                        is_too_close = True; break
                if not is_too_close: chosen_orbit_radius = test_r; break

            if chosen_orbit_radius == -1: # Fallback if no suitable distinct orbit was found easily
                last_r_edge = generated_orbit_radii_info[-1]['orbit_radius'] + generated_orbit_radii_info[-1]['radius'] if generated_orbit_radii_info else MIN_ORBIT_RADIUS
                chosen_orbit_radius = last_r_edge + planet_radius + random.uniform(300, 600)
                chosen_orbit_radius = min(chosen_orbit_radius, MAX_ORBIT_RADIUS - planet_radius)
                chosen_orbit_radius = max(chosen_orbit_radius, MIN_ORBIT_RADIUS + planet_radius)

            generated_orbit_radii_info.append({'orbit_radius': chosen_orbit_radius, 'radius': planet_radius})
            angle = random.uniform(0, 2 * math.pi)

            # Planets further out orbit slower for a more natural feel
            speed_numerator = random.uniform(0.008, 0.02)
            speed_denominator = 1 + (chosen_orbit_radius / MAX_ORBIT_RADIUS) * 3
            orbit_speed = speed_numerator / speed_denominator if speed_denominator > 0 else speed_numerator

            px = WORLD_CENTER_X + chosen_orbit_radius * math.cos(angle)
            py = WORLD_CENTER_Y + chosen_orbit_radius * math.sin(angle)
            self.solar_system_planets.append({
                'type': 'solar_system_planet', 'world_pos': [px, py], 'radius': planet_radius,
                'color': random.choice(planet_colors_ss), 'orbit_radius': chosen_orbit_radius,
                'orbit_speed': orbit_speed, 'current_orbit_angle': angle
            })
            self._generate_garbage_around_point(px, py, planet_radius, GARBAGE_PER_PLANET_CLUSTER)
            current_orbit_base = chosen_orbit_radius + planet_radius # Update base for next planet's placement consideration

    def _generate_general_garbage(self):
        """Scatters general garbage items throughout the world, ensuring they are within bounds."""
        for _ in range(NUM_GENERAL_GARBAGE):
            for attempt in range(20):
                # Min radius factor for general garbage: avoid Sun's immediate proximity, account for garbage size
                min_r_factor_from_center = (SUN_RADIUS + 200 + self.max_garbage_radius) / WORLD_RADIUS if WORLD_RADIUS > 0 else 0.1
                # Max radius factor: ensure garbage center allows its edge to be within world boundary
                max_r_factor_from_center = (WORLD_RADIUS - self.max_garbage_radius) / WORLD_RADIUS if WORLD_RADIUS > 0 else 0.95

                if min_r_factor_from_center >= max_r_factor_from_center :
                    # Fallback if world is too small for these rules, place more freely but still try to be inside
                    gx, gy = self._generate_element_in_world_circle(0.95, 0.1)
                else:
                    gx, gy = self._generate_element_in_world_circle(max_r_factor_from_center, min_r_factor_from_center)

                # The generation with max_r_factor_from_center should place the center appropriately.
                # A direct check is still good for robustness.
                dist_from_world_core = math.hypot(gx - WORLD_CENTER_X, gy - WORLD_CENTER_Y)
                if dist_from_world_core + self.max_garbage_radius >= WORLD_RADIUS:
                    continue # This position would place garbage outside bounds; try again

                if not self._is_position_colliding_with_celestial(gx, gy, self.max_garbage_radius):
                    self.all_garbage_items.append(Garbage(gx, gy))
                    break # Successfully placed

    def _generate_galactic_band_data(self):
        """Generates a visually dense band of stars, gas, and dust across the world."""
        num_segments = 32; path_points = []
        path_start_x = WORLD_CENTER_X - WORLD_RADIUS*0.8; path_end_x = WORLD_CENTER_X + WORLD_RADIUS*0.8
        current_y = WORLD_CENTER_Y + random.randint(-WORLD_RADIUS//4, WORLD_RADIUS//4)
        path_points.append((path_start_x, current_y))
        for i in range(1,num_segments+1):
            px = path_start_x+(i/num_segments)*(path_end_x-path_start_x); py_offset_scale=WORLD_RADIUS/2.5
            py_offset=math.sin(i/num_segments*math.pi*random.uniform(1.5,2.5)+random.uniform(-0.5,0.5))*py_offset_scale
            py_drift=random.randint(-WORLD_RADIUS//15, WORLD_RADIUS//15); current_y=current_y+py_drift/num_segments
            py=max(WORLD_CENTER_Y-WORLD_RADIUS*0.4,min(WORLD_CENTER_Y+WORLD_RADIUS*0.4, current_y+py_offset))
            path_points.append((int(px),int(py)))
        path_points.append((path_end_x,WORLD_CENTER_Y+random.randint(-WORLD_RADIUS//4,WORLD_RADIUS//4)))

        band_colors=[(255,220,180),(255,200,150),(240,180,120),(255,150,100),(230,120,80)]
        num_gas_blobs=2000; band_thickness=WORLD_RADIUS/random.uniform(4.0,6.0)

        # Populate gas blobs along the generated path
        for i in range(len(path_points)-1):
            p1,p2=pygame.math.Vector2(path_points[i]),pygame.math.Vector2(path_points[i+1]); seg_len=p1.distance_to(p2)
            if seg_len==0:continue
            seg_blobs_density = (num_gas_blobs / (num_segments if num_segments > 0 else 1))
            world_segment_equiv = ((WORLD_RADIUS * 2) / (num_segments if num_segments > 0 else 1)) # Avg segment length across world width
            seg_blobs = int(seg_blobs_density * (seg_len / world_segment_equiv if world_segment_equiv > 0 else 1))
            for _ in range(seg_blobs):
                t=random.random(); cur_pos=p1.lerp(p2,t)
                dist=random.normalvariate(0,band_thickness/2.5); dist=max(-band_thickness*0.8,min(band_thickness*0.8,dist))
                perp=(p2-p1).rotate(90).normalize() if (p2-p1).length_squared()>0 else pygame.math.Vector2(0,1)
                blob_pos=cur_pos+perp*dist+pygame.math.Vector2(random.uniform(-10,10),random.uniform(-10,10))
                s=pygame.Surface((random.randint(5,15),random.randint(5,15)),pygame.SRCALPHA)
                c=random.choice(band_colors); s.fill((c[0],c[1],c[2],random.randint(10,40)))
                self._all_galactic_gas_data.append({'type':'gas_blob','surface':s,'world_pos':(int(blob_pos.x),int(blob_pos.y))})

        num_band_stars=2000; star_colors_band=[(255,255,240),(255,240,220),(255,200,200),(200,220,255)]
        # Populate stars in the band
        for i in range(len(path_points)-1):
            p1,p2=pygame.math.Vector2(path_points[i]),pygame.math.Vector2(path_points[i+1]); seg_len=p1.distance_to(p2)
            if seg_len==0:continue
            seg_stars_density = (num_band_stars / (num_segments if num_segments > 0 else 1))
            world_segment_equiv = ((WORLD_RADIUS * 2) / (num_segments if num_segments > 0 else 1))
            seg_stars = int(seg_stars_density * (seg_len / world_segment_equiv if world_segment_equiv > 0 else 1))
            for _ in range(seg_stars):
                t=random.random();cur_pos=p1.lerp(p2,t)
                dist=random.normalvariate(0,band_thickness/1.5); dist=max(-band_thickness*1.2,min(band_thickness*1.2,dist))
                perp=(p2-p1).rotate(90).normalize() if (p2-p1).length_squared()>0 else pygame.math.Vector2(0,1)
                star_pos=cur_pos+perp*dist+pygame.math.Vector2(random.uniform(-30,30),random.uniform(-30,30))
                if math.hypot(star_pos.x-WORLD_CENTER_X,star_pos.y-WORLD_CENTER_Y)<=WORLD_RADIUS: # Ensure within world
                    cat=random.choice(['small','medium','medium','large']); c=random.choice(star_colors_band)
                    mod=random.uniform(0.8,1.2); final_c=(min(255,int(c[0]*mod)),min(255,int(c[1]*mod)),min(255,int(c[2]*mod)))
                    self._all_stars_data.append({'type':'star','world_pos':(int(star_pos.x),int(star_pos.y)),'color':final_c,'size_cat':cat})

        num_dust_lanes=6000; dust_color=(20,15,10)
        # Populate dust lanes
        for i in range(len(path_points)-1):
            p1,p2=pygame.math.Vector2(path_points[i]),pygame.math.Vector2(path_points[i+1]); seg_len=p1.distance_to(p2)
            if seg_len==0:continue
            seg_dust_density = (num_dust_lanes / (num_segments if num_segments > 0 else 1))
            world_segment_equiv = ((WORLD_RADIUS * 2) / (num_segments if num_segments > 0 else 1))
            seg_dust = int(seg_dust_density * (seg_len / world_segment_equiv if world_segment_equiv > 0 else 1))
            for _ in range(seg_dust):
                t=random.random();cur_pos=p1.lerp(p2,t)
                dist=random.normalvariate(0,band_thickness/2.5); dist=max(-band_thickness*0.7,min(band_thickness*0.7,dist))
                perp=(p2-p1).rotate(random.choice([-80,-90,-100,80,90,100])).normalize() if (p2-p1).length_squared()>0 else pygame.math.Vector2(0,1)
                dust_pos=cur_pos+perp*dist+pygame.math.Vector2(random.uniform(-15,15),random.uniform(-15,15))
                if math.hypot(dust_pos.x-WORLD_CENTER_X,dust_pos.y-WORLD_CENTER_Y)<=WORLD_RADIUS: # Ensure within world
                    s=pygame.Surface((random.randint(8,25),random.randint(8,25)),pygame.SRCALPHA)
                    s.fill((dust_color[0],dust_color[1],dust_color[2],random.randint(50,120)))
                    self._all_dust_lanes_data.append({'type':'dust_blob','surface':s,'world_pos':(int(dust_pos.x),int(dust_pos.y))})

    def _generate_outer_stars_data(self):
        """Generates stars in the sparser, outer regions of the game world."""
        num_outer_stars = 20000
        star_colors_outer = [(200,200,220), (180,180,200), (220,220,255)]
        for _ in range(num_outer_stars):
            angle=random.uniform(0,2*math.pi)
            # Distribute more stars towards the outer edge (sqrt for area uniformity)
            r_norm = 0.4 + (1.0 - 0.4) * math.sqrt(random.random())
            r=WORLD_RADIUS*r_norm
            x=int(WORLD_CENTER_X+r*math.cos(angle)); y=int(WORLD_CENTER_Y+r*math.sin(angle))
            # r_norm should keep stars within bounds, but an explicit check is harmless for robustness
            if math.hypot(x-WORLD_CENTER_X,y-WORLD_CENTER_Y) <= WORLD_RADIUS:
                cat=random.choice(['small','small','medium']); c=random.choice(star_colors_outer)
                mod=random.uniform(0.5,0.9); final_c=(min(255,int(c[0]*mod)),min(255,int(c[1]*mod)),min(255,int(c[2]*mod)))
                self._all_stars_data.append({'type':'star','world_pos':(x,y),'color':final_c,'size_cat':cat})

    def _generate_distant_planets_data(self):
        """Generates small, decorative planets for the distant background."""
        num_distant_planets = 6000
        planet_colors = [(80,80,110),(110,80,80),(80,110,80),(110,110,80)]
        for _ in range(num_distant_planets):
            # Generate within 95% of world radius to keep them "distant"
            x,y=self._generate_element_in_world_circle(0.95)
            radius=random.randint(3,7)
            # Avoid cluttering the central y-band if a galactic band is prominent there
            if (WORLD_CENTER_Y-WORLD_RADIUS*0.2) < y < (WORLD_CENTER_Y+WORLD_RADIUS*0.2):
                if random.random() < 0.7: continue # 70% chance to skip if in this band
            self._all_distant_planets_data.append({'type':'distant_planet','world_pos':(x,y),'radius':radius,'color':random.choice(planet_colors)})

    def update(self, dt):
        """Updates positions of orbiting planets and handles garbage interactions."""
        # Update orbiting planets
        for p_data in self.solar_system_planets:
            p_data['current_orbit_angle'] += p_data['orbit_speed'] * dt
            p_data['world_pos'][0] = WORLD_CENTER_X + p_data['orbit_radius'] * math.cos(p_data['current_orbit_angle'])
            p_data['world_pos'][1] = WORLD_CENTER_Y + p_data['orbit_radius'] * math.sin(p_data['current_orbit_angle'])

        items_to_remove = [] # For garbage that gets pushed out of bounds
        for i, G_item in enumerate(self.all_garbage_items):
            # Simple collision response: push garbage out from overlapping sun/planets
            for celestial_body_data in [self.sun_data] + self.solar_system_planets:
                cb_x, cb_y = celestial_body_data['world_pos']
                cb_r = celestial_body_data['radius']

                dx = G_item.world_x - cb_x
                dy = G_item.world_y - cb_y
                dist_sq = dx*dx + dy*dy
                combined_radius = cb_r + G_item.size / 2.0

                if dist_sq < combined_radius**2 and dist_sq > 1e-6: # Check for overlap
                    dist = math.sqrt(dist_sq)
                    overlap = combined_radius - dist
                    push_factor = overlap / dist * 0.5 # Push by half the overlap distance
                    G_item.world_x += dx * push_factor
                    G_item.world_y += dy * push_factor
                    G_item.rect.center = (G_item.world_x, G_item.world_y)

            # Check if garbage was pushed out of world bounds after interactions
            dist_from_center = math.hypot(G_item.world_x - WORLD_CENTER_X, G_item.world_y - WORLD_CENTER_Y)
            # Remove if its center is significantly beyond the world radius
            if dist_from_center > WORLD_RADIUS + G_item.size:
                 items_to_remove.append(i)

        # Remove items marked for deletion (e.g., pushed out of bounds)
        for i in sorted(items_to_remove, reverse=True):
            self.all_garbage_items.pop(i)

    def draw(self, surface, camera_x, camera_y):
        """Draws all background elements, using the spatial grid for optimization of static parts."""
        surface.fill(self.bg_color)

        # Determine visible grid cells based on camera
        cam_min_gx = int((camera_x - self.world_min_x - CELL_SIZE) / CELL_SIZE)
        cam_max_gx = int(((camera_x + SCREEN_WIDTH) - self.world_min_x + CELL_SIZE) / CELL_SIZE)
        cam_min_gy = int((camera_y - self.world_min_y - CELL_SIZE) / CELL_SIZE)
        cam_max_gy = int(((camera_y + SCREEN_HEIGHT) - self.world_min_y + CELL_SIZE) / CELL_SIZE)

        start_col = max(0, cam_min_gx); end_col = min(self.grid_cols - 1, cam_max_gx)
        start_row = max(0, cam_min_gy); end_row = min(self.grid_rows - 1, cam_max_gy)

        # Layered drawing of static elements from the visible grid cells
        for layer_type in ['gas_blob', 'dust_blob', 'distant_planet', 'star']:
            for gy_idx in range(start_row, end_row + 1):
                for gx_idx in range(start_col, end_col + 1):
                    # Grid indices are already clamped, direct access is safe
                    for item in self.grid[gy_idx][gx_idx]:
                        if item.get('type') == layer_type:
                            screen_x = item['world_pos'][0] - camera_x
                            screen_y = item['world_pos'][1] - camera_y
                            if layer_type == 'gas_blob' or layer_type == 'dust_blob':
                                blob_surf = item['surface']
                                blob_s = blob_surf.get_size()
                                # Basic culling for blob surfaces
                                if screen_x + blob_s[0] > 0 and screen_x < SCREEN_WIDTH and \
                                   screen_y + blob_s[1] > 0 and screen_y < SCREEN_HEIGHT:
                                    surface.blit(blob_surf, (screen_x, screen_y))
                            elif layer_type == 'distant_planet':
                                draw_pixel_circle(surface, item['color'], screen_x, screen_y, item['radius'])
                            elif layer_type == 'star':
                                draw_pixel_star(surface, screen_x, screen_y, item['color'], item['size_cat'])

        # Draw Solar System Planets (dynamic, positions updated each frame)
        for planet_data in self.solar_system_planets:
            draw_pixel_circle(surface, planet_data['color'],
                              planet_data['world_pos'][0] - camera_x,
                              planet_data['world_pos'][1] - camera_y,
                              planet_data['radius'])

        # Draw Sun
        sun_screen_x = self.sun_data['world_pos'][0] - camera_x
        sun_screen_y = self.sun_data['world_pos'][1] - camera_y
        sun_radius_val = self.sun_data['radius']
        # Culling for the Sun before drawing
        if not (sun_screen_x + sun_radius_val < 0 or sun_screen_x - sun_radius_val > SCREEN_WIDTH or \
                sun_screen_y + sun_radius_val < 0 or sun_screen_y - sun_radius_val > SCREEN_HEIGHT):
            pygame.draw.circle(surface, self.sun_data['color'], (int(sun_screen_x), int(sun_screen_y)), sun_radius_val)
