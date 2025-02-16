import math
import numpy as np
from config import *
from star_projection import StarMap

def euclidean_distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def find_nearest_star(star_proj, mouse_x, mouse_y):
    for _, row in star_proj.asterisms.iterrows():
        # Convert the RA and Dec strings into numpy arrays
        ras = np.array([float(x) * 360 / 24 for x in row['ra'].replace('[', '').replace(']', '').split(',')])
        decs = np.array([float(x) for x in row['dec'].replace('[', '').replace(']', '').split(',')])
    
        x_stars = WIDTH / 2 + ((ras - star_proj.view_ra + 180) % 360 - 180) / star_proj.scale
        y_stars = HEIGHT / 2 - (decs - star_proj.view_dec) / star_proj.scale
        
        distances = np.sqrt((x_stars - mouse_x) ** 2 + (y_stars - mouse_y) ** 2)
        min_idx = np.argmin(distances)
    
        if distances[min_idx] < 10:  # Threshold for selection
            constellation = row['name']
            #print(constellation)
            #print(ras[min_idx], decs[min_idx])
            return (ras[min_idx], decs[min_idx]), constellation
    return None, None