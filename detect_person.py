from ultralytics import YOLO

# Load the nano model (auto-downloads the first time you run this)
model = YOLO("yolov8n.pt")

# Run detection on your webcam, only looking for "person" (class 0)
results = model.predict(source=0, classes=[0], show=True, conf=0.4)