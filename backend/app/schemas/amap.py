from typing import Any

from pydantic import BaseModel, Field


class AmapRouteRequest(BaseModel):
    origin: str = Field(min_length=1, max_length=80)
    destination: str = Field(min_length=1, max_length=80)
    transport_mode: str = Field(default="driving", max_length=30)
    waypoints: list[str] = Field(default_factory=list)


class AmapRouteLinkRequest(BaseModel):
    origin_name: str = Field(min_length=1, max_length=120)
    origin: str = Field(min_length=1, max_length=80)
    destination_name: str = Field(min_length=1, max_length=120)
    destination: str = Field(min_length=1, max_length=80)
    transport_mode: str = Field(default="driving", max_length=30)


class AmapExportRouteMapRequest(BaseModel):
    record_id: int = Field(ge=1)
    route_snapshot_id: int | None = Field(default=None, ge=1)
    export_type: str = Field(default="screenshot", max_length=30)
    origin: str | None = Field(default=None, max_length=80)
    destination: str | None = Field(default=None, max_length=80)
    waypoints: list[str] = Field(default_factory=list)
    center: str | None = Field(default=None, max_length=80)
    size: str = Field(default="750*500", max_length=20)
    zoom: int = Field(default=11, ge=1, le=17)


class AmapSearchPlacesResponse(BaseModel):
    items: list[dict[str, Any]]
    source_updated_at: str
    mock: bool = False
    provider: str | None = None
    fallback_reason: str | None = None


class AmapRouteResponse(BaseModel):
    distance_m: int
    duration_s: int
    route_summary: str
    raw: dict[str, Any]
    provider: str | None = None
    mock: bool = False
    fallback_reason: str | None = None


class AmapRouteLinkResponse(BaseModel):
    amap_route_url: str
    mock: bool = False
    provider: str | None = None
    fallback_reason: str | None = None


class AmapExportRouteMapResponse(BaseModel):
    export_id: int
    status: str
    image_url: str | None = None
    export_type: str
    mock: bool = False
    provider: str | None = None
    amap_route_url: str | None = None
    width: int | None = None
    height: int | None = None
    fallback_reason: str | None = None
