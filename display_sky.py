import pygame
import math
import load_data

# ---------------------------
# CONFIGURATION
# ---------------------------
WIDTH, HEIGHT = 800, 600  # Screen size
stars = load_data.loadData()

# ---------------------------
# FUNCTION: GNOMONIC PROJECTION
# ---------------------------
def _project_star(ra, dec, ra0, dec0):
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
def _get_star_params(mag):
    """ Determines star size and brightness based on magnitude. """
    radius = max(1, int(6 - mag))
    brightness = max(100, min(255, 255 - int(mag * 20)))
    return radius, (brightness, brightness, brightness)

# ---------------------------
# DRAW RED LATITUDE AND LONGITUDE GRID LINES
# ---------------------------
def _draw_lat_lon_lines(screen, pixel_scale, max_proj, ra0, dec0):
    """
    Draws red grid lines (latitude and longitude) within the visible circle.
    Grid spacing is determined by the pixel_scale:
        - When zoomed out (low pixel_scale), use larger angular steps.
        - When zoomed in (high pixel_scale), use smaller angular steps.
    Also displays the coordinate labels (RA/Dec) on the grid lines.
    """
    grid_color = (255, 0, 0)  # Red color for grid lines

    # Create a font for displaying labels
    font = pygame.font.SysFont(None, 16)

    # Determine grid spacing (in degrees) based on pixel_scale.
    if pixel_scale < 150:
        ra_main_step = 30    # degrees between longitude lines
        dec_main_step = 30   # degrees between latitude lines
        sample_step = 5      # degrees sampling resolution along each line
    elif pixel_scale < 300:
        ra_main_step = 20
        dec_main_step = 20
        sample_step = 2
    elif pixel_scale < 600:
        ra_main_step = 10
        dec_main_step = 10
        sample_step = 1
    else:
        ra_main_step = 5
        dec_main_step = 5
        sample_step = 1

    # Draw latitude lines (constant declination)
def _draw_lat_lon_lines(screen, pixel_scale, max_proj, ra0, dec0):
    grid_color = (255, 0, 0)
    font = pygame.font.SysFont(None, 16)

    # Determine grid spacing and sample step
    if pixel_scale < 150:
        ra_main_step, dec_main_step, sample_step = 30, 30, 5
    elif pixel_scale < 300:
        ra_main_step, dec_main_step, sample_step = 20, 20, 2
    elif pixel_scale < 600:
        ra_main_step, dec_main_step, sample_step = 10, 10, 1
    else:
        ra_main_step, dec_main_step, sample_step = 5, 5, 1

    # Draw latitude lines (constant declination)
    for dec_deg in range(-90, 91, dec_main_step):
        dec_rad = math.radians(dec_deg)
        points_collection = []
        current_segment = []

        # Calculate the valid RA range for this declination
        # Compute the critical value to determine RA visibility
        tan_dec0 = math.tan(dec0) if abs(dec0) < math.pi/2 - 1e-6 else float('inf')
        critical = -tan_dec0 * math.tan(dec_rad)
        if critical >= 1:
            continue  # No visible points for this declination
        elif critical <= -1:
            ra_start_deg, ra_end_deg = 0, 360  # All RA are visible
        else:
            delta_max = math.acos(critical)
            ra0_deg = math.degrees(ra0)
            ra_start_deg = (ra0_deg - math.degrees(delta_max)) % 360
            ra_end_deg = (ra0_deg + math.degrees(delta_max)) % 360

        # Generate RA samples within the valid range
        # We need to handle the wrap-around at 360 degrees
        if ra_start_deg < ra_end_deg:
            ra_samples = list(range(0, 360, sample_step))  # Full circle
        else:
            # Split into two ranges: ra_start_deg to 360 and 0 to ra_end_deg
            ra_samples = list(range(0, int(ra_end_deg)+1, sample_step)) + \
                          list(range(int(ra_start_deg), 360, sample_step))

        for ra_deg in ra_samples:
            ra_rad = math.radians(ra_deg)
            proj = _project_star(ra_rad, dec_rad, ra0, dec0)
            if proj is None:
                if current_segment:
                    points_collection.append(current_segment)
                    current_segment = []
                continue
            x_proj, y_proj = proj
            if math.sqrt(x_proj**2 + y_proj**2) > max_proj:
                if current_segment:
                    points_collection.append(current_segment)
                    current_segment = []
                continue
            screen_x = WIDTH / 2 + x_proj * pixel_scale
            screen_y = HEIGHT / 2 - y_proj * pixel_scale
            current_segment.append((screen_x, screen_y))
        else:
            # After loop, add the remaining segment
            if current_segment:
                points_collection.append(current_segment)

        # Draw each segment of the latitude line
        for points in points_collection:
            if len(points) > 1:
                pygame.draw.lines(screen, grid_color, False, points, 1)
                # Label placement at the midpoint
                mid_point = points[len(points) // 2]
                label_text = font.render(f"Dec: {dec_deg}°", True, grid_color)
                screen.blit(label_text, mid_point)

    # Draw longitude lines (constant right ascension)
    for ra_deg in range(0, 360, ra_main_step):
        ra_rad = math.radians(ra_deg)
        points = []
        for dec_deg in range(-90, 91, sample_step):
            dec_rad = math.radians(dec_deg)
            proj = _project_star(ra_rad, dec_rad, ra0, dec0)
            if proj is None:
                continue
            x_proj, y_proj = proj
            if math.sqrt(x_proj**2 + y_proj**2) > max_proj:
                continue
            screen_x = WIDTH / 2 + x_proj * pixel_scale
            screen_y = HEIGHT / 2 - y_proj * pixel_scale
            points.append((screen_x, screen_y))
        if len(points) > 1:
            pygame.draw.lines(screen, grid_color, False, points, 1)
            # Display the RA label at the midpoint of the line
            label_pos = points[len(points) // 2]
            label_text = font.render(f"RA: {ra_deg}°", True, grid_color)
            screen.blit(label_text, label_pos)

def displaySky():
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

        # Draw red latitude and longitude lines
        _draw_lat_lon_lines(screen, pixel_scale, max_proj, view_ra, view_dec)

        for star in stars:
            ra, dec, mag = star
            proj = _project_star(ra, dec, view_ra, view_dec)
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
                radius, color = _get_star_params(mag)
                pygame.draw.circle(screen, color, (int(screen_x), int(screen_y)), radius)

        # Draw crosshair at center
        pygame.draw.line(screen, (50, 50, 50), (WIDTH/2 - 10, HEIGHT/2), (WIDTH/2 + 10, HEIGHT/2))
        pygame.draw.line(screen, (50, 50, 50), (WIDTH/2, HEIGHT/2 - 10), (WIDTH/2, HEIGHT/2 + 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
