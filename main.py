import cv2
import threading
import time
from vision_engine import HandTracker
from gesture_lib import GestureRecognizer
from window_manager import WindowManager

class GestureController:
    def __init__(self):
        self.is_running = False
        self.thread = None
        self.camera_index = 0
        self.lock = threading.Lock()
        self.frame_lock = threading.Lock()
        self.latest_frame = None
        self.win_manager = WindowManager()
        self.gesture_state = {
            "gesture": "NONE",
            "screen_x": None,
            "screen_y": None,
            "camera_x": None,
            "camera_y": None,
            "grabbed": False,
            "speed": 0,
            "gain": 1,
            "target": None,
            "error": None,
        }

    def get_available_cameras(self):
        """
        Checks the first 5 indexes. Returns a list of available camera IDs.
        """
        available = []
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                cap.release()
        return available

    def start(self, camera_index=0):
        with self.lock:
            if self.is_running:
                return False # Already running
            
            self.camera_index = camera_index
            self.is_running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            return True

    def stop(self):
        with self.lock:
            self.is_running = False
        if self.thread:
            self.thread.join()
            self.thread = None

    def get_latest_frame(self):
        with self.frame_lock:
            return self.latest_frame

    def get_status(self):
        with self.lock:
            is_running = self.is_running
            gesture_state = dict(self.gesture_state)
        return {"is_running": is_running, **gesture_state}

    def _set_gesture_state(
        self,
        gesture="NONE",
        screen_x=None,
        screen_y=None,
        camera_x=None,
        camera_y=None,
        grabbed=False,
        speed=0,
        gain=1,
        target=None,
        error=None,
    ):
        with self.lock:
            target_title = target
            if target_title is None and hasattr(self.win_manager, "target_title"):
                target_title = self.win_manager.target_title
            self.gesture_state = {
                "gesture": gesture,
                "screen_x": screen_x,
                "screen_y": screen_y,
                "camera_x": camera_x,
                "camera_y": camera_y,
                "grabbed": grabbed,
                "speed": speed,
                "gain": gain,
                "target": target_title,
                "error": error,
            }

    def capture_target_window(self):
        if not hasattr(self.win_manager, "capture_active_window"):
            return False, "Target window selection is not available on this platform"

        ok = self.win_manager.capture_active_window()
        error = None if ok else self.win_manager.last_error
        self._set_gesture_state(target=self.win_manager.target_title, error=error)
        return ok, error

    def clear_target_window(self):
        if hasattr(self.win_manager, "clear_target_window"):
            self.win_manager.clear_target_window()
        self._set_gesture_state()

    def _store_frame(self, frame):
        success, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if success:
            with self.frame_lock:
                self.latest_frame = buffer.tobytes()

    def _run_loop(self):
        cap = None
        try:
            tracker = HandTracker(detection_con=0.7)
            gesture_rec = GestureRecognizer()
            win_manager = self.win_manager
            screen_width, screen_height = win_manager.get_screen_size()

            cap = cv2.VideoCapture(self.camera_index)
            if not cap.isOpened():
                print(f"Could not open camera {self.camera_index}")
                self._set_gesture_state(error=f"Could not open camera {self.camera_index}")
                return
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)
            cap.set(cv2.CAP_PROP_FPS, 30)

            print(f"Starting tracking on camera {self.camera_index}...")

            while True:
                with self.lock:
                    if not self.is_running:
                        break

                success, frame = cap.read()
                if not success:
                    time.sleep(0.1)
                    continue

                frame = cv2.flip(frame, 1)
                frame_height, frame_width = frame.shape[:2]

                results = tracker.process(frame)
                tracker.draw_landmarks(frame)

                if results and results.hand_landmarks:
                    landmarks = results.hand_landmarks[0]

                    class LandmarkWrapper:
                        def __init__(self, lms):
                            self.landmark = lms

                    gesture_result = gesture_rec.classify(LandmarkWrapper(landmarks))
                    gesture_type = gesture_result[0]

                    if gesture_type != 'NONE':
                        norm_x, norm_y = gesture_result[1], gesture_result[2]
                        screen_x = int(norm_x * screen_width)
                        screen_y = int(norm_y * screen_height)
                        camera_x = int(norm_x * frame_width)
                        camera_y = int(norm_y * frame_height)

                        cv2.putText(frame, f"{gesture_type}", (10, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0,255,0), 3)
                        cv2.putText(
                            frame,
                            f"screen: {screen_x}, {screen_y}",
                            (10, 85),
                            cv2.FONT_HERSHEY_PLAIN,
                            1.4,
                            (0, 255, 0),
                            2,
                        )
                        cv2.putText(
                            frame,
                            f"speed: {int(win_manager.last_speed)} gain: {win_manager.last_gain}",
                            (10, 120),
                            cv2.FONT_HERSHEY_PLAIN,
                            1.4,
                            (0, 255, 0),
                            2,
                        )
                        cv2.circle(frame, (camera_x, camera_y), 10, (0, 255, 255), 2)
                        cv2.line(frame, (camera_x - 16, camera_y), (camera_x + 16, camera_y), (0, 255, 255), 2)
                        cv2.line(frame, (camera_x, camera_y - 16), (camera_x, camera_y + 16), (0, 255, 255), 2)

                        if gesture_type == 'PINCH':
                            if not win_manager.grabbed_window:
                                win_manager.start_drag(screen_x, screen_y)
                            else:
                                win_manager.update_drag(screen_x, screen_y)
                        elif gesture_type == 'OPEN_PALM' and win_manager.grabbed_window:
                            win_manager.end_drag()

                        self._set_gesture_state(
                            gesture_type,
                            screen_x,
                            screen_y,
                            camera_x,
                            camera_y,
                            bool(win_manager.grabbed_window),
                            int(win_manager.last_speed),
                            win_manager.last_gain,
                            getattr(win_manager, "target_title", None),
                            getattr(win_manager, "last_error", None),
                        )
                elif win_manager.grabbed_window:
                    win_manager.end_drag()
                    self._set_gesture_state()
                else:
                    self._set_gesture_state()

                self._store_frame(frame)
        except Exception as e:
            print(f"Tracking error: {e}")
            self._set_gesture_state(error=str(e))
        finally:
            if cap is not None:
                cap.release()
            with self.lock:
                self.is_running = False
            self._set_gesture_state()
            print("Tracking stopped.")

# Global instance for app to use
controller = GestureController()

if __name__ == "__main__":
    # Test run
    print("Available cameras:", controller.get_available_cameras())
    controller.start(0)
    try:
        while True:
            time.sleep(1)
            if not controller.is_running:
                break
    except KeyboardInterrupt:
        controller.stop()
