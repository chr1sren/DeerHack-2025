import pandas as pd
import numpy as np

def loadData():
    # Load datasets
    stars = pd.read_csv('./data/hygdata_processed_mag65.csv')
    asterisms = pd.read_csv('./data/asterisms.csv')
    constellations = pd.read_csv('./data/constellations.csv')
    const_names = pd.read_csv('./data/centered_constellations.csv', encoding="latin-1")

    # Preprocess coordinates
    stars['ra_deg'] = stars['ra'] * 15  # Convert hours to degrees
    
    return stars, asterisms, constellations, const_names
