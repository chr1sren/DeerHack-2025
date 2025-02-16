import pandas as pd
import numpy as np

def loadData():
    # Process asterism
    df = pd.read_csv('./data/constellationship.fab', header=None)
    df['constellation'] = df[0].str.split().str.get(0)
    df['num_pairs'] = df[0].str.split().str.get(1)
    df['stars'] = df[0].str.split().str[2:]
    df.drop(0, axis=1, inplace=True)

    df_names = pd.read_csv('./data/constellation_names.eng.fab', header=None)
    df_names = df_names[0].str.replace('\t', '').str.split('"', expand=True)
    df_names.drop([2, 3, 4], axis=1, inplace=True)
    df_names.columns = ['constellation', 'name']

    assert len(df) == len(df_names)
    df = pd.merge(df, df_names, on="constellation")

    stars = [float(y) for x in df['stars'].tolist() for y in x]
    stars = sorted(set(stars))

    hip_df = pd.read_csv('./data/hygdata_processed.csv', low_memory=False)
    ras, decs, = [], []
    for star in stars: 
        temp = hip_df[hip_df['hip']==star]
        assert len(temp) == 1
        ras.append(temp['ra'].tolist()[0])
        decs.append(temp['dec'].tolist()[0])

    star_df = pd.DataFrame(data={'star_ID':stars, 'ra':ras, 'dec':decs})

    df['ra'] = ''
    df['dec'] = ''

    for index, row in df.iterrows(): 
        ras, decs = [], []
        for star in row['stars']: 
            temp = hip_df[hip_df['hip']==float(star)]
            assert len(temp) == 1
            ras.append(temp['ra'].tolist()[0])
            decs.append(temp['dec'].tolist()[0])
        df.at[index, 'ra'] = ras
        df.at[index, 'dec'] = decs

    zodiacs = ['Aquarius', 'Aries', 'Cancer', 'Capricornus', 'Gemini', 'Leo', 'Libra', 
            'Pisces', 'Sagittarius', 'Scorpius', 'Taurus', 'Virgo']
    df['zodiac'] = df['name'].isin(zodiacs)
    assert df['zodiac'].sum() == 12
    df.to_csv('./data/asterisms.csv', index=False)

    # Process constellation vectors
    colwidths = [11, 11, 5, 100]
    colnames = ['right_ascension_hours', 'declination_degrees', 'const_abbreviation', 'type_point']

    df = pd.read_fwf('./data/bound_20.dat', widths=colwidths, names=colnames)

    const, ras, decs = [], [], []

    for name, group in df.groupby('const_abbreviation'):
        const.append(name)
        ras.append(group['right_ascension_hours'].tolist())
        decs.append(group['declination_degrees'].tolist())
        
    df_ra_dec = pd.DataFrame(data={'name':const, 'ra':ras, 'dec':decs})

    savename = './data/constellations.csv'
    df_ra_dec.to_csv('./data/constellations.csv', index=False)


    # Load datasets
    stars = pd.read_csv('./data/hygdata_processed_mag65.csv')
    asterisms = pd.read_csv('./data/asterisms.csv')
    constellations = pd.read_csv('./data/constellations.csv')
    const_names = pd.read_csv('./data/centered_constellations.csv', encoding="latin-1")

    # Preprocess coordinates
    stars['ra_deg'] = stars['ra'] * 15  # Convert hours to degrees
    
    return stars, asterisms, constellations, const_names
