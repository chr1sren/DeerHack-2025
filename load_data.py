from convert_angles import *
import math
import os
import csv

def loadData():
    STAR_FILE = "data/constellations.csv"  # Star catalog file

    # Check if file exists
    if not os.path.exists(STAR_FILE):
        print(f"Error: {STAR_FILE} not found!")
        exit(1)

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
    return stars