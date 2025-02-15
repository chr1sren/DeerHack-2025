from config import *
from load_data import loadData
import pandas as pd
import numpy as np

class StarMap:
    def __init__(self):
        # Load datasets
        self.stars, self.asterisms, self.constellations, self.const_names = loadData()
        
        # Initialize view parameters
        self._calculate_view_params()
        self._scale = self.min_scale
        self._view_ra = self.map_center_ra
        self._view_dec = self.map_center_dec
        
        # Performance optimizations
        self.visible_stars = None
        self.last_view_params = None
        self.drag_sensitivity = 1.2

    def _calculate_view_params(self):
        """Calculate map boundaries and scale limits"""
        ras = self.stars['ra_deg'] % 360
        sorted_ras = sorted(ras)
        
        max_gap = 0
        gap_start = 0
        for i in range(1, len(sorted_ras)):
            gap = sorted_ras[i] - sorted_ras[i-1]
            if gap > max_gap:
                max_gap = gap
                gap_start = sorted_ras[i-1]
        
        if max_gap > 180:
            self.min_ra = gap_start
            self.max_ra = (gap_start + max_gap) % 360
            adjusted_ras = [x if x >= gap_start else x+360 for x in sorted_ras]
            self.map_center_ra = np.mean(adjusted_ras) % 360
        else:
            self.min_ra = sorted_ras[0]
            self.max_ra = sorted_ras[-1]
            self.map_center_ra = (self.min_ra + self.max_ra) / 2 % 360
        
        self.min_dec = self.stars['dec'].min()
        self.max_dec = self.stars['dec'].max()
        self.map_center_dec = (self.min_dec + self.max_dec) / 2
        
        map_width = self.max_ra - self.min_ra if self.max_ra > self.min_ra else (360 - self.min_ra) + self.max_ra
        map_height = self.max_dec - self.min_dec
        self.min_scale = max(map_width/WIDTH, map_height/HEIGHT) * 1.05
        self.max_scale = self.min_scale / 50

    def _clamp_view(self):
        """Constrain view within valid boundaries"""
        visible_height = HEIGHT * self.scale
        self._view_dec = np.clip(self._view_dec,
                               self.min_dec + visible_height/2,
                               self.max_dec - visible_height/2)
        self._view_ra %= 360

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

    @property
    def view_ra(self):
        return self._view_ra

    @view_ra.setter
    def view_ra(self, value):
        self._view_ra = value % 360
        self._clamp_view()
        self._update_visible_stars()

    @property
    def view_dec(self):
        return self._view_dec

    @view_dec.setter
    def view_dec(self, value):
        self._view_dec = value
        self._clamp_view()
        self._update_visible_stars()

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value):
        self._scale = np.clip(value, self.max_scale, self.min_scale)
        self._clamp_view()
        self._update_visible_stars()