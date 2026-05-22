from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class RecordActor(BaseModel):
    user_id: int
    role: str = "user"


class RegenerateRecordRequest(BaseModel):
    override_input: dict[str, Any] = Field(default_factory=dict)


class PaginationResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[dict[str, Any]]


class PlanningRecordListItem(BaseModel):
    id: int
    record_no: str
    origin_text: str
    destination_text: str
    range_text: str
    transport_mode: str
    status: str
    summary_title: str | None = None
    summary_text: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None


class AdminRecordListItem(BaseModel):
    id: int
    record_no: str
    user_id: int
    user_nickname: str | None = None
    origin_text: str
    destination_text: str
    transport_mode: str
    status: str
    duration_ms: int | None = None
    error_message: str | None = None
    created_at: datetime | None = None


class RecordSummary(BaseModel):
    id: int
    record_no: str
    status: str
    current_stage: str | None = None
    origin_text: str
    destination_text: str
    transport_mode: str
    duration_ms: int | None = None
    created_at: datetime | None = None


class RecordInputSnapshot(BaseModel):
    origin_text: str | None = None
    destination_text: str | None = None
    range_text: str | None = None
    travel_date: date | None = None
    people_count: int | None = None
    preferences: list[str] = Field(default_factory=list)
    avoidances: list[str] = Field(default_factory=list)


class RecordOutputSnapshot(BaseModel):
    final_markdown: str | None = None
    result_json: dict[str, Any] = Field(default_factory=dict)
    weather_summary: str | None = None
    route_summary: str | None = None
    attractions_summary: str | None = None
    realtime_info_summary: str | None = None
    risk_summary: str | None = None
    amap_route_url: str | None = None


class RegenerateRecordResponse(BaseModel):
    record_id: int
    parent_record_id: int
    status: str
    stream_url: str | None = None
    request_payload: dict[str, Any] | None = None
