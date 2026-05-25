from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.auth import get_current_actor, require_admin_actor
from app.core.responses import ApiResponse, success_response
from app.schemas.amap import (
    AmapExportRouteMapRequest,
    AmapReverseGeocodeRequest,
    AmapRouteLinkRequest,
    AmapRouteRequest,
)
from app.schemas.records import RecordActor
from app.services.amap import AmapService

router = APIRouter(prefix="/amap", tags=["amap"])
service: AmapService | None = None


def get_amap_service() -> AmapService:
    global service
    if service is None:
        service = AmapService()
    return service


@router.get("/search_places", response_model=ApiResponse)
async def search_places(
    _actor: Annotated[RecordActor, Depends(require_admin_actor)],
    amap_service: Annotated[AmapService, Depends(get_amap_service)],
    keyword: Annotated[str, Query(min_length=1, max_length=120)],
    city: Annotated[str | None, Query(max_length=80)] = None,
) -> ApiResponse:
    data = await amap_service.search_places(keyword=keyword, city=city)
    return success_response(data=data)


@router.post("/reverse_geocode", response_model=ApiResponse)
async def reverse_geocode(
    payload: AmapReverseGeocodeRequest,
    _actor: Annotated[RecordActor, Depends(get_current_actor)],
    amap_service: Annotated[AmapService, Depends(get_amap_service)],
) -> ApiResponse:
    data = await amap_service.reverse_geocode(location=payload.location)
    return success_response(data=data)


@router.post("/calculate_route", response_model=ApiResponse)
async def calculate_route(
    payload: AmapRouteRequest,
    _actor: Annotated[RecordActor, Depends(require_admin_actor)],
    amap_service: Annotated[AmapService, Depends(get_amap_service)],
) -> ApiResponse:
    data = await amap_service.calculate_route(payload)
    return success_response(data=data)


@router.post("/create_route_link", response_model=ApiResponse)
async def create_route_link(
    payload: AmapRouteLinkRequest,
    _actor: Annotated[RecordActor, Depends(require_admin_actor)],
    amap_service: Annotated[AmapService, Depends(get_amap_service)],
) -> ApiResponse:
    data = await amap_service.create_route_link(payload)
    return success_response(data=data)


@router.post("/export_route_map", response_model=ApiResponse)
async def export_route_map(
    payload: AmapExportRouteMapRequest,
    _actor: Annotated[RecordActor, Depends(require_admin_actor)],
    amap_service: Annotated[AmapService, Depends(get_amap_service)],
) -> ApiResponse:
    data = await amap_service.export_route_map(payload)
    return success_response(data=data)
