from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.auth import require_admin_actor
from app.core.responses import ApiResponse, success_response
from app.schemas.amap import (
    AmapExportRouteMapRequest,
    AmapRouteLinkRequest,
    AmapRouteRequest,
)
from app.schemas.records import RecordActor
from app.services.amap import AmapService

router = APIRouter(prefix="/amap", tags=["amap"])
service = AmapService()


@router.get("/search_places", response_model=ApiResponse)
async def search_places(
    _actor: Annotated[RecordActor, Depends(require_admin_actor)],
    keyword: Annotated[str, Query(min_length=1, max_length=120)],
    city: Annotated[str | None, Query(max_length=80)] = None,
) -> ApiResponse:
    data = await service.search_places(keyword=keyword, city=city)
    return success_response(data=data)


@router.post("/calculate_route", response_model=ApiResponse)
async def calculate_route(
    payload: AmapRouteRequest,
    _actor: Annotated[RecordActor, Depends(require_admin_actor)],
) -> ApiResponse:
    data = await service.calculate_route(payload)
    return success_response(data=data)


@router.post("/create_route_link", response_model=ApiResponse)
async def create_route_link(
    payload: AmapRouteLinkRequest,
    _actor: Annotated[RecordActor, Depends(require_admin_actor)],
) -> ApiResponse:
    data = await service.create_route_link(payload)
    return success_response(data=data)


@router.post("/export_route_map", response_model=ApiResponse)
async def export_route_map(
    payload: AmapExportRouteMapRequest,
    _actor: Annotated[RecordActor, Depends(require_admin_actor)],
) -> ApiResponse:
    data = await service.export_route_map(payload)
    return success_response(data=data)
