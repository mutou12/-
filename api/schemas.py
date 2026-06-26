from datetime import date, datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class CompanyDocBase(BaseModel):
    company_id: int = Field(..., description="企业ID")
    doc_type: str = Field(..., description="文档类型，例如 license/id_card/financial_report")
    doc_no: Optional[str] = Field(default=None, description="证件/文档编号")
    status: Optional[str] = Field(default=None, description="状态，例如 valid/expired")
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    content: Dict[str, Any] = Field(..., description="非固定字段，JSON对象")


class CompanyDocCreate(CompanyDocBase):
    pass


class CompanyDocUpdate(BaseModel):
    doc_no: Optional[str] = None
    status: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    content: Optional[Dict[str, Any]] = None


class CompanyDocRead(CompanyDocBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
