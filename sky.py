import pygame
import math
import csv
import gzip
import os
import random

# ---------------------------
# Configuration and Setup
# ---------------------------
WIDTH, HEIGHT = 800, 600

# Star catalog file (gzipped CSV)
CATALOG_FILENAME = "hyg_v38.csv.gz"

if not os.path.exists(CATALOG_FILENAME):
    print(f"Catalog file '{CATALOG_FILENAME}' not found!")
    exit(1)

# ---------------------------
# Load Star Data from gzipped CSV
# ---------------------------
stars = []
with gzip.open(CATALOG_FILENAME, mode='rt', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        try:
            ra_deg = float(row['ra'])
            dec_deg = float(row['dec'])
            mag = float(row['mag'])
        except Exception:
            continue
        # Convert degrees to radians.
        ra_rad = math.radians(ra_deg)
        dec_rad = math.radians(dec_deg)
        stars.append((ra_rad, dec_rad, mag))
print(f"Loaded {len(stars)} stars from the gzipped catalog.")

# ---------------------------
# Initialize Pygame
# ---------------------------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Navigatable Skymap")
clock = pygame.time.Clock()

# View parameters (in radians) for the center of the screen.
view_ra = 0.0   # Right Ascension
view_dec = 0.0  # Declination

# Pixel scale: controls the zoom level (pixels per radian)
pixel_scale = 250

# ---------------------------
# Gnomonic Projection Function
# ---------------------------
def gnomonic_projection(ra, dec, ra0, dec0):
    """
    Projects a star at (ra, dec) onto a tangent plane centered at (ra0, dec0)
    using the gnomonic projection. Returns (x, y) in radians.
    """
    cos_c = math.sin(dec0) * math.sin(dec) + math.cos(dec0) * math.cos(dec) * math.cos(ra - ra0)
    if cos_c <= 0:
        return None  # Star is behind the projection plane
    x = (math.cos(dec) * math.sin(ra - ra0)) / cos_c
    y = (math.cos(dec0) * math.sin(dec) - math.sin(dec0) * math.cos(dec) * math.cos(ra - ra0)) / cos_c
    return (x, y)

# ---------------------------
# Star Drawing Helper
# ---------------------------
def get_star_draw_params(mag):
    """
    Map a star's magnitude to a drawn radius and grayscale color.
    Brighter stars (lower mag) are drawn larger and with higher intensity.
    """
    radius = max(1, int(5 - mag))
    intensity = max(100, min(255, 255 - int(mag * 20)))
    return radius, (intensity, intensity, intensity)

# ---------------------------
# Variables for Mouse Panning
# ---------------------------
dragging = False
last_mouse_pos = None

# ---------------------------
# Main Loop
# ---------------------------
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button begins dragging
                dragging = True
                last_mouse_pos = event.pos
            elif event.button == 4:  # Mouse wheel up: zoom in
                pixel_scale *= 1.1
            elif event.button == 5:  # Mouse wheel down: zoom out
                pixel_scale /= 1.1

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                dragging = False

        elif event.type == pygame.MOUSEMOTION:
            if dragging:
                dx = event.pos[0] - last_mouse_pos[0]
                dy = event.pos[1] - last_mouse_pos[1]
                last_mouse_pos = event.pos
                # Convert pixel movement to angular change (in radians)
                d_ra = -dx / (pixel_scale * math.cos(view_dec))
                d_dec = dy / pixel_scale
                view_ra += d_ra
                view_dec += d_dec
                view_dec = max(-math.pi/2 + 0.01, min(math.pi/2 - 0.01, view_dec))
                view_ra %= (2 * math.pi)

    # ---------------------------
    # Draw Frame
    # ---------------------------
    screen.fill((0, 0, 0))  # Black background

    # Calculate maximum projection distance (in radians) that will fill the screen.
    # Here we use the smallest half-dimension to ensure stars are clipped correctly.
    max_proj = min(WIDTH, HEIGHT) / (2 * pixel_scale)

    for star in stars:
        ra, dec, mag = star
        proj = gnomonic_projection(ra, dec, view_ra, view_dec)
        if proj is None:
            continue
        x_proj, y_proj = proj

        # Clip stars that fall outside the current visible field-of-view.
        if math.sqrt(x_proj**2 + y_proj**2) > max_proj:
            continue

        # Convert projection coordinates (radians) to screen pixels.
        screen_x = WIDTH / 2 + x_proj * pixel_scale
        screen_y = HEIGHT / 2 - y_proj * pixel_scale
        if 0 <= screen_x <= WIDTH and 0 <= screen_y <= HEIGHT:
            radius, color = get_star_draw_params(mag)
            pygame.draw.circle(screen, color, (int(screen_x), int(screen_y)), radius)

    # Optionally, draw a crosshair at the center.
    pygame.draw.line(screen, (50, 50, 50), (WIDTH/2 - 10, HEIGHT/2), (WIDTH/2 + 10, HEIGHT/2))
    pygame.draw.line(screen, (50, 50, 50), (WIDTH/2, HEIGHT/2 - 10), (WIDTH/2, HEIGHT/2 + 10))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
