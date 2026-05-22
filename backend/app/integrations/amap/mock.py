from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

APP_TZ = timezone(timedelta(hours=8))


class MockAmapClient:
    def __init__(self, *, provider: str = "mock") -> None:
        self.provider = provider

    async def search_places(
        self,
        *,
        keyword: str,
        city: str | None = None,
    ) -> dict[str, Any]:
        return {
            "items": [
                {
                    "name": f"{keyword}风景名胜区",
                    "address": f"{city or '示例城市'}示例地址",
                    "location": "120.143222,30.236064",
                    "type": "风景名胜",
                    "province_name": "示例省",
                    "city_name": city or "示例城市",
                    "adname": "示例区",
                }
            ],
            "source_updated_at": _iso_now(),
            "mock": True,
            "provider": self.provider,
        }

    async def calculate_route(
        self,
        *,
        origin: str,
        destination: str,
        transport_mode: str,
        waypoints: list[str],
    ) -> dict[str, Any]:
        return {
            "distance_m": 12800,
            "duration_s": 2400,
            "route_summary": "约12.8公里，预计40分钟",
            "mock": True,
            "provider": self.provider,
            "raw": {
                "provider": self.provider,
                "origin": origin,
                "destination": destination,
                "transport_mode": transport_mode,
                "waypoints": waypoints,
            },
        }

    async def create_route_link(
        self,
        *,
        origin_name: str,
        origin: str,
        destination_name: str,
        destination: str,
        transport_mode: str,
    ) -> dict[str, Any]:
        params = urlencode(
            {
                "from": f"{origin},{origin_name}",
                "to": f"{destination},{destination_name}",
                "mode": transport_mode,
            }
        )
        return {
            "amap_route_url": f"https://uri.amap.com/navigation?{params}",
            "mock": True,
            "provider": self.provider,
        }

    async def export_route_map(
        self,
        *,
        record_id: int,
        route_snapshot_id: int | None,
        export_type: str,
        origin: str | None = None,
        destination: str | None = None,
        waypoints: list[str] | None = None,
        center: str | None = None,
        size: str = "750*500",
        zoom: int = 11,
    ) -> dict[str, Any]:
        return {
            "export_id": route_snapshot_id or record_id,
            "status": "completed",
            "image_url": f"http://localhost:3002/static/route-maps/{record_id}.png",
            "export_type": export_type,
            "amap_route_url": f"https://uri.amap.com/navigation?record={record_id}",
            "width": _size_part(size, 0),
            "height": _size_part(size, 1),
            "mock": True,
            "provider": self.provider,
        }


def _iso_now() -> str:
    return datetime.now(APP_TZ).isoformat()


def _size_part(size: str, index: int) -> int | None:
    parts = size.split("*", 1)
    if len(parts) != 2:
        return None
    try:
        return int(parts[index])
    except ValueError:
        return None
