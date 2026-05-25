from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import quote, urlencode

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

    async def reverse_geocode(
        self,
        *,
        location: str,
    ) -> dict[str, Any]:
        province, city, district = _mock_reverse_parts(location)
        return {
            "province": province,
            "city": city,
            "district": district,
            "adcode": "000000",
            "citycode": "000",
            "formatted_address": " ".join(part for part in [province, city, district] if part),
            "province_city_district": " ".join(
                part for part in [province, city, district] if part
            ),
            "source_updated_at": _iso_now(),
            "mock": True,
            "provider": self.provider,
            "raw": {
                "location": location,
                "province": province,
                "city": city,
                "district": district,
            },
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
            "transport_mode": transport_mode,
            "origin_location": origin,
            "destination_location": destination,
            "waypoints": waypoints,
            "route_path_points": [],
            "route_waypoints_source": "requested" if waypoints else "none",
            "requested_waypoints": waypoints,
            "raw": {
                "provider": self.provider,
                "origin": origin,
                "destination": destination,
                "transport_mode": transport_mode,
                "waypoints": waypoints,
                "route_path_points": [],
                "route_waypoints_source": "requested" if waypoints else "none",
                "requested_waypoints": waypoints,
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
        waypoints: list[str | dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        waypoint_items = [_normalize_waypoint(waypoint) for waypoint in waypoints or []]
        waypoint_items = [item for item in waypoint_items if item is not None]
        params = {
            "from": f"{origin},{origin_name}",
            "to": f"{destination},{destination_name}",
            "mode": _uri_transport_mode(transport_mode),
            "src": "routecraft",
        }
        if params["mode"] in {"car", "ride"} and waypoint_items:
            vianames = "|".join(
                item["name"] or f"途径点{index}"
                for index, item in enumerate(waypoint_items, start=1)
            )
            schema = (
                "amapuri://drive/multiViaPointPlan?"
                f"sid=&slat=30.29191&slon=120.21201&sname={origin_name}"
                f"&did=&dlat=30.236064&dlon=120.143222&dname={destination_name}"
                f"&m=&dev=0&t=11&vian={len(waypoint_items)}"
                f"&vialons={'|'.join(item['location'].split(',', 1)[0] for item in waypoint_items)}"
                f"&vialats={'|'.join(item['location'].split(',', 1)[1] for item in waypoint_items)}"
                f"&vianames={vianames}"
            )
            return {
                "amap_route_url": (
                    "https://act.amap.com/activity/2020CommonLanding/index.html?"
                    f"id=default&local=1&schema={quote(schema, safe='%')}&whiteList=amap.com"
                ),
                "mock": True,
                "provider": self.provider,
            }
        return {
            "amap_route_url": f"https://uri.amap.com/navigation?{urlencode(params)}",
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
        route_url = f"https://uri.amap.com/navigation?record={record_id}"
        if origin and destination and waypoints:
            route_url = await self.create_route_link(
                origin_name="",
                origin=origin,
                destination_name="",
                destination=destination,
                transport_mode="driving",
                waypoints=waypoints,
            )
            route_url = route_url["amap_route_url"]
        return {
            "export_id": route_snapshot_id or record_id,
            "status": "completed",
            "image_url": f"http://localhost:3002/static/route-maps/{record_id}.png",
            "export_type": export_type,
            "amap_route_url": route_url,
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


def _normalize_waypoint(waypoint: str | dict[str, Any]) -> dict[str, str] | None:
    if isinstance(waypoint, str):
        value = waypoint.strip()
        if not value or "," not in value:
            return None
        return {"location": value, "name": ""}
    location = str(waypoint.get("location") or "").strip()
    if not location or "," not in location:
        return None
    return {"location": location, "name": str(waypoint.get("name") or "").strip()}


def _mock_reverse_parts(location: str) -> tuple[str, str, str]:
    if location.startswith("120.21201,30.29191"):
        return "浙江省", "杭州市", "上城区"
    if location.startswith("120.143222,30.236064"):
        return "浙江省", "杭州市", "西湖区"
    return "示例省", "示例市", "示例区"


def _uri_transport_mode(transport_mode: str) -> str:
    if transport_mode in {"transit", "mixed"}:
        return "bus"
    if transport_mode == "walking":
        return "walk"
    if transport_mode in {"cycling", "motorcycle"}:
        return "ride"
    return "car"
