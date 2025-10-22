from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil, os, logging
from logging.handlers import RotatingFileHandler

# Always resolve to the project root: backend/main.py → parents[1] == project root
BASE_DIR = Path(__file__).resolve().parents[1]
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

file_handler = RotatingFileHandler(
    LOGS_DIR / "app.log",
    maxBytes=5_000_000,
    backupCount=3,
    encoding="utf-8",
)
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s", "%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Configure *your* app logger explicitly; don't rely on basicConfig
smart_logger = logging.getLogger("smartdoc")
smart_logger.setLevel(logging.INFO)
# Avoid duplicate handlers if uvicorn reloads
smart_logger.handlers.clear()
smart_logger.addHandler(file_handler)
smart_logger.addHandler(console_handler)
smart_logger.propagate = False

smart_logger.info("SmartDoc logger configured. Logs dir: %s", LOGS_DIR)
# ---- end logging setup ----

# load config from project root (your current setup)
from config import settings

app = FastAPI(title="SmartDoc API")
api_log = logging.getLogger("smartdoc")

# CORS (same as you had)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- delayed imports to avoid circular/import-path surprises ----
# DB wiring
from backend.db.database import get_db, engine
from backend.db import models as db_models
from backend.db import crud, schemas

# Processing pipeline
from backend.pipeline.document_processor import DocumentProcessor
from backend.pipeline.cv_processor import CVProcessor
from fastapi import Query
from typing import List

# ----------------------------------------------------------------

logger = logging.getLogger(__name__)
processor = DocumentProcessor()
cv_processor = CVProcessor()

# Dev convenience: create tables once (use Alembic later in prod)
db_models.Base.metadata.create_all(bind=engine)


@app.get("/health")
async def health_check():
    api_log.info("Health check ping")
    return {"status": "healthy"}


@app.get("/documents")
def list_documents(limit: int = Query(20, ge=1, le=100), db=Depends(get_db)):
    return crud.list_documents(db, limit=limit)


@app.get("/documents/{doc_id}", response_model=schemas.ProcessResponse)
def get_document(doc_id: str, db=Depends(get_db)):
    doc = crud.get_document(db, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    res = crud.get_latest_result(db, doc_id)
    if not res:
        raise HTTPException(404, "No results for this document")
    return {"document": doc, "latest_result": res}


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Simple raw upload (no DB). Keeps your existing endpoint."""
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"filename": file.filename, "message": "File uploaded successfully"}


@app.post("/process", response_model=schemas.ProcessResponse)
async def process_document(file: UploadFile = File(...), db=Depends(get_db)):
    """
    Full pipeline:
      1) Save upload to disk
      2) Create Document row
      3) Run OCR + LLM
      4) Persist Result row
      5) Return (document, latest_result)
    """
    api_log.info("Received /process request")
    # 1) Save upload
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    # use a subdir per document id? (DB will generate id—so save temp first)
    temp_path = upload_dir / file.filename
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    size = os.path.getsize(temp_path)

    # 2) Create Document row (DB will assign id)
    doc = crud.create_document(
        db,
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        size=size,
        stored_path=str(temp_path),  # for dev/local only
    )

    # Optionally move file into a folder named after doc.id
    doc_dir = upload_dir / doc.id
    doc_dir.mkdir(parents=True, exist_ok=True)
    final_path = doc_dir / file.filename
    temp_path.replace(final_path)

    # Also update stored_path to the final location if you care (optional)
    # (requires a tiny update method in crud; safe to skip for now)

    # 3) Run pipeline
    result = processor.process(final_path)

    # Extract metrics safely
    ocr_conf = float(result.get("ocr", {}).get("confidence", 0.0) or 0.0)
    tokens = int(result.get("tokens_used", 0) or 0)
    cost = float(result.get("processing_cost", 0.0) or 0.0)
    extracted = result.get("extracted_data", {}) or {}

    # 4) Persist Result row
    res = crud.add_result(
        db,
        document_id=doc.id,
        ocr_conf=ocr_conf,
        tokens=tokens,
        cost=cost,
        extracted=extracted,
    )

    # (Optional) also write the full result JSON to disk as a backup
    processed_dir = Path(settings.processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)
    # Keep it simple: write {doc.id}.json
    try:
        import json
        with open(processed_dir / f"{doc.id}.json", "w", encoding="utf-8") as f:
            json.dump({"document_id": doc.id, **result}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Could not write processed JSON file: {e}")

    # 5) Response
    clean = result.get("extracted_data") or result.get("extracted_json") or {}
    return {"document": doc, "latest_result": res, "extracted_data": clean}


@app.get("/results/{doc_id}", response_model=schemas.ProcessResponse)
async def get_result(doc_id: str, db=Depends(get_db)):
    doc = crud.get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    res = crud.get_latest_result(db, doc_id)
    if not res:
        raise HTTPException(status_code=404, detail="No results for this document yet")
    return {"document": doc, "latest_result": res}


@app.get("/results")
async def list_results(limit: int = 10, db=Depends(get_db)):
    """List recent results with vendor name (if available)."""
    rows = crud.list_recent(db, limit=limit)
    enriched = []
    for row in rows:
        vendor = row.extracted_json.get("vendor") if row.extracted_json else "Unknown Vendor"
        enriched.append({
            "document_id": row.document_id,
            "vendor": vendor,
            "created_at": row.created_at,
        })
    return enriched

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, db=Depends(get_db)):
    ok = crud.delete_document_and_results(db, doc_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"deleted": True, "document_id": doc_id}

