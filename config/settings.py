"""Phase 1 configuration — edit line coordinates to match your camera view."""

from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "retailvision.db"

# Camera (USB webcam index; 0 = default device)
CAMERA_INDEX = 0
CAMERA_NAME = "Default Webcam"
CAMERA_SOURCE_TYPE = "usb"
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30

# Virtual counting line — two pixel coordinates on the frame (FR-005).
# Adjust after seeing the live preview; defaults assume 640x480.
LINE_POINT_1 = (40, 240)
LINE_POINT_2 = (250, 240)

# Which crossing direction counts as ENTRY (FR-005):
#   "negative_to_positive" — person moves from the right side of the directed
#       line (p1→p2) to the left side.
#   "positive_to_negative" — person moves from left to right.
ENTRY_DIRECTION = "negative_to_positive"

# AI inference (CPU-only, Standard Tier targets 15–20 FPS)
MODEL_NAME = "yolov8n.pt"
CONFIDENCE_THRESHOLD = 0.4
INFERENCE_SIZE = 640
DEVICE = "cpu"
TRACKER_CONFIG = "bytetrack.yaml"

# Person class in COCO (FR-003)
PERSON_CLASS_ID = 0
