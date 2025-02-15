# ---------------------------
# FUNCTION: DRAW LATITUDE AND LONGITUDE LINES
# ---------------------------
def draw_lat_lon_lines(screen):
    # # Latitude lines (constant Dec)
    # latitudes = [-math.pi/2, -math.pi/3, -math.pi/6, 0, math.pi/6, math.pi/3, math.pi/2]  # Example Dec values
    # for dec in latitudes:
    #     for ra_deg in range(0, 360, 15):  # RA from 0 to 360 degrees, step 15 degrees
    #         ra = math.radians(ra_deg)
    #         proj = project_star(ra, dec, view_ra, view_dec)
    #         if proj:
    #             x_proj, y_proj = proj
    #             screen_x = WIDTH / 2 + x_proj * pixel_scale
    #             screen_y = HEIGHT / 2 - y_proj * pixel_scale
    #             pygame.draw.circle(screen, (255, 0, 0), (int(screen_x), int(screen_y)), 1)

    # # Longitude lines (constant RA)
    # for ra_deg in range(0, 360, 15):  # RA from 0 to 360 degrees, step 15 degrees
    #     ra = math.radians(ra_deg)
    #     for dec_deg in range(-90, 91, 15):  # Dec from -90° to 90°, step 15°
    #         dec = math.radians(dec_deg)
    #         proj = project_star(ra, dec, view_ra, view_dec)
    #         if proj:
    #             x_proj, y_proj = proj
    #             screen_x = WIDTH / 2 + x_proj * pixel_scale
    #             screen_y = HEIGHT / 2 - y_proj * pixel_scale
    #             pygame.draw.circle(screen, (255, 0, 0), (int(screen_x), int(screen_y)), 1)
    grid_color = (255, 0, 0)  # Red color for the grid

    # Draw latitude lines (Declination)
    for dec_deg in range(-60, 90, 30):  # -60° to 60° (every 30°)
        dec_rad = math.radians(dec_deg)
        points = []
        for ra_deg in range(0, 361, 10):  # Full circle, 0° to 360°
            ra_rad = math.radians(ra_deg)
            proj = project_star(ra_rad, dec_rad, view_ra, view_dec)
            if proj:
                x_proj, y_proj = proj
                screen_x = WIDTH / 2 + x_proj * pixel_scale
                screen_y = HEIGHT / 2 - y_proj * pixel_scale
                points.append((screen_x, screen_y))
        
        if len(points) > 1:
            pygame.draw.lines(screen, grid_color, False, points, 1)

    # Draw longitude lines (Right Ascension)
    for ra_deg in range(0, 360, 30):  # Every 30°
        ra_rad = math.radians(ra_deg)
        points = []
        for dec_deg in range(-90, 91, 10):  # From -90° to 90°
            dec_rad = math.radians(dec_deg)
            proj = project_star(ra_rad, dec_rad, view_ra, view_dec)
            if proj:
                x_proj, y_proj = proj
                screen_x = WIDTH / 2 + x_proj * pixel_scale
                screen_y = HEIGHT / 2 - y_proj * pixel_scale
                points.append((screen_x, screen_y))
        
        if len(points) > 1:
            pygame.draw.lines(screen, grid_color, False, points, 1)