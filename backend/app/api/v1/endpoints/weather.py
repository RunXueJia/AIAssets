from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.auth import require_admin_actor
from app.core.responses import ApiResponse, success_response
from app.schemas.records import RecordActor
from app.schemas.weather import WeatherBatchSummaryRequest
from app.services.weather import WeatherService, weather_service

router = APIRouter(prefix="/weather", tags=["weather"])


def get_weather_service() -> WeatherService:
    return weather_service


@router.get("/query", response_model=ApiResponse)
async def query_weather(
    _actor: Annotated[RecordActor, Depends(require_admin_actor)],
    service: Annotated[WeatherService, Depends(get_weather_service)],
    city: Annotated[str, Query(min_length=1, max_length=80)],
    weather_date: Annotated[date | None, Query(alias="date")] = None,
) -> ApiResponse:
    data = await service.query_weather(city=city, weather_date=weather_date)
    return success_response(data=data)


@router.post("/batch_summary", response_model=ApiResponse)
async def batch_weather_summary(
    payload: WeatherBatchSummaryRequest,
    _actor: Annotated[RecordActor, Depends(require_admin_actor)],
    service: Annotated[WeatherService, Depends(get_weather_service)],
) -> ApiResponse:
    data = await service.summarize_route_weather(
        destination_city=payload.destination_city,
        route_cities=payload.route_cities,
        weather_date=payload.weather_date,
    )
    return success_response(data=data)
