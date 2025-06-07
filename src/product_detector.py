from typing import List, Dict
from PIL import Image
from ultralytics import YOLO

class ProductDetector:
    """Detect products on a retail shelf using YOLOv8."""

    def __init__(self, model_path: str = "models/best.pt", conf: float = 0.5):
        self.model = YOLO(model_path)
        self.conf = conf

    def detect_products(self, image_path: str) -> List[Dict]:
        """Detect products and return their bounding boxes and cropped images."""
        results = self.model.predict(source=image_path, conf=self.conf, save=False)
        detections: List[Dict] = []
        original = Image.open(image_path)
        for r in results:
            if not hasattr(r, "boxes"):
                continue
            for box in r.boxes.xyxy.cpu().numpy():
                x1, y1, x2, y2 = [int(v) for v in box[:4]]
                crop = original.crop((x1, y1, x2, y2))
                detections.append({
                    "bbox": [x1, y1, x2, y2],
                    "image": crop
                })
        original.close()
        return detections
