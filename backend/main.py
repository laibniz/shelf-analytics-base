from datetime import datetime
from tempfile import NamedTemporaryFile
import base64
import os
import io
from typing import Dict, List
import logging

from fastapi import FastAPI, UploadFile, File, Depends
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
async def upload_image(file: UploadFile = File(...)):
    logger.info("Received upload: %s", file.filename)

    with NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    logger.debug("Temporary file saved at %s", tmp_path)
    try:
        detections = detector.detect_products(tmp_path)
        os.remove(tmp_path)
        logger.debug("Detections: %s", len(detections))
        clusters = clusterer.cluster(detections)
        logger.debug("Clusters formed: %s", len(clusters))
        response: List[Dict] = []
        for cluster_id, items in clusters.items():
            for item in items:
                buf = io.BytesIO()
                item['image'].save(buf, format='JPEG')
                encoded = base64.b64encode(buf.getvalue()).decode('utf-8')
                response.append({
                    'cluster_id': cluster_id,
                    'image': encoded
                })
        return {'products': response}
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
