from sqlalchemy import JSON, BigInteger, Column, Date, DateTime, String, func

from api.database import Base


class CompanyDoc(Base):
    __tablename__ = "company_doc"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_id = Column(BigInteger, nullable=False, index=True)
    doc_type = Column(String(64), nullable=False, index=True)
    doc_no = Column(String(128), nullable=True)
    status = Column(String(32), nullable=True, index=True)
    issue_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    content = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
