# ---------------------------
# FUNCTION TO CONVERT RA (hh:mm:ss) TO DEGREES
# ---------------------------
def ra_to_degrees(ra_str):
    """ Converts RA from hh:mm:ss format to degrees. """
    ra_parts = ra_str.split("h")
    hours = float(ra_parts[0].strip())
    minutes_seconds = ra_parts[1].split("m")
    minutes = float(minutes_seconds[0].strip())
    seconds = float(minutes_seconds[1].replace("s", "").strip())
    
    # Convert to degrees (1 hour = 15 degrees)
    ra_degrees = (hours + minutes / 60 + seconds / 3600) * 15
    return ra_degrees

# ---------------------------
# FUNCTION TO CONVERT DEC (dd° mm′ ss″) TO DEGREES
# ---------------------------
def dec_to_degrees(dec_str):
    """ Converts Dec from dd° mm′ ss″ format to degrees. """
    dec_parts = dec_str.split("°")
    degrees = float(dec_parts[0].strip())
    minutes_seconds = dec_parts[1].split("′")
    minutes = float(minutes_seconds[0].strip())
    seconds = float(minutes_seconds[1].replace("″", "").strip())
    
    # Convert to degrees
    dec_degrees = degrees + (minutes / 60) + (seconds / 3600)
    
    # If it's a negative declination (South), convert to negative degrees
    if dec_str[0] == "-":
        dec_degrees = -dec_degrees
    return dec_degrees