import win32gui
import win32api
import win32con


class WindowManager:
    def __init__(self):
        self.grabbed_window = None
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.last_speed = 0
        self.last_gain = 1

    def get_screen_size(self):
        return (
            win32api.GetSystemMetrics(win32con.SM_CXSCREEN),
            win32api.GetSystemMetrics(win32con.SM_CYSCREEN),
        )

    def get_window_at_point(self, x, y):
        """
        Returns the HWND of the window at the screen coordinates (x, y).
        """
        return win32gui.WindowFromPoint((x, y))

    def start_drag(self, x, y):
        """
        Called when a pinch starts. Finds the window and prepares for dragging.
        """
        hwnd = self.get_window_at_point(x, y)
        if hwnd:
            # Check if it's a valid window (not desktop or specialized system window if needed)
            # For now, just grab whatever is there.
            self.grabbed_window = hwnd
            self.last_mouse_x = x
            self.last_mouse_y = y
            print(f"Grabbed window: {win32gui.GetWindowText(hwnd)}")
        return self.grabbed_window

    def update_drag(self, x, y):
        """
        Called while pinching to move the window.
        """
        if self.grabbed_window:
            dx = x - self.last_mouse_x
            dy = y - self.last_mouse_y

            try:
                # Get current window position
                rect = win32gui.GetWindowRect(self.grabbed_window)
                current_x = rect[0]
                current_y = rect[1]
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]

                # Move window
                win32gui.MoveWindow(self.grabbed_window, current_x + dx, current_y + dy, width, height, True)

                self.last_mouse_x = x
                self.last_mouse_y = y
            except Exception as e:
                print(f"Error moving window: {e}")
                self.end_drag()

    def end_drag(self):
        """
        Called when pinch is released.
        """
        self.grabbed_window = None
        print("Released window")
