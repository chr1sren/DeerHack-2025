import pygame
import numpy as np
from config import *

class Renderer:
    def __init__(self, star_projection):
        self.star_proj = star_projection
        self.asterism_cache = {}
        self.constellation_cache = {}

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
        for x, y in self.asterism_cache[cache_key]:
            pygame.draw.circle(surface, ASTERISM_COLOR, (int(x), int(y)), 2)

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
        
        sizes = np.maximum(1, (3 - mags_vis/2).astype(int))
        for x, y, size in zip(x_vis, y_vis, sizes):
            pygame.draw.circle(surface, (255,255,255), (int(x), int(y)), size)

    def draw_constellations(self, surface):
        scale_inv = 1.0 / self.star_proj.scale
        cache_key = (int(self.star_proj.view_ra), int(self.star_proj.scale * 100))
        
        if cache_key not in self.constellation_cache:
            constellation_lines = []
            for index, row in self.star_proj.asterisms.iterrows():
                # Convert the RA and Dec strings into numpy arrays
                ras = np.array([float(x) * 360 / 24 for x in row['ra'].replace('[', '').replace(']', '').split(',')])
                decs = np.array([float(x) for x in row['dec'].replace('[', '').replace(']', '').split(',')])
                
                # Wrap and sort the RA values
                # wrapped_ras = self.star_proj._wrap_ra(ras)
                # sorted_idx = np.argsort(wrapped_ras)
                # sorted_ras = ras[sorted_idx]
                # sorted_decs = decs[sorted_idx]
                
                # Convert each segment into screen coordinates
                x = WIDTH / 2 + ((ras - self.star_proj.view_ra + 180) % 360 - 180) * scale_inv
                y = HEIGHT / 2 - (decs - self.star_proj.view_dec) * scale_inv
                
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
                pygame.draw.lines(surface, CONSTELLATION_COLOR, False, points, 2)

    def draw_constellation(self, surface, name):
        scale_inv = 1.0 / self.star_proj.scale
        cache_key = (int(self.star_proj.view_ra), int(self.star_proj.scale * 100))
        
        if cache_key not in self.constellation_cache:
            constellation_lines = []
            for index, row in self.star_proj.asterisms[self.star_proj.asterisms['name'] == name].iterrows():
                # Convert the RA and Dec strings into numpy arrays
                ras = np.array([float(x) * 360 / 24 for x in row['ra'].replace('[', '').replace(']', '').split(',')])
                decs = np.array([float(x) for x in row['dec'].replace('[', '').replace(']', '').split(',')])
                
                # Wrap and sort the RA values
                # wrapped_ras = self.star_proj._wrap_ra(ras)
                # sorted_idx = np.argsort(wrapped_ras)
                # sorted_ras = ras[sorted_idx]
                # sorted_decs = decs[sorted_idx]
                
                # Convert each segment into screen coordinates
                x = WIDTH / 2 + ((ras - self.star_proj.view_ra + 180) % 360 - 180) * scale_inv
                y = HEIGHT / 2 - (decs - self.star_proj.view_dec) * scale_inv
                
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
                print(points)
                pygame.draw.lines(surface, CONSTELLATION_COLOR, False, points, 2)