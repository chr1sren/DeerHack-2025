import pygame
import numpy as np
from config import *

class Renderer:
    def __init__(self, star_projection):
        self.star_proj = star_projection
        self.asterism_cache = {}
        self.constellation_cache = {}
        self.selected_lines_cache = {}  # Cache for selected lines

    def draw_boundaries(self, surface):
        scale_inv = 1.0 / self.star_proj.scale
        cache_key = (int(self.star_proj.view_ra), int(self.star_proj.scale * 100))
        
        if cache_key not in self.asterism_cache:
            asterism_points = []
            for index, row in self.star_proj.constellations.iterrows():
                # Convert the RA and Dec strings into numpy arrays
                ras = np.array([float(x) * 360 / 24 for x in row['ra'].replace('[', '').replace(']', '').split(',')])
                decs = np.array([float(x) for x in row['dec'].replace('[', '').replace(']', '').split(',')])
                
                # Wrap and sort the RA values
                wrapped_ras = self.star_proj._wrap_ra(ras)
                sorted_idx = np.argsort(wrapped_ras)
                sorted_ras = ras[sorted_idx]
                sorted_decs = decs[sorted_idx]
                
                # Convert each point into screen coordinates
                x = WIDTH / 2 + ((sorted_ras - self.star_proj.view_ra + 180) % 360 - 180) * scale_inv
                y = HEIGHT / 2 - (sorted_decs - self.star_proj.view_dec) * scale_inv
                
                for x_coord, y_coord in zip(x, y):
                    asterism_points.append((x_coord, y_coord))
            
            self.asterism_cache[cache_key] = asterism_points
        
        # Draw the computed asterism boundaries on the provided surface
        gray_color = (128, 128, 128)
        for x, y in self.asterism_cache[cache_key]:
            pygame.draw.circle(surface, gray_color, (int(x), int(y)), 1)

    def draw_constellation(self, surface, name):
        constellation = self.star_proj.constellations[self.star_proj.constellations['name'] == name]
        if not constellation.empty:
            ras = np.array([float(x)*15 for x in constellation['ra'].values[0].strip('[]').split(',')])
            decs = np.array([float(x) for x in constellation['dec'].values[0].strip('[]').split(',')])
            
            wrapped_ras = self.star_proj._wrap_ra(ras)
            x = WIDTH/2 + (wrapped_ras - self.star_proj.view_ra) / self.star_proj.scale
            y = HEIGHT/2 - (decs - self.star_proj.view_dec) / self.star_proj.scale
            
            points = np.column_stack([x, y]).astype(int)
            if len(points) >= 2:
                pygame.draw.lines(surface, CONSTELLATION_COLOR, False, points.tolist(), 2)

        name_data = self.star_proj.const_names[self.star_proj.const_names['name'] == name]
        if not name_data.empty:
            font = pygame.font.SysFont('Arial', 20)
            text = font.render(name, True, FONT_COLOR)
            x_pos = WIDTH/2 + (name_data['ra'].values[0]*15 - self.star_proj.view_ra)/self.star_proj.scale
            y_pos = HEIGHT/2 - (name_data['dec'].values[0] - self.star_proj.view_dec)/self.star_proj.scale
            surface.blit(text, (x_pos + 10, y_pos - 10))

    def draw_stars(self, surface):
        if self.star_proj.visible_stars is None or self.star_proj.visible_stars.empty:
            return
        
        stars = self.star_proj.visible_stars
        ras = stars['ra_deg'].values
        decs = stars['dec'].values
        mags = stars['mag'].values

        x_coords = WIDTH/2 + ((ras - self.star_proj.view_ra + 180) % 360 - 180)/self.star_proj.scale
        y_coords = HEIGHT/2 - (decs - self.star_proj.view_dec)/self.star_proj.scale

        valid = (x_coords >= 0) & (x_coords <= WIDTH) & (y_coords >= 0) & (y_coords <= HEIGHT)
        x_vis = x_coords[valid]
        y_vis = y_coords[valid]
        mags_vis = mags[valid]

        # Map magnitude to size.
        # This mapping makes brighter stars (lower mag) appear larger.
        sizes = np.maximum(1, (6 - mags_vis).astype(int))

        def compute_color(ci):
            if ci is None:
                return (255, 255, 255)
            try:
                # Using an approximate formula to compute temperature from color index.
                temperature = 4600 * (1/(0.92 * ci + 1.7) + 1/(0.92 * ci + 0.62))
            except Exception:
                return (255, 255, 255)
            # More vibrant color mapping:
            if temperature >= 10000:
                return (155, 176, 255)  # Bluish
            elif temperature >= 7500:
                return (170, 190, 255)  # Soft blue
            elif temperature >= 6000:
                return (255, 255, 255)  # White
            elif temperature >= 5000:
                return (255, 244, 214)  # Warm white
            else:
                return (255, 204, 111)  # Reddish
            
        if 'ci' in stars.columns:
            ci_all = stars['ci'].values
            ci_vis = ci_all[valid]
        else:
            ci_vis = [None] * len(x_vis)
        
        for x, y, size, ci in zip(x_vis, y_vis, sizes, ci_vis):
            color = compute_color(ci)
            pygame.draw.circle(surface, color, (int(x), int(y)), size)

    def draw_constellations(self, surface):
        cache_key = (int(self.star_proj.view_ra), int(self.star_proj.scale * 100))
        
        if cache_key not in self.constellation_cache:
            constellation_lines = []
            for index, row in self.star_proj.asterisms.iterrows():
                # Convert the RA and Dec strings into numpy arrays
                ras = np.array([float(x) * 360 / 24 for x in row['ra'].replace('[', '').replace(']', '').split(',')])
                decs = np.array([float(x) for x in row['dec'].replace('[', '').replace(']', '').split(',')])
                
                # Convert each segment into screen coordinates
                x, y = self.star_proj.convert_coordinates(ras, decs)
                
                points = np.column_stack([x, y]).astype(int)
                if len(points) >= 2:
                    # Filter out segments with large gaps to avoid random lines
                    dx_screen = np.abs(np.diff(x))
                    valid_segments = dx_screen < WIDTH * 0.8
                    start = 0
                    for i in range(len(valid_segments)):
                        if not valid_segments[i]:
                            if start <= i:
                                if len(points[start:i+1]) >= 2:
                                    constellation_lines.append(points[start:i+1])
                            start = i + 1
                    if start < len(points) and len(points[start:]) >= 2:
                        constellation_lines.append(points[start:])
            
            self.constellation_cache[cache_key] = constellation_lines
        
        # Draw the computed constellation lines on the provided surface
        for points in self.constellation_cache[cache_key]:
                if len(points) >= 2:
                    for i in range(0, len(points) - 1, 2):
                        p1 = points[i]
                        p2 = points[i + 1]
                        pygame.draw.line(surface, CONSTELLATION_COLOR, p1, p2, 2)

    def draw_constellation(self, surface, name):
        cache_key = (int(self.star_proj.view_ra), int(self.star_proj.scale * 100))
        
        if cache_key not in self.constellation_cache:
            constellation_lines = []
            for index, row in self.star_proj.asterisms[self.star_proj.asterisms['name'] == name].iterrows():
                # Convert the RA and Dec strings into numpy arrays
                ras = np.array([float(x) * 360 / 24 for x in row['ra'].replace('[', '').replace(']', '').split(',')])
                decs = np.array([float(x) for x in row['dec'].replace('[', '').replace(']', '').split(',')])
                
                # Convert each segment into screen coordinates
                x, y = self.star_proj.convert_coordinates(ras, decs)
                
                points = np.column_stack([x, y]).astype(int)
                if len(points) >= 2:
                    # Filter out segments with large gaps to avoid random lines
                    dx_screen = np.abs(np.diff(x))
                    valid_segments = dx_screen < WIDTH * 0.8
                    start = 0
                    for i in range(len(valid_segments)):
                        if not valid_segments[i]:
                            if start <= i:
                                if len(points[start:i+1]) >= 2:
                                    constellation_lines.append(points[start:i+1])
                            start = i + 1
                    if start < len(points) and len(points[start:]) >= 2:
                        constellation_lines.append(points[start:])
            
            self.constellation_cache[cache_key] = constellation_lines
        
        # Draw the computed constellation lines on the provided surface
        for points in self.constellation_cache[cache_key]:
            if len(points) >= 2:
                for i in range(0, len(points) - 1, 2):
                    p1 = points[i]
                    p2 = points[i + 1]
                    pygame.draw.line(surface, CONSTELLATION_COLOR, p1, p2, 2)

    # def _get_stars_in_constellation(self, constellation):
    #     """Get all star coordinates and adjacency relationships within the constellation."""
    #     all_points = []
    #     adjacency_list = []  # Store the adjacency relationships (i.e., consecutive points)

    #     # Get all asterism data for the specified constellation
    #     constellation_data = self.star_proj.asterisms[self.star_proj.asterisms['name'] == constellation]

    #     for _, row in constellation_data.iterrows():
    #         # Convert the raw RA and Dec strings into numpy arrays
    #         ras = np.array([float(x) * 360 / 24 for x in row['ra'].strip('[]').split(',')])
    #         decs = np.array([float(x) for x in row['dec'].strip('[]').split(',')])

    #         # Convert astronomical coordinates to screen coordinates
    #         x_coords = WIDTH / 2 + ((ras - self.star_proj.view_ra + 180) % 360 - 180) / self.star_proj.scale
    #         y_coords = HEIGHT / 2 - (decs - self.star_proj.view_dec) / self.star_proj.scale
    #         points = np.column_stack((x_coords, y_coords)).astype(int)

    #         # Create adjacency relationships (connect consecutive points)
    #         for i in range(len(points) - 1):
    #             adjacency_list.append((tuple(points[i]), tuple(points[i + 1])))

    #         all_points.extend(points.tolist())

    #     return np.array(all_points), adjacency_list

    def draw_selected_stars(self, surface, stars):
        if not stars:
            return

        # Get the actual astronomical coordinates of all selected points
        selected_points = np.array([(star[0][0], star[0][1]) for star in stars])
        constellation = stars[0][1]

        # Drawing logic
        cache_key = (int(self.star_proj.view_ra), int(self.star_proj.scale * 100), constellation)
        for points in self.constellation_cache[cache_key]:
                if len(points) >= 2:
                    for i in range(0, len(points) - 1, 2):
                        p1 = points[i]
                        p2 = points[i + 1]
                        index_p1 = np.where(np.all(selected_points == p1, axis=1))
                        index_p2 = np.where(np.all(selected_points == p2, axis=1))

                        if index_p1

        # for constellation in constellations:
        #     # Get the screen coordinates and adjacency relationships for the given constellation
        #     cache_key = (int(self.star_proj.view_ra), int(self.star_proj.scale * 100), constellation)
        #     if cache_key not in self.constellation_cache:
        #         points, adjacency = self._get_stars_in_constellation(constellation)
        #         self.constellation_cache[cache_key] = (points, adjacency)
        #     else:
        #         constellation_lines = self.constellation_cache[cache_key]

        #     # Find the selected points that belong to the current constellation
        #     constellation_stars = [star for star in stars if star[1] == constellation]
        #     selected_points = np.array([(star[0][0], star[0][1]) for star in constellation_stars])

        #     # Generate connected pairs (in astronomical coordinates)
        #     connected_pairs = []
        #     for (p1, p2) in adjacency:
        #         # Check if both endpoints are among the selected points (using an absolute tolerance)
        #         p1_in_selected = np.any(np.all(np.isclose(selected_points, p1, atol=10), axis=1))
        #         p2_in_selected = np.any(np.all(np.isclose(selected_points, p2, atol=10), axis=1))

        #         if p1_in_selected and p2_in_selected:
        #             connected_pairs.append((p1, p2))

        #     # Draw the connecting lines
        #     for p1, p2 in connected_pairs:
        #         # Convert to screen coordinates (if not already in screen coordinates)
        #         x1 = WIDTH / 2 + ((p1[0] - self.star_proj.view_ra + 180) % 360 - 180) / self.star_proj.scale
        #         y1 = HEIGHT / 2 - (p1[1] - self.star_proj.view_dec) / self.star_proj.scale
        #         x2 = WIDTH / 2 + ((p2[0] - self.star_proj.view_ra + 180) % 360 - 180) / self.star_proj.scale
        #         y2 = HEIGHT / 2 - (p2[1] - self.star_proj.view_dec) / self.star_proj.scale

        #         # Check if the screen span is reasonable
        #         if abs(x2 - x1) < WIDTH * 0.8:
        #             pygame.draw.aaline(surface, SELECTED_LINE_COLOR,
        #                             (int(x1), int(y1)), (int(x2), int(y2)), 3)

        # Draw markers for the selected points (maintaining original logic)
        ras = np.array([star[0][0] for star in stars])
        decs = np.array([star[0][1] for star in stars])
        x_coords = WIDTH / 2 + ((ras - self.star_proj.view_ra + 180) % 360 - 180) / self.star_proj.scale
        y_coords = HEIGHT / 2 - (decs - self.star_proj.view_dec) / self.star_proj.scale

        for x, y in zip(x_coords, y_coords):
            pygame.draw.circle(surface, SELECTED_COLOR, (int(x), int(y)), 8)
