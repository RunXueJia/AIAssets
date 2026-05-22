from typing import Any

from pydantic import BaseModel, Field


class TripPlanningContext(BaseModel):
    request: dict[str, Any]
    weather: dict[str, Any]
    route: dict[str, Any]
    transport: dict[str, Any]
    map_export: dict[str, Any]
    attractions: dict[str, Any]
    realtime: dict[str, Any]
    risks: list[str] = Field(default_factory=list)
    prompt: str


class TripPlanningResult(BaseModel):
    summary_title: str
    summary_text: str
    snapshots: dict[str, dict[str, Any]]
    final_markdown: str
    result_json: dict[str, Any]
    weather_summary: str | None = None
    route_summary: str | None = None
    attractions_summary: str | None = None
    realtime_info_summary: str | None = None
    risk_summary: str | None = None
    amap_route_url: str | None = None
    context: TripPlanningContext


class TripPlanningExternalContext(BaseModel):
    weather: dict[str, Any]
    route: dict[str, Any]
    transport: dict[str, Any]
    map_export: dict[str, Any]
    attractions: dict[str, Any]
    realtime: dict[str, Any]
