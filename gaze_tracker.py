"""
Webcam-based eye/gaze tracker using MediaPipe Face Mesh iris landmarks.
Falls back to mouse cursor tracking if no webcam is available.
"""
import threading
import time

import cv2
import numpy as np


class GazeTracker:
    # MediaPipe iris landmark indices (requires refine_landmarks=True)
    LEFT_IRIS = [474, 475, 476, 477]
    RIGHT_IRIS = [469, 470, 471, 472]

    def __init__(self):
        self.gaze_x = 0
        self.gaze_y = 0
        self.running = False
        self.callback = None
        self.mode = "eye"          # "eye" or "mouse"
        self.available = False
        self._smooth_x = 0.0
        self._smooth_y = 0.0
        self._screen_w = 1920
        self._screen_h = 1080
        self._cap = None
        self._face_mesh = None

    def initialize(self, screen_w: int, screen_h: int) -> bool:
        self._screen_w = screen_w
        self._screen_h = screen_h
        self._smooth_x = screen_w / 2
        self._smooth_y = screen_h / 2
        self.gaze_x = screen_w // 2
        self.gaze_y = screen_h // 2

        try:
            import mediapipe as mp
            self._cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self._cap.isOpened():
                raise RuntimeError("No webcam found")
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self._cap.set(cv2.CAP_PROP_FPS, 30)
            self._face_mesh = mp.solutions.face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self.available = True
            self.mode = "eye"
        except Exception:
            self.available = False
            self.mode = "mouse"

        return self.available

    def start(self, callback):
        self.callback = callback
        self.running = True
        if self.mode == "eye":
            t = threading.Thread(target=self._eye_loop, daemon=True)
        else:
            t = threading.Thread(target=self._mouse_loop, daemon=True)
        t.start()
        return self.mode

    def stop(self):
        self.running = False
        if self._cap:
            self._cap.release()

    def _iris_center(self, landmarks, indices, w, h):
        xs = [landmarks[i].x * w for i in indices]
        ys = [landmarks[i].y * h for i in indices]
        return sum(xs) / len(xs), sum(ys) / len(ys)

    def _eye_loop(self):
        alpha = 0.20  # smoothing factor (lower = smoother but laggier)

        # These ranges define how much the iris moves within the webcam frame.
        # Tuned empirically; adjust if tracking feels off.
        X_MIN, X_MAX = 0.38, 0.62
        Y_MIN, Y_MAX = 0.33, 0.60

        while self.running:
            ret, frame = self._cap.read()
            if not ret:
                time.sleep(0.05)
                continue

            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self._face_mesh.process(rgb)

            if results.multi_face_landmarks:
                lm = results.multi_face_landmarks[0].landmark

                lx, ly = self._iris_center(lm, self.LEFT_IRIS, w, h)
                rx, ry = self._iris_center(lm, self.RIGHT_IRIS, w, h)

                norm_x = (lx + rx) / (2 * w)
                norm_y = (ly + ry) / (2 * h)

                # Webcam is mirrored — flip x
                norm_x = 1.0 - norm_x

                sx = np.clip((norm_x - X_MIN) / (X_MAX - X_MIN), 0, 1) * self._screen_w
                sy = np.clip((norm_y - Y_MIN) / (Y_MAX - Y_MIN), 0, 1) * self._screen_h

                self._smooth_x = self._smooth_x * (1 - alpha) + sx * alpha
                self._smooth_y = self._smooth_y * (1 - alpha) + sy * alpha

                self.gaze_x = int(self._smooth_x)
                self.gaze_y = int(self._smooth_y)

                if self.callback:
                    self.callback(self.gaze_x, self.gaze_y)

            time.sleep(0.033)  # ~30 fps

    def _mouse_loop(self):
        """Fallback: track mouse cursor position when no webcam is available."""
        import ctypes

        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

        while self.running:
            pt = POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            self.gaze_x = pt.x
            self.gaze_y = pt.y
            if self.callback:
                self.callback(pt.x, pt.y)
            time.sleep(0.05)
