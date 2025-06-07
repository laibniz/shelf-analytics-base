from datetime import datetime
from tempfile import NamedTemporaryFile
import base64
import os
import io
from typing import Dict, List
from PIL import Image
import logging

from fastapi import FastAPI, UploadFile, File, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from src.product_detector import ProductDetector
from src.product_clusterer import ProductClusterer

DATABASE_URL = "sqlite:///./clusters.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ClusterLabel(Base):
    __tablename__ = "cluster_labels"
    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(String, unique=True, index=True)
    label = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI()

# Allow the React frontend to make cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

detector = ProductDetector()
clusterer = ProductClusterer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/log")
async def log_message(message: Dict[str, str]):
    text = message.get("message", "")
    logger.info("CLIENT LOG: %s", text)
    return {"status": "logged"}

@app.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    clusters: int = Query(10, description="Number of clusters")
):
    logger.info("Received upload: %s with %d clusters", file.filename, clusters)

    with NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    logger.debug("Temporary file saved at %s", tmp_path)
    try:
        detections = detector.detect_products(tmp_path)
        os.remove(tmp_path)
        logger.debug("Detections: %s", len(detections))
        clustered = clusterer.cluster(detections, n_clusters=clusters)
        logger.debug("Clusters formed: %s", len(clustered))

        with open(tmp_path, "rb") as f:
            original_bytes = f.read()
        original_image = Image.open(io.BytesIO(original_bytes))
        width, height = original_image.size
        original_encoded = base64.b64encode(original_bytes).decode("utf-8")
        original_image.close()

        response_clusters: List[Dict] = []
        detection_data: List[Dict] = []
        for cid, info in clustered.items():
            items = info["items"]
            rep_idx = info["representative_index"]

            rep_buf = io.BytesIO()
            items[rep_idx]["image"].save(rep_buf, format="JPEG")
            rep_encoded = base64.b64encode(rep_buf.getvalue()).decode("utf-8")
            response_clusters.append({"cluster_id": cid, "image": rep_encoded})

            for item in items:
                detection_data.append({
                    "cluster_id": cid,
                    "bbox": item["bbox"],
                })

        return {
            "image": original_encoded,
            "width": width,
            "height": height,
            "clusters": response_clusters,
            "detections": detection_data,
        }
    except Exception as exc:
        logger.exception("Error processing image: %s", exc)
        return {'error': 'processing failed'}

@app.post("/save-labels")
async def save_labels(labels: Dict[str, str], db: Session = Depends(get_db)):
    logger.info("Saving %d labels", len(labels))
    for cluster_id, label in labels.items():
        item = db.query(ClusterLabel).filter_by(cluster_id=str(cluster_id)).first()
        if item:
            item.label = label
        else:
            item = ClusterLabel(cluster_id=str(cluster_id), label=label)
            db.add(item)
    db.commit()
    return {'status': 'ok'}

@app.get("/clusters")
def list_clusters(db: Session = Depends(get_db)):
    items = db.query(ClusterLabel).all()
    logger.debug("Listing %d clusters", len(items))
    return [
        {
            'cluster_id': item.cluster_id,
            'label': item.label,
            'created_at': item.created_at.isoformat()
        } for item in items
    ]
