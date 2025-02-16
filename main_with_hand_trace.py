import pygame
from config import *
from star_projection import StarMap
from render import Renderer
from selection import find_nearest_star
from hand_trace_demo import HandGestureController
from main import main

import threading
import mediapipe as mp

def run_mediapipe():
    controller = HandGestureController()
    controller.run()

def run_pygame():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    
    # Initialize star projection and renderer
    star_proj = StarMap()
    renderer = Renderer(star_proj)
    
    # Interaction state variables
    dragging = False
    last_pos = (0, 0)
    drag_sensitivity = 1.2  # Mouse drag-to-pan ratio

    # Enable optimized display flags
    flags = pygame.DOUBLEBUF | pygame.HWSURFACE  # Double buffering & hardware acceleration
    screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
    
    # Create off-screen buffer for smooth rendering
    back_buffer = pygame.Surface((WIDTH, HEIGHT))

    running = True
    while running:
        # Event processing loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            # Mouse event handling
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    selected, constellation = find_nearest_star(star_proj, event.pos[0], event.pos[1])
                    if selected is not None and constellation is not None:
                        if len(star_proj.selected_stars) > 0 and constellation == star_proj.selected_stars[-1][1]:
                            star_proj.selected_stars.append([selected, constellation])
                        else:
                            star_proj.selected_stars = [[selected, constellation]]  # Restart selection
                
                elif event.button == 3:  # Right mouse button
                    dragging = True
                    last_pos = event.pos
                    renderer.asterism_cache.clear()  # Clear cached asterism paths
                    renderer.constellation_cache.clear()  # Clear cached constellation paths

                elif event.button == 4:  # Mouse wheel up (zoom in)
                    star_proj.scale = max(star_proj.scale * 0.9, star_proj.max_scale)
                    renderer.asterism_cache.clear()  # Clear cached asterism paths
                    renderer.constellation_cache.clear()  # Clear cached constellation paths

                elif event.button == 5:  # Mouse wheel down (zoom out)
                    star_proj.scale = min(star_proj.scale * 1.1, star_proj.min_scale)
                    renderer.asterism_cache.clear()  # Clear cached asterism paths
                    renderer.constellation_cache.clear()  # Clear cached constellation paths
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3:  # Left button release
                    dragging = False
            
            elif event.type == pygame.MOUSEMOTION and dragging:
                # Calculate pan movement
                dx, dy = event.pos[0] - last_pos[0], event.pos[1] - last_pos[1]
                last_pos = event.pos
                
                # Update view coordinates
                star_proj.view_ra -= dx * star_proj.scale * drag_sensitivity
                star_proj.view_dec += dy * star_proj.scale * drag_sensitivity
                renderer.asterism_cache.clear()  # Invalidate cached paths
                renderer.constellation_cache.clear()  # Invalidate cached paths

        # Rendering pipeline
        back_buffer.fill(BACKGROUND_COLOR)  # Clear background
        
        # Draw celestial elements
        renderer.draw_boundaries(back_buffer)  # Draw constellation boundaries
        # renderer.draw_constellations(back_buffer)  # Draw constellation lines
        # renderer.draw_constellation(back_buffer, "Leo")  # Draw Leo constellation
        renderer.draw_stars(back_buffer)  # Draw visible stars

        # Draw selected stars
        renderer.draw_selected_stars(back_buffer, star_proj.selected_stars)
        
        # Update display
        screen.blit(back_buffer, (0, 0))
        pygame.display.flip()  # Swap buffers
        
        clock.tick(60)  # Maintain 60 FPS

    pygame.quit()


# Run both tasks in parallel
t1 = threading.Thread(target=run_mediapipe)
t2 = threading.Thread(target=run_pygame)

t1.start()
t2.start()

t1.join()
t2.join()
