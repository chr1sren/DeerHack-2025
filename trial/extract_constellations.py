import csv
import gzip

STAR_FILE = "hyg_v38.csv.gz"
CONSTELLATION_FILE = "constellations.txt"

# Load star data
stars = {}
with gzip.open(STAR_FILE, mode='rt', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        try:
            hip = int(row['hip']) if row['hip'] else None
            if hip:
                stars[hip] = row
        except ValueError:
            continue

# Example constellation data (replace with actual data source)
constellation_data = [
    # Orion
    (24436, 25336),
    (25336, 26727),
    (26727, 27989),
    (27989, 28614),
    (28614, 29426),
    (29426, 28691),
    (28691, 27989),
    # Add more constellations as needed
]

# Write constellation lines to file
with open(CONSTELLATION_FILE, 'w') as file:
    for star1, star2 in constellation_data:
        if star1 in stars and star2 in stars:
            file.write(f"{star1} {star2}\n")

print(f"Constellation lines written to {CONSTELLATION_FILE}")
