from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import get_settings
from app.integrations.amap import AmapClientError, AmapClientProtocol, create_amap_client
from app.schemas.amap import (
    AmapExportRouteMapRequest,
    AmapExportRouteMapResponse,
    AmapReverseGeocodeResponse,
    AmapRouteLinkRequest,
    AmapRouteLinkResponse,
    AmapRouteRequest,
    AmapRouteResponse,
    AmapSearchPlacesResponse,
)

APP_TZ = timezone(timedelta(hours=8))


class AmapService:
    def __init__(self, client: AmapClientProtocol | None = None) -> None:
        self.client = client or create_amap_client(api_key=self._configured_api_key())

    async def search_places(
        self,
        *,
        keyword: str,
        city: str | None = None,
    ) -> dict[str, Any]:
        data = await self.client.search_places(keyword=keyword, city=self._blank_to_none(city))
        return AmapSearchPlacesResponse.model_validate(data).model_dump(mode="json")

    async def reverse_geocode(self, *, location: str) -> dict[str, Any]:
        try:
            data = await self.client.reverse_geocode(location=location)
            return AmapReverseGeocodeResponse.model_validate(data).model_dump(mode="json")
        except (AmapClientError, TypeError, ValueError) as exc:
            provider = getattr(self.client, "provider", None)
            mock = bool(getattr(self.client, "mock", False))
            return AmapReverseGeocodeResponse(
                source_updated_at=self._now_iso(),
                provider=provider,
                mock=mock,
                fallback_reason=str(exc),
            ).model_dump(mode="json")

    async def calculate_route(self, payload: AmapRouteRequest) -> dict[str, Any]:
        data = await self.client.calculate_route(
            origin=payload.origin,
            destination=payload.destination,
            transport_mode=payload.transport_mode,
            waypoints=payload.waypoints,
        )
        return AmapRouteResponse.model_validate(data).model_dump(mode="json")

    async def create_route_link(self, payload: AmapRouteLinkRequest) -> dict[str, Any]:
        data = await self.client.create_route_link(
            origin_name=payload.origin_name,
            origin=payload.origin,
            destination_name=payload.destination_name,
            destination=payload.destination,
            transport_mode=payload.transport_mode,
            waypoints=[self._waypoint_payload(item) for item in payload.waypoints],
        )
        return AmapRouteLinkResponse.model_validate(data).model_dump(mode="json")

    async def export_route_map(self, payload: AmapExportRouteMapRequest) -> dict[str, Any]:
        data = await self.client.export_route_map(
            record_id=payload.record_id,
            route_snapshot_id=payload.route_snapshot_id,
            export_type=payload.export_type,
            origin=payload.origin,
            destination=payload.destination,
            waypoints=payload.waypoints,
            center=payload.center,
            size=payload.size,
            zoom=payload.zoom,
        )
        return AmapExportRouteMapResponse.model_validate(data).model_dump(mode="json")

    def _configured_api_key(self) -> str | None:
        settings = get_settings()
        return self._blank_to_none(settings.amap_api_key or settings.amap_key)

    def _blank_to_none(self, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    def _waypoint_payload(self, value: str | dict[str, Any]) -> str | dict[str, str]:
        if isinstance(value, str):
            return value
        return {
            key: str(item)
            for key, item in value.items()
            if key in {"name", "location"} and item is not None
        }

    def _now_iso(self) -> str:
        return datetime.now(APP_TZ).isoformat()
