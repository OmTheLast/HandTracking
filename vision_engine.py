import cv2
import mediapipe as mp
import numpy as np
import time
import os

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

class HandTracker:
    def __init__(self, mode=False, max_hands=1, detection_con=0.5, track_con=0.5):
        # Note: New API doesn't map 1:1 to old params, but we adapt key ones.
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hand_landmarker.task')
        
        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=VisionRunningMode.VIDEO,
            num_hands=max_hands,
            min_hand_detection_confidence=detection_con,
            min_hand_presence_confidence=track_con,
            min_tracking_confidence=track_con
        )
        self.landmarker = HandLandmarker.create_from_options(options)
        self.timestamp_ms = 0

    def process(self, frame):
        # Convert to RGB
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
        
        # Timestamp needed for VIDEO mode
        self.timestamp_ms = int(time.time() * 1000)
        
        # Detect
        self.results = self.landmarker.detect_for_video(mp_image, self.timestamp_ms)
        return self.results

    def draw_landmarks(self, frame):
        # Custom drawer since we lost mp.solutions.drawing_utils support in this context easily
        # or we have to manually map it. Let's do a simple manual draw for now to avoid dependency hell.
        if self.results and self.results.hand_landmarks:
            h, w, c = frame.shape
            for hand_lms in self.results.hand_landmarks:
                # Draw points
                for lm in hand_lms:
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    cv2.circle(frame, (cx, cy), 5, (255, 0, 255), cv2.FILLED)
                
                # Draw connections (simple version, wrist to fingertips)
                # We can add full skeleton later if needed.
        return frame
