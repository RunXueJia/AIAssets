from typing import Any, Literal

from pydantic import BaseModel, Field

RealtimeCategory = Literal["news", "traffic", "guide", "pitfall"]


class RealtimeItem(BaseModel):
    title: str
    url: str | None = None
    source: str
    published_at: str | None = None
    category: RealtimeCategory
    classification: str
    summary: str
    tags: list[str] = Field(default_factory=list)
    credibility_score: float = Field(ge=0, le=100)
    credibility_label: str
    source_type: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class RealtimeSourceSummary(BaseModel):
    source: str
    item_count: int
    latest_published_at: str | None = None
    credibility_avg: float


class RealtimeSearchResult(BaseModel):
    keyword: str
    category: RealtimeCategory
    items: list[RealtimeItem] = Field(default_factory=list)
    sources: list[RealtimeSourceSummary] = Field(default_factory=list)
    realtime_info_summary: str
    provider: str = "mock"
    source_updated_at: str
    mock: bool = False
    fallback_reason: str | None = None
