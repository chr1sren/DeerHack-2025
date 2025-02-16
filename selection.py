import math
import numpy as np
from config import *
from star_projection import StarMap

def euclidean_distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def find_nearest_star(star_proj, x, y):
    
    nearest_star = None
    min_distance = 10 # minimum distance to a star
    for _, row in star_proj.asterisms.iterrows():
        # Convert the RA and Dec strings into numpy arrays
        ras = np.array([float(x) * 360 / 24 for x in row['ra'].replace('[', '').replace(']', '').split(',')])
        decs = np.array([float(x) for x in row['dec'].replace('[', '').replace(']', '').split(',')])
        # Convert each segment into screen coordinates
        x_stars = WIDTH/2 + ((ras - self.star_proj.view_ra + 180) % 360 - 180)/self.star_proj.scale
        y_stars = HEIGHT/2 - (decs - self.star_proj.view_dec)/self.star_proj.scale

        valid = (x_stars >= 0) & (x_stars <= WIDTH) & (y_stars >= 0) & (y_stars <= HEIGHT)
        x_vis = x_stars[valid]
        y_vis = x_stars[valid]
        
        # x_stars, y_stars = star_proj.convert_coordinates(ras, decs)

        for i in range(len(x_stars)):
            x_star = x_stars[i]
            y_star = y_stars[i]
            distance = euclidean_distance(x, y, x_star, y_star)
            if distance < min_distance:
                min_distance = distance
                nearest_star = [x_star, y_star]

    return nearest_star