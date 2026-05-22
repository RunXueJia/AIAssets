from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WeatherAlert(BaseModel):
    title: str = ""
    level: str = "none"
    description: str = ""
    source: str | None = None


class WeatherCitySummary(BaseModel):
    city_name: str
    weather_date: date | None = None
    weather_summary: str
    alert_level: str = "none"
    alerts: list[WeatherAlert] = Field(default_factory=list)
    condition: str | None = None
    temperature_range: str | None = None
    wind: str | None = None
    humidity: str | None = None
    provider: str = "mock"
    source_updated_at: str
    mock: bool = False
    fallback_reason: str | None = None
    date_matched: bool = True
    raw: dict[str, Any] = Field(default_factory=dict)


class WeatherBatchSummaryRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    destination_city: str = Field(min_length=1, max_length=80)
    route_cities: list[str] = Field(default_factory=list, max_length=20)
    weather_date: date | None = Field(default=None, alias="date")


class WeatherBatchSummary(BaseModel):
    destination_city: str
    route_city_names: list[str] = Field(default_factory=list)
    destination: WeatherCitySummary
    route_cities: list[WeatherCitySummary] = Field(default_factory=list)
    items: list[WeatherCitySummary] = Field(default_factory=list)
    weather_summary: str
    alert_level: str = "none"
    alerts: list[WeatherAlert] = Field(default_factory=list)
    provider: str = "mock"
    source_updated_at: str
    mock: bool = False
    fallback_reason: str | None = None
