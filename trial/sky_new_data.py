import pygame
import math
import csv
import os

# ---------------------------
# CONFIGURATION
# ---------------------------
WIDTH, HEIGHT = 800, 600  # Screen size
STAR_FILE = "constellations.csv"  # Star catalog file

# Check if file exists
if not os.path.exists(STAR_FILE):
    print(f"Error: {STAR_FILE} not found!")
    exit(1)

# ---------------------------
# FUNCTION TO CONVERT RA (hh:mm:ss) TO DEGREES
# ---------------------------
def ra_to_degrees(ra_str):
    """ Converts RA from hh:mm:ss format to degrees. """
    ra_parts = ra_str.split("h")
    hours = float(ra_parts[0].strip())
    minutes_seconds = ra_parts[1].split("m")
    minutes = float(minutes_seconds[0].strip())
    seconds = float(minutes_seconds[1].replace("s", "").strip())
    
    # Convert to degrees (1 hour = 15 degrees)
    ra_degrees = (hours + minutes / 60 + seconds / 3600) * 15
    return ra_degrees

# ---------------------------
# FUNCTION TO CONVERT DEC (dd° mm′ ss″) TO DEGREES
# ---------------------------
def dec_to_degrees(dec_str):
    """ Converts Dec from dd° mm′ ss″ format to degrees. """
    dec_parts = dec_str.split("°")
    degrees = float(dec_parts[0].strip())
    minutes_seconds = dec_parts[1].split("′")
    minutes = float(minutes_seconds[0].strip())
    seconds = float(minutes_seconds[1].replace("″", "").strip())
    
    # Convert to degrees
    dec_degrees = degrees + (minutes / 60) + (seconds / 3600)
    
    # If it's a negative declination (South), convert to negative degrees
    if dec_str[0] == "-":
        dec_degrees = -dec_degrees
    return dec_degrees

# ---------------------------
# LOAD STAR DATA
# ---------------------------
stars = []
with open(STAR_FILE, mode='r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        try:
            name = row['Name']
            ra_str = row['Right Ascension']
            dec_str = row['Declination']
            mag = float(row['Apparent Magnitude'])  # Apparent Magnitude
            constellation = row['Constellation']

            print(name,',',ra_str,',',dec_str,',',mag,',',constellation)
            
            # Convert RA and Dec to degrees
            ra_deg = ra_to_degrees(ra_str)
            dec_deg = dec_to_degrees(dec_str)
            
            # Convert degrees to radians
            ra_rad = math.radians(ra_deg)
            dec_rad = math.radians(dec_deg)
            
            stars.append((ra_rad, dec_rad, mag))
        except ValueError:
            continue

print(f"Loaded {len(stars)} stars from {STAR_FILE}")

# ---------------------------
# PYGAME INITIALIZATION
# ---------------------------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Star Map")
clock = pygame.time.Clock()

# View parameters (in radians)
view_ra = 0.0   # Right Ascension (center)
# view_dec = math.radians(90)  # Declination (center)
view_dec = 0.0  # Declination (center)
pixel_scale = 250  # Zoom: pixels per radian

# ---------------------------
# FUNCTION: GNOMONIC PROJECTION
# ---------------------------
def project_star(ra, dec, ra0, dec0):
    """ Projects (ra, dec) onto a 2D plane using Gnomonic projection. """
    cos_c = math.sin(dec0) * math.sin(dec) + math.cos(dec0) * math.cos(dec) * math.cos(ra - ra0)
    # if cos_c <= 0:
    #     return None  # Star is behind
    x = (math.cos(dec) * math.sin(ra - ra0)) / cos_c
    y = (math.cos(dec0) * math.sin(dec) - math.sin(dec0) * math.cos(dec) * math.cos(ra - ra0)) / cos_c
    return x, y

# ---------------------------
# FUNCTION: MAGNITUDE TO STAR SIZE/COLOR
# ---------------------------
def get_star_params(mag):
    """ Determines star size and brightness based on magnitude. """
    radius = max(1, int(6 - mag))
    brightness = max(100, min(255, 255 - int(mag * 20)))
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

                # Special Case: Handle Dec exceeding ±90° to prevent locking at the poles
                if view_dec > math.pi / 2:
                    view_dec = math.pi - view_dec  # Reverse direction
                    view_ra += math.pi  # Flip RA by 180°
                elif view_dec < -math.pi / 2:
                    view_dec = -math.pi - view_dec  # Reverse direction
                    view_ra += math.pi  # Flip RA by 180°

                view_ra %= (2 * math.pi)  # Keep RA in [0, 2π]

    # ---------------------------
    # DRAW FRAME
    # ---------------------------
    screen.fill((0, 0, 0))  # Black background

    # # Draw red latitude and longitude lines
    # draw_lat_lon_lines(screen)

    # Compute max projection distance
    max_proj = min(WIDTH, HEIGHT) / (2 * pixel_scale)

    for star in stars:
        ra, dec, mag = star
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

    # Draw crosshair at center
    pygame.draw.line(screen, (50, 50, 50), (WIDTH/2 - 10, HEIGHT/2), (WIDTH/2 + 10, HEIGHT/2))
    pygame.draw.line(screen, (50, 50, 50), (WIDTH/2, HEIGHT/2 - 10), (WIDTH/2, HEIGHT/2 + 10))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
