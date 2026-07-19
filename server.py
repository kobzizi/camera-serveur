from flask import Flask, Response, render_template_string, request
import cv2
import numpy as np
import time
from threading import Lock

app = Flask(__name__)

latest_frame = None
lock = Lock()

# Page web
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Flux Caméra</title>
    <style>
        body { 
            background: black; 
            color: white; 
            text-align: center; 
            font-family: Arial, sans-serif; 
            margin: 0;
            padding: 20px;
        }
        img { 
            width: 100%; 
            max-width: 900px; 
            border: 2px solid #333;
        }
        h1 { margin-bottom: 10px; }
    </style>
</head>
<body>
    <h1>Flux en direct</h1>
    <img src="/video_feed" />
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

# Route qui reçoit les images du client
@app.route('/stream', methods=['POST'])
def receive_stream():
    global latest_frame
    try:
        data = request.get_data()
        img_array = np.frombuffer(data, dtype=np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if frame is not None:
            with lock:
                latest_frame = frame.copy()
    except:
        pass
    return "OK", 200

# Génère le flux vidéo
def gen_frames():
    global latest_frame
    while True:
        with lock:
            if latest_frame is not None:
                frame_to_send = latest_frame.copy()
            else:
                # Image noire en attendant le flux
                frame_to_send = np.zeros((480, 640, 3), dtype=np.uint8)
        
        ret, buffer = cv2.imencode('.jpg', frame_to_send)
        if ret:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        time.sleep(0.05)

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print("🚀 Serveur démarré sur Render")
    app.run(host='0.0.0.0', port=5000, debug=False)
