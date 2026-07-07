import platform


if platform.system() == "Darwin":
    from window_manager_macos import WindowManager
elif platform.system() == "Windows":
    from window_manager_windows import WindowManager
else:
    raise RuntimeError(f"Unsupported platform for window control: {platform.system()}")
