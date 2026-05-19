from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    keyword: str | None = None


class IDPayload(BaseModel):
    id: str


class StatusPayload(BaseModel):
    id: str
    status: str


class TimestampMixin(ORMModel):
    id: str
    created_at: datetime
    updated_at: datetime


JsonDict = dict[str, Any]
