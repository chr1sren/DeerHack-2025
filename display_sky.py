import pygame
import pandas as pd
import numpy as np

# Configuration constants
WIDTH, HEIGHT = 1200, 600  # 2:1 aspect ratio
BACKGROUND_COLOR = (0, 0, 0)
ASTERISM_COLOR = (255, 0, 0)
CONSTELLATION_COLOR = (100, 100, 255)
FONT_COLOR = (200, 200, 255)

class StarMap:
    def __init__(self):
        # Load datasets
        self.stars = pd.read_csv('./data/hygdata_processed_mag65.csv')
        self.asterisms = pd.read_csv('./data/asterisms.csv')
        self.constellations = pd.read_csv('./data/constellations.csv')
        self.const_names = pd.read_csv('./data/centered_constellations.csv', encoding="latin-1")

        # Preprocess coordinates
        self.stars['ra_deg'] = self.stars['ra'] * 15  # Convert hours to degrees
        
        # Initialize view parameters
        self._calculate_view_params()
        self.scale = self.min_scale
        self.view_ra = self.map_center_ra
        self.view_dec = self.map_center_dec
        
        # Performance optimizations
        self.visible_stars = None
        self.last_view_params = None
        self.drag_sensitivity = 1.2
        self.asterism_cache = {}

    def _calculate_view_params(self):
        """Calculate map boundaries and scale limits"""
        # RA boundary calculation with 360° wrapping
        ras = self.stars['ra_deg'] % 360
        sorted_ras = sorted(ras)
        
        # Find largest RA gap
        max_gap = 0
        gap_start = 0
        for i in range(1, len(sorted_ras)):
            gap = sorted_ras[i] - sorted_ras[i-1]
            if gap > max_gap:
                max_gap = gap
                gap_start = sorted_ras[i-1]
        
        # Calculate effective boundaries
        if max_gap > 180:
            self.min_ra = gap_start
            self.max_ra = (gap_start + max_gap) % 360
            adjusted_ras = [x if x >= gap_start else x+360 for x in sorted_ras]
            self.map_center_ra = np.mean(adjusted_ras) % 360
        else:
            self.min_ra = sorted_ras[0]
            self.max_ra = sorted_ras[-1]
            self.map_center_ra = (self.min_ra + self.max_ra) / 2 % 360
        
        # DEC boundaries
        self.min_dec = self.stars['dec'].min()
        self.max_dec = self.stars['dec'].max()
        self.map_center_dec = (self.min_dec + self.max_dec) / 2
        
        # Scale limits calculation
        map_width = self.max_ra - self.min_ra if self.max_ra > self.min_ra else (360 - self.min_ra) + self.max_ra
        map_height = self.max_dec - self.min_dec
        self.min_scale = max(map_width/WIDTH, map_height/HEIGHT) * 1.05
        self.max_scale = self.min_scale / 50

    def _clamp_view(self):
        """Constrain view within valid boundaries"""
        # Calculate visible area boundaries
        visible_height = HEIGHT * self.scale
        
        # Constrain declination range
        self.view_dec = np.clip(self.view_dec,
                              self.min_dec + visible_height/2,
                              self.max_dec - visible_height/2)
        self.view_ra %= 360  # Normalize RA

    def _update_visible_stars(self):
        """Precompute visible stars for performance optimization"""
        current_view = (self.view_ra, self.view_dec, self.scale)
        if current_view == self.last_view_params:
            return
        
        view_width = WIDTH * self.scale
        view_height = HEIGHT * self.scale
        
        ras = self.stars['ra_deg'].values
        decs = self.stars['dec'].values
        
        ra_diffs = (ras - self.view_ra + 180) % 360 - 180
        dec_diffs = decs - self.view_dec
        
        visible_mask = (np.abs(ra_diffs) < view_width/2) & (np.abs(dec_diffs) < view_height/2)
        self.visible_stars = self.stars[visible_mask]
        self.last_view_params = current_view

    def _wrap_ra(self, ras):
        """Handle RA periodicity wrapping"""
        base_ra = self.view_ra
        return np.where(ras - base_ra > 180, ras - 360,
                      np.where(ras - base_ra < -180, ras + 360, ras))

    def draw_asterisms(self, surface):
        """Draw asterism boundaries with automatic segmentation"""
        scale_inv = 1.0 / self.scale
        cache_key = (int(self.view_ra), int(self.scale*100))
        
        if cache_key not in self.asterism_cache:
            asterism_lines = []
            for _, asterism in self.asterisms.iterrows():
                # Convert to numpy arrays
                ras = np.array([float(x)*15 for x in asterism['ra'].strip('[]').split(',')])
                decs = np.array([float(x) for x in asterism['dec'].strip('[]').split(',')])
                
                # Handle periodicity and sorting
                wrapped_ras = self._wrap_ra(ras)
                sorted_idx = np.argsort(wrapped_ras)
                
                # Fix 1: Correctly sort original coordinates
                sorted_ras = ras[sorted_idx]  # Use original RA values for sorting
                sorted_decs = decs[sorted_idx]
                
                # Segment connections
                segments = []
                current_segment = []
                prev_ra = None
                
                # Fix 2: Add maximum visible span detection
                max_visible_span = 180 / self.scale  # Dynamic threshold
                
                for ra, dec in zip(sorted_ras, sorted_decs):
                    if prev_ra is not None:
                        # Calculate actual screen-spanning distance
                        dx = abs(ra - prev_ra)
                        # Handle 360° wrapping
                        dx = min(dx, 360 - dx)
                        
                        if dx > max_visible_span * 1.2:  # Add safety factor
                            if current_segment:
                                segments.append(current_segment)
                            current_segment = []
                    
                    current_segment.append((ra, dec))
                    prev_ra = ra
                
                if current_segment:
                    segments.append(current_segment)
                
                # Convert coordinates
                for seg in segments:
                    ras_seg, decs_seg = np.array(seg).T
                    
                    # Convert to screen coordinates
                    x = WIDTH/2 + ((ras_seg - self.view_ra + 180) % 360 - 180) * scale_inv
                    y = HEIGHT/2 - (decs_seg - self.view_dec) * scale_inv
                    
                    # Filter cross-screen connections
                    dx_screen = np.abs(np.diff(x))
                    valid_segments = dx_screen < WIDTH * 0.8  # Prevent screen-spanning
                    
                    # Split valid segments
                    start = 0
                    for i in range(len(valid_segments)):
                        if not valid_segments[i]:
                            if start <= i:
                                asterism_lines.append((x[start:i+1], y[start:i+1]))
                            start = i+1
                    if start < len(x):
                        asterism_lines.append((x[start:], y[start:]))
            
            self.asterism_cache[cache_key] = asterism_lines
        
        # Draw optimized lines
        for x, y in self.asterism_cache[cache_key]:
            points = np.column_stack([x, y]).astype(int)
            if len(points) >= 2:
                pygame.draw.aalines(surface, ASTERISM_COLOR, False, points, 1)

    def draw_constellation(self, surface, name):
        """Draw specified constellation"""
        constellation = self.constellations[self.constellations['name'] == name]
        if not constellation.empty:
            # Process constellation lines
            ras = np.array([float(x)*15 for x in constellation['ra'].values[0].strip('[]').split(',')])
            decs = np.array([float(x) for x in constellation['dec'].values[0].strip('[]').split(',')])
            
            # Handle periodicity
            wrapped_ras = self._wrap_ra(ras)
            x = WIDTH/2 + (wrapped_ras - self.view_ra) / self.scale
            y = HEIGHT/2 - (decs - self.view_dec) / self.scale
            
            # Draw lines
            points = np.column_stack([x, y]).astype(int)
            if len(points) >= 2:
                pygame.draw.lines(surface, CONSTELLATION_COLOR, False, points.tolist(), 2)

        # Draw constellation name
        name_data = self.const_names[self.const_names['name'] == name]
        if not name_data.empty:
            font = pygame.font.SysFont('Arial', 20)
            text = font.render(name, True, FONT_COLOR)
            x_pos = WIDTH/2 + (name_data['ra'].values[0]*15 - self.view_ra)/self.scale
            y_pos = HEIGHT/2 - (name_data['dec'].values[0] - self.view_dec)/self.scale
            surface.blit(text, (x_pos + 10, y_pos - 10))

    def draw_stars(self, surface):
        """Render visible stars with performance optimizations"""
        self._update_visible_stars()
        
        if self.visible_stars is None or self.visible_stars.empty:
            return
        
        # Vectorized coordinate calculation
        ras = self.visible_stars['ra_deg'].values
        decs = self.visible_stars['dec'].values
        mags = self.visible_stars['mag'].values
        
        x_coords = WIDTH/2 + ((ras - self.view_ra + 180) % 360 - 180)/self.scale
        y_coords = HEIGHT/2 - (decs - self.view_dec)/self.scale
        
        # Filter visible points
        valid = (x_coords >= 0) & (x_coords <= WIDTH) & (y_coords >= 0) & (y_coords <= HEIGHT)
        x_vis = x_coords[valid]
        y_vis = y_coords[valid]
        mags_vis = mags[valid]
        
        # Batch rendering
        sizes = np.maximum(1, (3 - mags_vis/2).astype(int))
        for x, y, size in zip(x_vis, y_vis, sizes):
            pygame.draw.circle(surface, (255,255,255), (int(x), int(y)), size)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    
    star_map = StarMap()
    dragging = False
    last_pos = (0, 0)

    # Enable double buffering and hardware acceleration
    flags = pygame.DOUBLEBUF | pygame.HWSURFACE
    screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
    
    # Create off-screen surface to reduce flickering
    back_buffer = pygame.Surface((WIDTH, HEIGHT))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            # Handle mouse events
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    dragging = True
                    last_pos = event.pos
                    star_map.asterism_cache.clear()
                elif event.button == 4:  # Mouse wheel up (zoom in)
                    star_map.scale = max(star_map.scale * 0.9, star_map.max_scale)
                elif event.button == 5:  # Mouse wheel down (zoom out)
                    star_map.scale = min(star_map.scale * 1.1, star_map.min_scale)
                star_map._clamp_view()
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left button release
                    dragging = False
            
            elif event.type == pygame.MOUSEMOTION:
                if dragging:  # Only process movement when dragging
                    dx = event.pos[0] - last_pos[0]
                    dy = event.pos[1] - last_pos[1]
                    last_pos = event.pos
                    
                    delta_ra = dx * star_map.scale * star_map.drag_sensitivity
                    delta_dec = dy * star_map.scale * star_map.drag_sensitivity
                    star_map.view_ra -= delta_ra
                    star_map.view_dec += delta_dec
                    star_map._clamp_view()
                    star_map.asterism_cache.clear()

        # Drawing pipeline
        back_buffer.fill(BACKGROUND_COLOR)
        
        # Draw static content first
        star_map.draw_asterisms(back_buffer)
        
        # Then draw dynamic content
        star_map.draw_stars(back_buffer)
        
        # Single blit to reduce flickering
        screen.blit(back_buffer, (0, 0))
        pygame.display.flip()
        
        clock.tick(60)  # Maintain stable frame rate

    pygame.quit()

if __name__ == "__main__":
    main()