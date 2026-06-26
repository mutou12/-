from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from api import crud, models, schemas
from api.database import Base, engine, get_db

app = FastAPI(title="Company Document API", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/docs", response_model=schemas.CompanyDocRead)
def create_doc(payload: schemas.CompanyDocCreate, db: Session = Depends(get_db)):
    return crud.create_doc(db, payload)


@app.get("/docs/{doc_id}", response_model=schemas.CompanyDocRead)
def get_doc(doc_id: int, db: Session = Depends(get_db)):
    obj = crud.get_doc(db, doc_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="document not found")
    return obj


@app.get("/companies/{company_id}/docs", response_model=list[schemas.CompanyDocRead])
def list_docs(
    company_id: int,
    doc_type: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    return crud.list_docs_by_company(
        db=db,
        company_id=company_id,
        doc_type=doc_type,
        status=status,
    )


@app.patch("/docs/{doc_id}", response_model=schemas.CompanyDocRead)
def update_doc(
    doc_id: int,
    payload: schemas.CompanyDocUpdate,
    db: Session = Depends(get_db),
):
    obj = crud.update_doc(db, doc_id, payload)
    if obj is None:
        raise HTTPException(status_code=404, detail="document not found")
    return obj


@app.delete("/docs/{doc_id}")
def delete_doc(doc_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_doc(db, doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="document not found")
    return {"deleted": True}
