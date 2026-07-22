from ultralytics import YOLO

model = YOLO("yolov8n.pt")

# track() instead of predict() - assigns a persistent ID to each person
results = model.track(
    source=0,
    classes=[0],
    persist=True,
    show=True,
    conf=0.4,
    tracker="bytetrack.yaml"
)