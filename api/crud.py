from typing import Optional

from sqlalchemy.orm import Session

from api import models, schemas


def create_doc(db: Session, payload: schemas.CompanyDocCreate) -> models.CompanyDoc:
    obj = models.CompanyDoc(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_doc(db: Session, doc_id: int) -> Optional[models.CompanyDoc]:
    return db.query(models.CompanyDoc).filter(models.CompanyDoc.id == doc_id).first()


def list_docs_by_company(
    db: Session,
    company_id: int,
    doc_type: Optional[str] = None,
    status: Optional[str] = None,
) -> list[models.CompanyDoc]:
    query = db.query(models.CompanyDoc).filter(models.CompanyDoc.company_id == company_id)
    if doc_type:
        query = query.filter(models.CompanyDoc.doc_type == doc_type)
    if status:
        query = query.filter(models.CompanyDoc.status == status)
    return query.order_by(models.CompanyDoc.created_at.desc()).all()


def update_doc(
    db: Session, doc_id: int, payload: schemas.CompanyDocUpdate
) -> Optional[models.CompanyDoc]:
    obj = get_doc(db, doc_id)
    if obj is None:
        return None

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(obj, key, value)

    db.commit()
    db.refresh(obj)
    return obj


def delete_doc(db: Session, doc_id: int) -> bool:
    obj = get_doc(db, doc_id)
    if obj is None:
        return False
    db.delete(obj)
    db.commit()
    return True
