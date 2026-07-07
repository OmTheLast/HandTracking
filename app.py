import time

from flask import Flask, Response, render_template, jsonify, request
from main import controller

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/cameras')
def get_cameras():
    cameras = controller.get_available_cameras()
    return jsonify({'cameras': cameras})

@app.route('/api/start', methods=['POST'])
def start_tracking():
    data = request.json or {}
    camera_idx = int(data.get('camera_index') or 0)
    
    if not controller.start(camera_index=camera_idx):
        return jsonify({'status': 'error', 'message': 'Already running'}), 400
    
    return jsonify({'status': 'started', 'camera_index': camera_idx})

@app.route('/api/stop', methods=['POST'])
def stop_tracking():
    controller.stop()
    return jsonify({'status': 'stopped'})

@app.route('/api/target', methods=['POST'])
def capture_target():
    ok, error = controller.capture_target_window()
    if not ok:
        return jsonify({'status': 'error', 'message': error}), 403
    return jsonify({'status': 'targeted', 'target': controller.get_status().get('target')})

@app.route('/api/target', methods=['DELETE'])
def clear_target():
    controller.clear_target_window()
    return jsonify({'status': 'cleared'})

@app.route('/api/status')
def get_status():
    return jsonify(controller.get_status())

@app.route('/video_feed')
def video_feed():
    def generate():
        while True:
            frame = controller.get_latest_frame()
            if frame is None:
                time.sleep(0.05)
                continue

            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
            )
            time.sleep(0.03)

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False) # use_reloader=False prevents double-loading which messes up threads
