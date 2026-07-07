import urllib.request
import os

url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
filename = "hand_landmarker.task"

print(f"Downloading {filename} from {url}...")
try:
    urllib.request.urlretrieve(url, filename)
    if os.path.exists(filename):
        print(f"Success! File size: {os.path.getsize(filename)} bytes")
    else:
        print("Error: File not found after download.")
except Exception as e:
    print(f"Error downloading: {e}")
