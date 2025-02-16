import cv2
import mediapipe as mp
import math
import time
import pyautogui

class HandGestureController:
    GRIP_THRESHOLD = 40
    DRAG_SMOOTHING = 0.5
    ZOOM_SMOOTHING_DELTA = 5

    # Initializes the hand gesture controller and sets up video capture.
    def __init__(self, camera_index=0):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
        self.mp_drawing = mp.solutions.drawing_utils

        self.prev_drag_point = None
        self.prev_zoom_distance = None
        self.prev_time = time.time()
        self.mouse_down = False

        self.cap = cv2.VideoCapture(camera_index)

    # Calculates the grip point from hand landmarks if fingers are close enough.
    def get_grip_point(self, hand_landmarks, frame_shape):
        h, w, _ = frame_shape
        thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        x1, y1 = int(thumb_tip.x * w), int(thumb_tip.y * h)
        x2, y2 = int(index_tip.x * w), int(index_tip.y * h)
        if math.hypot(x2 - x1, y2 - y1) < self.GRIP_THRESHOLD:
            return ((x1 + x2) // 2, (y1 + y2) // 2)
        return None

    # Processes drag movement and calculates the delta from the previous point.
    def process_drag(self, current_point, prev_point):
        if prev_point is None:
            return current_point, (0, 0)
        dx = int((current_point[0] - prev_point[0]) * self.DRAG_SMOOTHING)
        dy = int((current_point[1] - prev_point[1]) * self.DRAG_SMOOTHING)
        return current_point, (dx, dy)

    # Processes zoom action based on the distance between two grip points.
    def process_zoom(self, gp1, gp2, prev_distance):
        current_distance = math.hypot(gp2[0] - gp1[0], gp2[1] - gp1[1])
        zoom_action = None
        if prev_distance is not None:
            delta = current_distance - prev_distance
            if delta > self.ZOOM_SMOOTHING_DELTA:
                zoom_action = "Zooming out"
            elif delta < -self.ZOOM_SMOOTHING_DELTA:
                zoom_action = "Zooming in"
        return current_distance, zoom_action

    # Main loop: captures frames, processes hand gestures, and performs corresponding actions.
    def run(self):
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            current_time = time.time()
            fps = 1 / (current_time - self.prev_time)
            self.prev_time = current_time

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)

            grip_points = []
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    grip = self.get_grip_point(hand_landmarks, frame.shape)
                    if grip:
                        grip_points.append(grip)
                        cv2.circle(frame, grip, 8, (0, 0, 255), cv2.FILLED)
                    h, w, _ = frame.shape
                    thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
                    index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
                    x1, y1 = int(thumb_tip.x * w), int(thumb_tip.y * h)
                    x2, y2 = int(index_tip.x * w), int(index_tip.y * h)
                    cv2.circle(frame, (x1, y1), 5, (255, 0, 0), cv2.FILLED)
                    cv2.circle(frame, (x2, y2), 5, (255, 0, 0), cv2.FILLED)
                    cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            if len(grip_points) == 1:
                if not self.mouse_down:
                    pyautogui.mouseDown(button="right")
                    self.mouse_down = True
                current_point = grip_points[0]
                self.prev_drag_point, delta = self.process_drag(current_point, self.prev_drag_point)
                pyautogui.moveRel(delta[0], delta[1], duration=0)
                cv2.putText(frame, "Dragging Map", (10, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                self.prev_zoom_distance = None
            elif len(grip_points) == 2:
                if self.mouse_down:
                    pyautogui.mouseUp(button="right")
                    self.mouse_down = False
                gp1, gp2 = grip_points
                current_zoom_distance, zoom_action = self.process_zoom(gp1, gp2, self.prev_zoom_distance)
                if self.prev_zoom_distance is not None:
                    delta = current_zoom_distance - self.prev_zoom_distance
                    if abs(delta) > self.ZOOM_SMOOTHING_DELTA:
                        pyautogui.scroll(int(delta) * 3)
                self.prev_zoom_distance = current_zoom_distance
                text = zoom_action if zoom_action else "Pinch detected"
                cv2.putText(frame, text, (10, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                cv2.line(frame, gp1, gp2, (0, 255, 255), 2)
                self.prev_drag_point = None
            else:
                if self.mouse_down:
                    pyautogui.mouseUp(button="right")
                    self.mouse_down = False
                self.prev_drag_point = None
                self.prev_zoom_distance = None

            cv2.putText(frame, f"FPS: {int(fps)}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
            cv2.imshow("Demo", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    controller = HandGestureController()
    controller.run()