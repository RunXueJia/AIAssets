from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field

TransportMode = Literal["driving", "transit", "walking", "cycling", "mixed"]
GenerationStatus = Literal["pending", "streaming", "completed", "failed", "canceled"]
GenerationStage = Literal[
    "understanding",
    "weather",
    "route",
    "transport",
    "map_export",
    "attractions",
    "realtime",
    "summary",
]
StreamEventType = Literal["record_created", "stage", "token", "snapshot", "done", "error"]


class GenerateStreamRequest(BaseModel):
    origin: str = Field(min_length=1, max_length=255)
    destination: str = Field(min_length=1, max_length=255)
    range: str = Field(min_length=1, max_length=120)
    transport_mode: TransportMode = "mixed"
    travel_date: date | None = None
    people_count: int | None = Field(default=None, ge=1, le=99)
    preferences: list[str] = Field(default_factory=list)
    avoidances: list[str] = Field(default_factory=list)


class GenerationRecordCreated(BaseModel):
    record_id: int
    record_no: str
    status: GenerationStatus


class GenerationStageEvent(BaseModel):
    record_id: int
    stage: GenerationStage
    stage_name: str
    status: GenerationStatus


class GenerationTokenEvent(BaseModel):
    record_id: int
    stage: GenerationStage
    content: str


class GenerationSnapshotEvent(BaseModel):
    record_id: int
    type: str
    data: dict[str, Any]


class GenerationDoneEvent(BaseModel):
    record_id: int
    status: GenerationStatus
    duration_ms: int


class GenerationStreamEvent(BaseModel):
    event: StreamEventType
    data: dict[str, Any]


class CancelGenerationData(BaseModel):
    record_id: int
    status: GenerationStatus
