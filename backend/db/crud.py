from sqlalchemy.orm import Session
from . import models

from pathlib import Path
from sqlalchemy.orm import Session
from . import models
from config import settings
import shutil, os

def create_document(db: Session, *, filename: str, content_type: str, size: int, stored_path: str) -> models.Document:
    doc = models.Document(
        filename=filename,
        content_type=content_type,
        size_bytes=size,
        stored_path=stored_path,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

def add_result(db: Session, *, document_id: str, ocr_conf: float, tokens: int, cost: float, extracted: dict) -> models.Result:
    res = models.Result(
        document_id=document_id,
        ocr_confidence=ocr_conf,
        tokens_used=tokens,
        api_cost=cost,
        extracted_json=extracted,
    )
    db.add(res)
    db.commit()
    db.refresh(res)
    return res

def get_document(db: Session, doc_id: str) -> models.Document | None:
    return db.get(models.Document, doc_id)

def get_latest_result(db: Session, doc_id: str) -> models.Result | None:
    return (
        db.query(models.Result)
        .filter(models.Result.document_id == doc_id)
        .order_by(models.Result.created_at.desc())
        .first()
    )

def list_recent(db: Session, limit: int = 10):
    return (
        db.query(models.Result)
        .order_by(models.Result.created_at.desc())
        .limit(limit)
        .all()
    )

def list_documents(db, limit=20):
    return db.query(models.Document).order_by(models.Document.created_at.desc()).limit(limit).all()


def delete_document_and_results(db: Session, doc_id: str) -> bool:
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        return False

    # delete result rows
    db.query(models.Result).filter(models.Result.document_id == doc_id).delete()

    # delete processed backup JSON
    try:
        (Path(settings.processed_dir) / f"{doc_id}.json").unlink(missing_ok=True)
    except Exception:
        pass

    # delete uploaded file/folder if you used per-doc subdir
    try:
        p = Path(doc.stored_path)
        folder = p.parent if p.exists() else (Path(settings.upload_dir) / doc_id)
        if folder.exists() and folder.is_dir():
            shutil.rmtree(folder)
        else:
            p.unlink(missing_ok=True)
    except Exception:
        pass

    db.delete(doc)
    db.commit()
    return True