import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.integrations.cache import TtlCache

APP_TZ = timezone(timedelta(hours=8))


class AmapClientError(Exception):
    pass


class AmapClientProtocol(Protocol):
    async def search_places(
        self,
        *,
        keyword: str,
        city: str | None = None,
    ) -> dict[str, Any]: ...

    async def calculate_route(
        self,
        *,
        origin: str,
        destination: str,
        transport_mode: str,
        waypoints: list[str],
    ) -> dict[str, Any]: ...

    async def create_route_link(
        self,
        *,
        origin_name: str,
        origin: str,
        destination_name: str,
        destination: str,
        transport_mode: str,
    ) -> dict[str, Any]: ...

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
    ) -> dict[str, Any]: ...


class AmapWebServiceClient:
    provider = "amap"
    mock = False

    def __init__(
        self,
        *,
        api_key: str,
        timeout_s: float = 8,
        max_retries: int = 1,
        cache: TtlCache | None = None,
    ) -> None:
        self.api_key = api_key
        self.timeout_s = timeout_s
        self.max_retries = max_retries
        self.cache = cache or TtlCache(ttl_s=300)
        self.place_endpoint = "https://restapi.amap.com/v3/place/text"
        self.driving_endpoint = "https://restapi.amap.com/v3/direction/driving"
        self.walking_endpoint = "https://restapi.amap.com/v3/direction/walking"
        self.transit_endpoint = "https://restapi.amap.com/v3/direction/transit/integrated"
        self.static_map_endpoint = "https://restapi.amap.com/v3/staticmap"

    async def search_places(
        self,
        *,
        keyword: str,
        city: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "keywords": keyword,
            "city": city or "",
            "citylimit": "false",
            "offset": "10",
            "page": "1",
            "extensions": "base",
        }
        payload = await self._cached_request("place", self.place_endpoint, params)
        pois = payload.get("pois")
        if not isinstance(pois, list):
            raise AmapClientError("高德地点搜索未返回 POI 列表")
        return {
            "items": [
                {
                    "name": str(poi.get("name") or ""),
                    "address": self._address_text(poi.get("address")),
                    "location": str(poi.get("location") or ""),
                    "type": str(poi.get("type") or ""),
                    "province_name": str(poi.get("pname") or ""),
                    "city_name": str(poi.get("cityname") or ""),
                    "adname": str(poi.get("adname") or ""),
                }
                for poi in pois
                if isinstance(poi, dict)
            ],
            "source_updated_at": _iso_now(),
            "mock": False,
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
        normalized_mode = self._normalize_transport_mode(transport_mode)
        origin_place = await self._resolve_place(origin)
        destination_place = await self._resolve_place(destination)
        origin_location = origin_place["location"]
        destination_location = destination_place["location"]
        waypoint_locations = []
        for waypoint in waypoints:
            resolved = await self._resolve_place(waypoint)
            waypoint_locations.append(resolved["location"])
        params: dict[str, Any] = {
            "origin": origin_location,
            "destination": destination_location,
            "extensions": "base",
        }
        endpoint = self.driving_endpoint
        cache_scope = "route-driving"
        if normalized_mode == "walking":
            endpoint = self.walking_endpoint
            cache_scope = "route-walking"
        elif normalized_mode == "transit":
            endpoint = self.transit_endpoint
            cache_scope = "route-transit"
            params["city"] = origin_place["city_name"] or self._city_code_or_name(origin)
            params["cityd"] = destination_place["city_name"] or self._city_code_or_name(destination)
        elif waypoint_locations:
            params["waypoints"] = ";".join(waypoint_locations)

        payload = await self._cached_request(cache_scope, endpoint, params)
        route = payload.get("route")
        if not isinstance(route, dict):
            raise AmapClientError("高德路径规划未返回路线")
        path = self._first_path(route)
        distance_m = self._int_value(path.get("distance"))
        duration_s = self._int_value(path.get("duration"))
        return {
            "distance_m": distance_m,
            "duration_s": duration_s,
            "route_summary": self._route_summary(distance_m, duration_s),
            "provider": self.provider,
            "mock": False,
            "origin_location": origin_location,
            "destination_location": destination_location,
            "waypoints": waypoint_locations,
            "raw": {
                "provider": self.provider,
                "origin": origin,
                "destination": destination,
                "origin_location": origin_location,
                "destination_location": destination_location,
                "transport_mode": transport_mode,
                "waypoints": waypoint_locations,
                "route": route,
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
                "mode": self._normalize_transport_mode(transport_mode),
            }
        )
        return {
            "amap_route_url": f"https://uri.amap.com/navigation?{params}",
            "mock": False,
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
        marker_locations = [
            value for value in [origin, *(waypoints or []), destination] if self._is_location(value)
        ]
        center_location = (
            center if self._is_location(center) else self._center_from(marker_locations)
        )
        params = {
            "key": self.api_key,
            "location": center_location,
            "zoom": str(zoom),
            "size": size,
            "scale": "2",
        }
        if marker_locations:
            labels = ["S", *["P" for _ in marker_locations[1:-1]], "E"]
            if len(marker_locations) == 1:
                labels = ["A"]
            params["markers"] = "|".join(
                f"mid,,{label}:{location}"
                for label, location in zip(labels, marker_locations, strict=False)
            )
            params["paths"] = f"5,0x1677FF,0.8,,:{';'.join(marker_locations)}"
        else:
            params["markers"] = f"mid,,A:{center_location}"
        image_url = f"{self.static_map_endpoint}?{urlencode(params)}"
        return {
            "export_id": route_snapshot_id or record_id,
            "status": "completed",
            "image_url": image_url,
            "export_type": export_type,
            "amap_route_url": self._route_uri(origin=origin, destination=destination),
            "width": self._size_part(size, 0),
            "height": self._size_part(size, 1),
            "mock": False,
            "provider": self.provider,
        }

    async def _cached_request(
        self,
        scope: str,
        endpoint: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        full_params = {"key": self.api_key, "output": "json", **params}
        cache_key = f"{scope}:{endpoint}:{urlencode(sorted(full_params.items()))}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        payload = await self._request(endpoint, full_params)
        self.cache.set(cache_key, payload)
        return payload

    async def _request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                payload = await asyncio.to_thread(self._request_sync, endpoint, params)
                if payload.get("status") != "1":
                    message = payload.get("info") or payload.get("infocode") or "高德接口返回失败"
                    raise AmapClientError(str(message))
                return payload
            except AmapClientError as exc:
                last_error = exc
            if attempt < self.max_retries:
                await asyncio.sleep(0.2 * (2**attempt))
        raise AmapClientError(str(last_error or "高德接口请求失败"))

    def _request_sync(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            f"{endpoint}?{urlencode(params)}",
            headers={"User-Agent": "RouteCraft/1.0"},
        )
        try:
            with urlopen(request, timeout=self.timeout_s) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise AmapClientError(f"高德接口请求失败: {exc}") from exc

    def _first_path(self, route: dict[str, Any]) -> dict[str, Any]:
        paths = route.get("paths")
        if isinstance(paths, list) and paths and isinstance(paths[0], dict):
            return paths[0]
        transits = route.get("transits")
        if isinstance(transits, list) and transits and isinstance(transits[0], dict):
            return transits[0]
        raise AmapClientError("高德路径规划未返回可用方案")

    async def _resolve_place(self, value: str) -> dict[str, str]:
        if self._is_location(value):
            return {"location": value, "city_name": ""}
        places = await self.search_places(keyword=value)
        for item in places.get("items") or []:
            if not isinstance(item, dict):
                continue
            location = item.get("location")
            if isinstance(location, str) and self._is_location(location):
                return {
                    "location": location,
                    "city_name": str(item.get("city_name") or ""),
                }
        raise AmapClientError(f"高德地点解析失败：{value}")

    def _normalize_transport_mode(self, transport_mode: str) -> str:
        if transport_mode in {"walking", "transit", "driving"}:
            return transport_mode
        if transport_mode == "mixed":
            return "transit"
        return "driving"

    def _city_code_or_name(self, location: str) -> str:
        return location if "," not in location else ""

    def _route_summary(self, distance_m: int, duration_s: int) -> str:
        distance_km = distance_m / 1000
        duration_min = max(1, round(duration_s / 60))
        return f"约{distance_km:.1f}公里，预计{duration_min}分钟"

    def _int_value(self, value: Any) -> int:
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return 0

    def _address_text(self, value: Any) -> str:
        if isinstance(value, list):
            return "".join(str(item) for item in value)
        return str(value or "")

    def _is_location(self, value: str | None) -> bool:
        if not value or "," not in value:
            return False
        lng, lat = value.split(",", 1)
        try:
            float(lng)
            float(lat)
        except ValueError:
            return False
        return True

    def _center_from(self, locations: list[str]) -> str:
        if not locations:
            return "120.143222,30.236064"
        lng_values: list[float] = []
        lat_values: list[float] = []
        for location in locations:
            lng, lat = location.split(",", 1)
            lng_values.append(float(lng))
            lat_values.append(float(lat))
        return f"{sum(lng_values) / len(lng_values):.6f},{sum(lat_values) / len(lat_values):.6f}"

    def _route_uri(self, *, origin: str | None, destination: str | None) -> str | None:
        if not origin or not destination:
            return None
        return f"https://uri.amap.com/navigation?{urlencode({'from': origin, 'to': destination})}"

    def _size_part(self, size: str, index: int) -> int | None:
        parts = size.split("*", 1)
        if len(parts) != 2:
            return None
        try:
            return int(parts[index])
        except ValueError:
            return None


def create_amap_client(*, api_key: str | None = None) -> AmapClientProtocol:
    if api_key:
        return AmapWebServiceClient(api_key=api_key)
    raise AmapClientError("未配置高德 Web 服务 Key：请设置 BACKEND_AMAP_API_KEY")


# Backward-compatible alias used by existing tests/imports.
AmapRealClient = AmapWebServiceClient


def _iso_now() -> str:
    return datetime.now(APP_TZ).isoformat()
