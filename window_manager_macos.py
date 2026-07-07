import math
import time

from AppKit import NSWorkspace, NSScreen
from ApplicationServices import (
    AXIsProcessTrustedWithOptions,
    AXUIElementCopyAttributeValue,
    AXUIElementCopyElementAtPosition,
    AXUIElementCreateApplication,
    AXUIElementCreateSystemWide,
    AXUIElementIsAttributeSettable,
    AXUIElementSetAttributeValue,
    AXValueCreate,
    AXValueGetValue,
    kAXFocusedWindowAttribute,
    kAXMainWindowAttribute,
    kAXParentAttribute,
    kAXPositionAttribute,
    kAXRoleAttribute,
    kAXTitleAttribute,
    kAXTrustedCheckOptionPrompt,
    kAXValueCGPointType,
    kAXWindowRole,
    kAXWindowsAttribute,
)


class WindowManager:
    def __init__(self):
        self.grabbed_window = None
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.filtered_mouse_x = None
        self.filtered_mouse_y = None
        self.residual_dx = 0
        self.residual_dy = 0
        self.last_drag_time = None
        self.velocity_x = 0
        self.velocity_y = 0
        self.last_speed = 0
        self.last_gain = 1
        self.deadzone_px = 8
        self.smoothing_alpha = 0.32
        self.max_step_px = 160
        self.min_move_interval = 1 / 60
        self.target_window = None
        self.target_title = None
        self.last_error = None
        self._system_wide = AXUIElementCreateSystemWide()
        self._ensure_accessibility_permission()

    def _ensure_accessibility_permission(self):
        trusted = AXIsProcessTrustedWithOptions({kAXTrustedCheckOptionPrompt: True})
        if not trusted:
            print(
                "macOS Accessibility permission is required. "
                "Open System Settings > Privacy & Security > Accessibility "
                "and allow your terminal or Python app."
            )

    def get_screen_size(self):
        frame = NSScreen.mainScreen().frame()
        return int(frame.size.width), int(frame.size.height)

    def _copy_attribute(self, element, attribute):
        error, value = AXUIElementCopyAttributeValue(element, attribute, None)
        if error == 0:
            return value
        return None

    def _is_position_settable(self, window):
        error, settable = AXUIElementIsAttributeSettable(window, kAXPositionAttribute, None)
        return error == 0 and bool(settable)

    def _window_title(self, window):
        return self._copy_attribute(window, kAXTitleAttribute) or "active macOS window"

    def _find_window_element(self, element):
        current = element
        for _ in range(8):
            role = self._copy_attribute(current, kAXRoleAttribute)
            if role == kAXWindowRole:
                return current
            parent = self._copy_attribute(current, kAXParentAttribute)
            if parent is None:
                break
            current = parent
        return element

    def get_window_at_point(self, x, y):
        """
        Returns the macOS Accessibility window element at screen coordinates.
        """
        error, element = AXUIElementCopyElementAtPosition(self._system_wide, float(x), float(y), None)
        if error != 0 or element is None:
            return None
        return self._find_window_element(element)

    def get_active_window(self):
        """
        Returns the focused window from the frontmost macOS application.
        """
        app = NSWorkspace.sharedWorkspace().frontmostApplication()
        if app is None:
            return None

        ax_app = AXUIElementCreateApplication(app.processIdentifier())
        for attribute in (kAXFocusedWindowAttribute, kAXMainWindowAttribute):
            window = self._copy_attribute(ax_app, attribute)
            if window is not None:
                return window

        windows = self._copy_attribute(ax_app, kAXWindowsAttribute)
        if windows:
            return windows[0]
        return None

    def capture_active_window(self):
        window = self.get_active_window()
        if not window:
            self.last_error = "No active window found"
            return False

        title = self._window_title(window)
        if not self._is_position_settable(window):
            self.last_error = f"Access denied for '{title}'. Choose a normal movable app window."
            return False

        self.target_window = window
        self.target_title = title
        self.last_error = None
        print(f"Target window: {title}")
        return True

    def clear_target_window(self):
        self.target_window = None
        self.target_title = None
        self.last_error = None
        self.end_drag()

    def start_drag(self, x, y):
        """
        Called when a pinch starts. Grabs the active window and prepares for dragging.
        """
        window = self.target_window or self.get_active_window()
        if window:
            if not self._is_position_settable(window):
                title = self._window_title(window)
                self.last_error = f"Access denied for '{title}'. Choose a normal movable app window."
                return None

            self.grabbed_window = window
            self.last_mouse_x = x
            self.last_mouse_y = y
            self.filtered_mouse_x = float(x)
            self.filtered_mouse_y = float(y)
            self.residual_dx = 0
            self.residual_dy = 0
            self.last_drag_time = time.monotonic()
            self.velocity_x = 0
            self.velocity_y = 0
            self.last_speed = 0
            self.last_gain = 1
            title = self.target_title or self._window_title(window)
            self.last_error = None
            print(f"Grabbed {title}")
        return self.grabbed_window

    def update_drag(self, x, y):
        """
        Called while pinching to move the window.
        """
        if not self.grabbed_window:
            return

        now = time.monotonic()
        dt = max(now - self.last_drag_time, 1 / 120) if self.last_drag_time else 1 / 60
        if dt < self.min_move_interval:
            return

        raw_dx = x - self.last_mouse_x
        raw_dy = y - self.last_mouse_y
        raw_distance = math.hypot(raw_dx, raw_dy)
        if raw_distance < self.deadzone_px:
            self.last_drag_time = now
            return

        if self.filtered_mouse_x is None or self.filtered_mouse_y is None:
            self.filtered_mouse_x = float(self.last_mouse_x)
            self.filtered_mouse_y = float(self.last_mouse_y)

        self.filtered_mouse_x += (x - self.filtered_mouse_x) * self.smoothing_alpha
        self.filtered_mouse_y += (y - self.filtered_mouse_y) * self.smoothing_alpha

        dx = self.filtered_mouse_x - self.last_mouse_x
        dy = self.filtered_mouse_y - self.last_mouse_y
        distance = math.hypot(dx, dy)
        if distance < self.deadzone_px:
            self.last_drag_time = now
            return

        deadzone_scale = (distance - self.deadzone_px) / distance
        dx *= deadzone_scale
        dy *= deadzone_scale

        raw_velocity_x = dx / dt
        raw_velocity_y = dy / dt
        self.velocity_x = (self.velocity_x * 0.65) + (raw_velocity_x * 0.35)
        self.velocity_y = (self.velocity_y * 0.65) + (raw_velocity_y * 0.35)
        speed = math.hypot(self.velocity_x, self.velocity_y)
        gain = 1.0 if speed < 850 else min(3.8, 1.0 + ((speed - 850) / 900))

        move_dx = max(-self.max_step_px, min(self.max_step_px, (dx * gain) + self.residual_dx))
        move_dy = max(-self.max_step_px, min(self.max_step_px, (dy * gain) + self.residual_dy))
        int_move_dx = int(round(move_dx))
        int_move_dy = int(round(move_dy))
        self.residual_dx = move_dx - int_move_dx
        self.residual_dy = move_dy - int_move_dy

        if int_move_dx == 0 and int_move_dy == 0:
            self.last_drag_time = now
            return

        try:
            position_value = self._copy_attribute(self.grabbed_window, kAXPositionAttribute)
            if position_value is None:
                self.end_drag()
                return

            success, current_position = AXValueGetValue(position_value, kAXValueCGPointType, None)
            if not success:
                self.end_drag()
                return

            new_position = AXValueCreate(
                kAXValueCGPointType,
                (current_position.x + int_move_dx, current_position.y + int_move_dy),
            )
            error = AXUIElementSetAttributeValue(self.grabbed_window, kAXPositionAttribute, new_position)
            if error != 0:
                self.last_error = f"Access denied while moving window (AX error {error})"
                print(self.last_error)
                self.end_drag()
                return

            self.last_mouse_x = self.filtered_mouse_x
            self.last_mouse_y = self.filtered_mouse_y
            self.last_drag_time = now
            self.last_speed = int(speed)
            self.last_gain = round(gain, 2)
        except Exception as e:
            self.last_error = f"Error moving macOS window: {e}"
            print(self.last_error)
            self.end_drag()

    def end_drag(self):
        """
        Called when pinch is released.
        """
        self.grabbed_window = None
        self.filtered_mouse_x = None
        self.filtered_mouse_y = None
        self.residual_dx = 0
        self.residual_dy = 0
        self.last_drag_time = None
        self.velocity_x = 0
        self.velocity_y = 0
        self.last_speed = 0
        self.last_gain = 1
        print("Released window")
