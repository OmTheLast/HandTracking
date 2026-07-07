import math

class GestureRecognizer:
    def __init__(self):
        self.pinch_on_threshold = 0.075
        self.pinch_off_threshold = 0.105
        self.last_gesture = 'NONE'

    def calculate_distance(self, p1, p2):
        return math.hypot(p2.x - p1.x, p2.y - p1.y)

    def classify(self, landmarks):
        """
        Classifies the gesture based on landmarks.
        Returns: 'PINCH', 'OPEN_PALM', 'NONE'
        """
        if not landmarks:
            return 'NONE'
        
        # Landmarks for thumb tip (4) and index tip (8)
        thumb_tip = landmarks.landmark[4]
        index_tip = landmarks.landmark[8]

        # Calculate distance
        distance = self.calculate_distance(thumb_tip, index_tip)

        # Coordinates are normalized [0, 1]. Separate on/off thresholds reduce flicker.
        is_pinching = distance < self.pinch_on_threshold
        if self.last_gesture == 'PINCH':
            is_pinching = distance < self.pinch_off_threshold

        if is_pinching:
            self.last_gesture = 'PINCH'
            return 'PINCH', (thumb_tip.x + index_tip.x) / 2, (thumb_tip.y + index_tip.y) / 2

        self.last_gesture = 'OPEN_PALM'
        return 'OPEN_PALM', thumb_tip.x, thumb_tip.y
