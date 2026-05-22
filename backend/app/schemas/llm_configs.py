from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class LlmConfigCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    provider: str = Field(min_length=1, max_length=50)
    base_url: str = Field(min_length=1, max_length=500)
    model_name: str = Field(min_length=1, max_length=120)
    api_key: str = Field(min_length=1)
    timeout_s: int = Field(default=60, ge=1, le=600)
    max_tokens: int | None = Field(default=None, ge=1)
    temperature: Decimal | None = Field(default=None, ge=0, le=2)
    is_default: bool = False


class LlmConfigUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    provider: str | None = Field(default=None, min_length=1, max_length=50)
    base_url: str | None = Field(default=None, min_length=1, max_length=500)
    model_name: str | None = Field(default=None, min_length=1, max_length=120)
    api_key: str | None = None
    timeout_s: int | None = Field(default=None, ge=1, le=600)
    max_tokens: int | None = Field(default=None, ge=1)
    temperature: Decimal | None = Field(default=None, ge=0, le=2)
    is_default: bool | None = None


class LlmConfigTestRequest(BaseModel):
    test_prompt: str = Field(default="请回复 OK", max_length=1000)


class PaginationResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[dict[str, Any]]


class LlmConfigListItem(BaseModel):
    id: int
    name: str
    provider: str
    base_url: str
    model_name: str
    api_key_masked: str
    status: str
    is_default: bool
    last_test_status: str | None = None
    last_test_at: datetime | None = None


class LlmConfigDetail(LlmConfigListItem):
    timeout_s: int
    max_tokens: int | None = None
    temperature: Decimal | None = None
    last_test_message: str | None = None


class LlmConfigStatusResponse(BaseModel):
    id: int
    status: str


class LlmConfigMutationResponse(BaseModel):
    id: int
    api_key_masked: str | None = None
