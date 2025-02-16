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
    main.main()

# Run both tasks in parallel
t1 = threading.Thread(target=run_mediapipe)
t2 = threading.Thread(target=run_pygame)

t1.start()
t2.start()

t1.join()
t2.join()
