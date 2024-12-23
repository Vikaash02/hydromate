import cv2
import requests

ESP32_CAM_URL = "http://<ESP32-CAM-IP>/stream"  # Replace with the ESP32-CAM IP
NODE_RED_URL = "http://localhost:1880/video_feed"  # Node-RED endpoint

def forward_stream():
    # Capture stream from ESP32-CAM
    cap = cv2.VideoCapture(ESP32_CAM_URL)
    if not cap.isOpened():
        print("Error: Cannot connect to ESP32-CAM stream.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to read frame.")
            break

        # Encode frame as JPEG
        _, buffer = cv2.imencode(".jpg", frame)

        # Forward frame to Node-RED
        try:
            requests.post(NODE_RED_URL, data=buffer.tobytes(), headers={"Content-Type": "image/jpeg"})
        except Exception as e:
            print(f"Error sending frame: {e}")

if __name__ == "__main__":
    forward_stream()
