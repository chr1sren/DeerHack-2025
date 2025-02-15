import pygame
import math
import csv
import gzip
import os

# ---------------------------
# CONFIGURATION
# ---------------------------
WIDTH, HEIGHT = 800, 600  # Screen size
STAR_FILE = "hyg_v38.csv.gz"  # Star catalog file
CONSTELLATION_FILE = "constellations.txt"  # Constellation line data

# ---------------------------
# LOAD STAR DATA
# ---------------------------
stars = {}
with gzip.open(STAR_FILE, mode='rt', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        try:
            hip = int(row['hip']) if row['hip'] else None  # HIP ID
            ra = float(row['ra'])  # Right Ascension
            dec = float(row['dec'])  # Declination
            mag = float(row['mag'])  # Magnitude
        except ValueError:
            continue
        if hip:
            stars[hip] = (math.radians(ra * 15), math.radians(dec), mag)  # Convert to radians

print(f"Loaded {len(stars)} stars from {STAR_FILE}")

# ---------------------------
# LOAD CONSTELLATION LINES
# ---------------------------
constellation_lines = []
if os.path.exists(CONSTELLATION_FILE):
    with open(CONSTELLATION_FILE, 'r') as file:
        for line in file:
            parts = line.strip().split()
            if len(parts) == 2:
                try:
                    star1 = int(parts[0])
                    star2 = int(parts[1])
                    if star1 in stars and star2 in stars:
                        constellation_lines.append((stars[star1], stars[star2]))
                except ValueError:
                    continue

print(f"Loaded {len(constellation_lines)} constellation lines from {CONSTELLATION_FILE}")

# ---------------------------
# PYGAME INITIALIZATION
# ---------------------------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Star Map with Constellations")
clock = pygame.time.Clock()

# View parameters (in radians)
view_ra = 0.0   # Right Ascension (center)
view_dec = 0.0  # Declination (center)
pixel_scale = 250  # Zoom: pixels per radian

# ---------------------------
# FUNCTION: GNOMONIC PROJECTION
# ---------------------------
def project_star(ra, dec, ra0, dec0):
    """ Projects (ra, dec) onto a 2D plane using Gnomonic projection. """
    cos_c = math.sin(dec0) * math.sin(dec) + math.cos(dec0) * math.cos(dec) * math.cos(ra - ra0)
    if cos_c <= 0:
        return None  # Star is behind
    x = (math.cos(dec) * math.sin(ra - ra0)) / cos_c
    y = (math.cos(dec0) * math.sin(dec) - math.sin(dec0) * math.cos(dec) * math.cos(ra - ra0)) / cos_c
    return x, y

# ---------------------------
# FUNCTION: MAGNITUDE TO STAR SIZE/COLOR
# ---------------------------
def get_star_params(mag):
    """ Determines star size and brightness based on magnitude. """
    radius = max(1, int(6 - mag))  # Brighter stars are larger
    brightness = max(100, min(255, 255 - int(mag * 20)))  # Adjust brightness
    return radius, (brightness, brightness, brightness)

# ---------------------------
# MOUSE CONTROLS
# ---------------------------
dragging = False
last_mouse_pos = None

# ---------------------------
# MAIN LOOP
# ---------------------------
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left-click: Start panning
                dragging = True
                last_mouse_pos = event.pos
            elif event.button == 4:  # Scroll up: Zoom in
                pixel_scale *= 1.1
            elif event.button == 5:  # Scroll down: Zoom out
                pixel_scale /= 1.1

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                dragging = False

        elif event.type == pygame.MOUSEMOTION:
            if dragging:
                dx = event.pos[0] - last_mouse_pos[0]
                dy = event.pos[1] - last_mouse_pos[1]
                last_mouse_pos = event.pos
                # Convert pixel movement to angular change
                d_ra = -dx / (pixel_scale * math.cos(view_dec))
                d_dec = dy / pixel_scale
                view_ra += d_ra
                view_dec += d_dec
                # Keep declination in range
                view_dec = max(-math.pi/2 + 0.01, min(math.pi/2 - 0.01, view_dec))
                view_ra %= (2 * math.pi)  # Keep RA in [0, 2π]

    # ---------------------------
    # DRAW FRAME
    # ---------------------------
    screen.fill((0, 0, 0))  # Black background

    # Compute max projection distance
    max_proj = min(WIDTH, HEIGHT) / (2 * pixel_scale)

    # Draw constellation lines first (so stars appear on top)
    for (star1, star2) in constellation_lines:
        proj1 = project_star(star1[0], star1[1], view_ra, view_dec)
        proj2 = project_star(star2[0], star2[1], view_ra, view_dec)
        if proj1 and proj2:
            x1, y1 = proj1
            x2, y2 = proj2
            if (math.sqrt(x1**2 + y1**2) <= max_proj and 
                math.sqrt(x2**2 + y2**2) <= max_proj):
                pygame.draw.line(screen, (50, 50, 255), 
                                 (WIDTH / 2 + x1 * pixel_scale, HEIGHT / 2 - y1 * pixel_scale),
                                 (WIDTH / 2 + x2 * pixel_scale, HEIGHT / 2 - y2 * pixel_scale), 1)

    # Draw stars
    for hip, (ra, dec, mag) in stars.items():
        proj = project_star(ra, dec, view_ra, view_dec)
        if proj is None:
            continue
        x_proj, y_proj = proj

        # Clip to visible area
        if math.sqrt(x_proj**2 + y_proj**2) > max_proj:
            continue

        # Convert to screen coordinates
        screen_x = WIDTH / 2 + x_proj * pixel_scale
        screen_y = HEIGHT / 2 - y_proj * pixel_scale
        if 0 <= screen_x <= WIDTH and 0 <= screen_y <= HEIGHT:
            radius, color = get_star_params(mag)
            pygame.draw.circle(screen, color, (int(screen_x), int(screen_y)), radius)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
