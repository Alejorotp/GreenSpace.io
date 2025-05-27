import pygame
import random
import math
import time
import colorsys

# Window dimensions
WIDTH, HEIGHT = 800, 600

# Colors
RED = (255, 65, 98)
BLUE = (0, 120, 255)
ORANGE = (255, 154, 0)
GREEN = (1, 255, 31)
YELLOW = (227, 255, 0)
PURPLE = (189, 0, 255)
MAGNET_BORDER = (50, 50, 50)
BACKGROUND = (240, 240, 245)

# Magnet properties
MAGNET_RADIUS = 60
MAGNET_BORDER_WIDTH = 8
MAGNET_STRENGTH = 100000

# Particle properties
PARTICLE_SIZE = 18
PARTICLE_CHARGE_RANGE = (0.5, 4)  # Only positive charges for simplicity
PARTICLE_COLORS = [RED, BLUE, ORANGE, GREEN, YELLOW, PURPLE]

# Brownian motion parameters
DIFFUSION_COEFFICIENT = 0.2   # Controls randomness strength
TEMPERATURE = 1.0             # Thermal energy
TIME_STEP = 1/60              # Match physics to 60 FPS

class Particle:
    def __init__(self):
        self.charge = random.uniform(*PARTICLE_CHARGE_RANGE)
        self.color = random.choice(PARTICLE_COLORS)
        self.x = random.randint(PARTICLE_SIZE, WIDTH - PARTICLE_SIZE)
        self.y = random.randint(PARTICLE_SIZE, HEIGHT - PARTICLE_SIZE)
        self.vx = 0
        self.vy = 0
        self.trail = []

    def update(self, magnet_x, magnet_y, magnet_polarity):
        # --- BROWNIAN MOTION (Random forces) ---
        random_force_x = math.sqrt(2 * DIFFUSION_COEFFICIENT * TEMPERATURE / TIME_STEP) * random.gauss(0, 1)
        random_force_y = math.sqrt(2 * DIFFUSION_COEFFICIENT * TEMPERATURE / TIME_STEP) * random.gauss(0, 1)

        # Apply random force (Brownian jitter)
        self.vx += random_force_x * TIME_STEP
        self.vy += random_force_y * TIME_STEP

        # MAGNETIC FORCE
        dx = magnet_x - self.x
        dy = magnet_y - self.y
        distance = math.sqrt(dx**2 + dy**2) + 20
        force = self.charge * MAGNET_STRENGTH * magnet_polarity / (distance ** 2)
        angle = math.atan2(dy, dx)
        self.vx += force * math.cos(angle) / 60
        self.vy += force * math.sin(angle) / 60

        # DAMPING
        self.vx *= 0.95
        self.vy *= 0.95

        # Update position
        self.x += self.vx
        self.y += self.vy

        # Wall bouncing
        if self.x <= PARTICLE_SIZE or self.x >= WIDTH - PARTICLE_SIZE:
            self.vx *= -1
            self.x = max(PARTICLE_SIZE, min(WIDTH - PARTICLE_SIZE, self.x))
        if self.y <= PARTICLE_SIZE or self.y >= HEIGHT - PARTICLE_SIZE:
            self.vy *= -1
            self.y = max(PARTICLE_SIZE, min(HEIGHT - PARTICLE_SIZE, self.y))

        # Store trail
        self.trail.append((self.x, self.y))
        if len(self.trail) > 20:
            self.trail.pop(0)

    def draw(self, screen):
        # Draw trail
        for i, (x, y) in enumerate(self.trail):
            h, s, v = colorsys.rgb_to_hsv(*[c/255 for c in self.color])
            trail_color = colorsys.hsv_to_rgb(h, s, max(0.3, v * 0.7))
            trail_color = tuple(int(c * 255) for c in trail_color)
            trail_radius = max(1, PARTICLE_SIZE - 2)
            pygame.draw.circle(screen, trail_color, (int(x), int(y)), trail_radius)

        # Draw particle
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), PARTICLE_SIZE)

def draw_magnet(screen, x, y, polarity):
    pygame.draw.circle(screen, MAGNET_BORDER, (x, y), MAGNET_RADIUS)
    pygame.draw.circle(
        screen,
        RED if polarity > 0 else BLUE,
        (x, y),
        MAGNET_RADIUS - MAGNET_BORDER_WIDTH
    )

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Brownian Motion + Magnet")
    clock = pygame.time.Clock()

    particles = []
    magnet_x, magnet_y = WIDTH // 2, HEIGHT // 2
    magnet_polarity = 1

    start_time = time.time()
    runtime = 40  # 40-second simulation

    running = True
    while running:
        current_time = time.time() - start_time
        if current_time >= runtime:
            running = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    magnet_polarity *= -1  # Toggle polarity

        screen.fill(BACKGROUND)
        draw_magnet(screen, magnet_x, magnet_y, magnet_polarity)

        # Spawn new particles
        if random.random() < 0.1 and len(particles) < 200:
            particles.append(Particle())

        # Update and draw particles
        for particle in particles[:]:
            particle.update(magnet_x, magnet_y, magnet_polarity)
            particle.draw(screen)

        if len(particles) > 200:
            particles.pop(0)

        # Display time left
        font = pygame.font.SysFont('Arial', 20)
        time_text = font.render(f"Time: {int(runtime - current_time)}s", True, (0, 0, 0))
        screen.blit(time_text, (10, 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
