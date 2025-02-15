import cv2
import mediapipe as mp
import math
import time

GRIP_THRESHOLD = 40
DRAG_SMOOTHING = 0.5
ZOOM_SMOOTHING_DELTA = 5

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

prev_drag_point = None
prev_zoom_distance = None
prev_time = time.time()

def get_grip_point(hand_landmarks, frame_shape):
    h, w, _ = frame_shape
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    x1, y1 = int(thumb_tip.x * w), int(thumb_tip.y * h)
    x2, y2 = int(index_tip.x * w), int(index_tip.y * h)
    if math.hypot(x2 - x1, y2 - y1) < GRIP_THRESHOLD:
        return ((x1 + x2) // 2, (y1 + y2) // 2)
    return None

def process_drag(current_point, prev_point):
    if prev_point is None:
        return current_point, (0, 0)
    dx = int((current_point[0] - prev_point[0]) * DRAG_SMOOTHING)
    dy = int((current_point[1] - prev_point[1]) * DRAG_SMOOTHING)
    return current_point, (dx, dy)

def process_zoom(gp1, gp2, prev_distance):
    current_distance = math.hypot(gp2[0] - gp1[0], gp2[1] - gp1[1])
    zoom_action = None
    if prev_distance is not None:
        delta = current_distance - prev_distance
        if delta > ZOOM_SMOOTHING_DELTA:
            zoom_action = "Zooming out"
        elif delta < -ZOOM_SMOOTHING_DELTA:
            zoom_action = "Zooming in"
    return current_distance, zoom_action

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)

    current_time = time.time()
    fps = 1 / (current_time - prev_time)
    prev_time = current_time

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)
    
    grip_points = []
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            grip = get_grip_point(hand_landmarks, frame.shape)
            if grip:
                grip_points.append(grip)
                cv2.circle(frame, grip, 8, (0, 0, 255), cv2.FILLED)
            h, w, _ = frame.shape
            thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
            index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            x1, y1 = int(thumb_tip.x * w), int(thumb_tip.y * h)
            x2, y2 = int(index_tip.x * w), int(index_tip.y * h)
            cv2.circle(frame, (x1, y1), 5, (255, 0, 0), cv2.FILLED)
            cv2.circle(frame, (x2, y2), 5, (255, 0, 0), cv2.FILLED)
            cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    
    if len(grip_points) == 1:
        current_point = grip_points[0]
        prev_drag_point, delta = process_drag(current_point, prev_drag_point)
        cv2.putText(frame, "Dragging Map", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.arrowedLine(frame, current_point, (current_point[0] + delta[0], current_point[1] + delta[1]), (255, 0, 255), 2)
        prev_zoom_distance = None
    elif len(grip_points) == 2:
        gp1, gp2 = grip_points
        current_zoom_distance, zoom_action = process_zoom(gp1, gp2, prev_zoom_distance)
        prev_zoom_distance = current_zoom_distance
        text = zoom_action if zoom_action else "Pinch detected"
        cv2.putText(frame, text, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        cv2.line(frame, gp1, gp2, (0, 255, 255), 2)
        prev_drag_point = None
    else:
        prev_drag_point = None
        prev_zoom_distance = None

    cv2.putText(frame, f"FPS: {int(fps)}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

    cv2.imshow("MediaPipe Hands - Gesture Map Control", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()