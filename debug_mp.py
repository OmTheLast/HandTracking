import sys
print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")

try:
    import mediapipe
    print(f"MediaPipe File: {mediapipe.__file__}")
    print(f"MediaPipe Dir: {dir(mediapipe)}")
    
    try:
        from mediapipe.python import solutions
        print("SUCCESS: Import via 'from mediapipe.python import solutions' worked.")
    except ImportError as e:
        print(f"FAIL: Deep import failed: {e}")

except ImportError as e:
    print(f"FAIL: generic import failed: {e}")
except Exception as e:
    print(f"ERROR: {e}")
