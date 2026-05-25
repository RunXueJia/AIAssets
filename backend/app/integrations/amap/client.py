import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol
from urllib.parse import quote, urlencode
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

    async def reverse_geocode(
        self,
        *,
        location: str,
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
        waypoints: list[str | dict[str, Any]] | None = None,
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
        self.driving_endpoint = "https://restapi.amap.com/v5/direction/driving"
        self.walking_endpoint = "https://restapi.amap.com/v5/direction/walking"
        self.transit_endpoint = "https://restapi.amap.com/v5/direction/transit/integrated"
        self.bicycling_endpoint = "https://restapi.amap.com/v5/direction/bicycling"
        self.electrobike_endpoint = "https://restapi.amap.com/v5/direction/electrobike"
        self.static_map_endpoint = "https://restapi.amap.com/v3/staticmap"
        self.regeocode_endpoint = "https://restapi.amap.com/v3/geocode/regeo"

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
                    "city_code": str(poi.get("citycode") or ""),
                    "adname": str(poi.get("adname") or ""),
                    "adcode": str(poi.get("adcode") or ""),
                }
                for poi in pois
                if isinstance(poi, dict)
            ],
            "source_updated_at": _iso_now(),
            "mock": False,
            "provider": self.provider,
        }

    async def reverse_geocode(
        self,
        *,
        location: str,
    ) -> dict[str, Any]:
        if not self._is_location(location):
            raise AmapClientError("逆地理编码需要有效经纬度")
        params: dict[str, Any] = {
            "location": location,
            "extensions": "all",
            "radius": "1000",
            "roadlevel": "0",
        }
        payload = await self._cached_request("regeocode", self.regeocode_endpoint, params)
        regeocode = payload.get("regeocode")
        if not isinstance(regeocode, dict):
            raise AmapClientError("高德逆地理编码未返回结果")
        address = regeocode.get("addressComponent")
        if not isinstance(address, dict):
            raise AmapClientError("高德逆地理编码未返回地址组件")
        province = str(address.get("province") or "")
        city = str(address.get("city") or "")
        district = str(address.get("district") or "")
        adcode = str(address.get("adcode") or "")
        citycode = str(address.get("citycode") or "")
        formatted_address = str(regeocode.get("formatted_address") or "")
        return {
            "province": province,
            "city": city,
            "district": district,
            "adcode": adcode,
            "citycode": citycode,
            "formatted_address": formatted_address,
            "province_city_district": self._join_parts(province, city, district),
            "source_updated_at": _iso_now(),
            "mock": False,
            "provider": self.provider,
            "raw": payload,
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
        waypoint_locations = self._dedupe_route_waypoints(
            waypoint_locations,
            origin=origin_location,
            destination=destination_location,
        )
        params: dict[str, Any] = {
            "origin": origin_location,
            "destination": destination_location,
            "extensions": "base",
        }
        endpoint = self.driving_endpoint
        cache_scope = "route-driving"
        params["show_fields"] = "cost,tmcs"
        if normalized_mode == "walking":
            endpoint = self.walking_endpoint
            cache_scope = "route-walking"
            params["show_fields"] = "cost,navi"
        elif normalized_mode == "transit":
            endpoint = self.transit_endpoint
            cache_scope = "route-transit"
            params["show_fields"] = "cost"
            city1 = self._place_city_code_or_name(origin_place, origin)
            city2 = self._place_city_code_or_name(destination_place, destination)
            if city1:
                params["city1"] = city1
            if city2:
                params["city2"] = city2
        elif normalized_mode == "bicycling":
            endpoint = self.bicycling_endpoint
            cache_scope = "route-bicycling"
            params["show_fields"] = "cost,navi"
        elif normalized_mode == "electrobike":
            endpoint = self.electrobike_endpoint
            cache_scope = "route-electrobike"
            params["show_fields"] = "cost,navi"
        elif waypoint_locations:
            params["waypoints"] = ";".join(waypoint_locations)

        payload = await self._cached_request(cache_scope, endpoint, params)
        route = payload.get("route")
        if not isinstance(route, dict):
            raise AmapClientError("高德路径规划未返回路线")
        path = self._first_path(route)
        distance_m = self._int_value(path.get("distance"))
        duration_s = self._int_value(
            path.get("duration") or self._nested_value(path, "cost", "duration")
        )
        route_path_points = self._route_path_points(path)
        applied_waypoints = waypoint_locations if normalized_mode == "driving" else []
        route_waypoints = applied_waypoints or self._sample_route_path_points(route_path_points)
        route_waypoints_source = "requested" if applied_waypoints else (
            "route_path" if route_waypoints else "none"
        )
        return {
            "distance_m": distance_m,
            "duration_s": duration_s,
            "route_summary": self._route_summary(distance_m, duration_s),
            "provider": self.provider,
            "mock": False,
            "transport_mode": transport_mode,
            "origin_location": origin_location,
            "destination_location": destination_location,
            "waypoints": route_waypoints,
            "route_path_points": route_path_points,
            "route_waypoints_source": route_waypoints_source,
            "requested_waypoints": waypoint_locations,
            "raw": {
                "provider": self.provider,
                "origin": origin,
                "destination": destination,
                "origin_location": origin_location,
                "destination_location": destination_location,
                "transport_mode": transport_mode,
                "route_mode": normalized_mode,
                "waypoints": route_waypoints,
                "route_path_points": route_path_points,
                "route_waypoints_source": route_waypoints_source,
                "requested_waypoints": waypoint_locations,
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
        waypoints: list[str | dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        origin_place = await self._resolve_place(origin)
        destination_place = await self._resolve_place(destination)
        resolved_waypoints = []
        for waypoint in waypoints or []:
            normalized = self._normalize_link_waypoint(waypoint)
            if not normalized:
                continue
            resolved_waypoints.append(
                {
                    **await self._resolve_place(normalized["value"]),
                    "name": normalized["name"],
                }
            )
        resolved_waypoints = self._dedupe_uri_waypoints(
            resolved_waypoints,
            origin=origin_place["location"],
            destination=destination_place["location"],
        )
        route_url = self._route_uri(
            origin=origin_place["location"],
            destination=destination_place["location"],
            origin_name=origin_name,
            destination_name=destination_name,
            transport_mode=transport_mode,
            waypoints=resolved_waypoints,
        )
        if route_url is None:
            raise AmapClientError("缺少高德导航链接起终点")
        return {
            "amap_route_url": route_url,
            "mock": False,
            "provider": self.provider,
        }

    def _normalize_link_waypoint(
        self,
        waypoint: str | dict[str, Any],
    ) -> dict[str, str] | None:
        if isinstance(waypoint, str):
            value = waypoint.strip()
            if not value:
                return None
            return {"value": value, "name": self._waypoint_display_name(value)}
        location = str(waypoint.get("location") or "").strip()
        name = str(waypoint.get("name") or "").strip()
        if not location:
            return None
        return {"value": location, "name": name}

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
            "amap_route_url": self._route_uri(
                origin=origin,
                destination=destination,
                transport_mode="driving",
                waypoints=waypoints or [],
            ),
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
        if isinstance(paths, dict):
            return paths
        transits = route.get("transits")
        if isinstance(transits, list) and transits and isinstance(transits[0], dict):
            return transits[0]
        if isinstance(transits, dict):
            return transits
        raise AmapClientError("高德路径规划未返回可用方案")

    def _route_path_points(self, path: dict[str, Any]) -> list[str]:
        points: list[str] = []
        for step in self._route_steps(path):
            for field in ("polyline", "tmc_polyline"):
                self._append_polyline_points(points, step.get(field))
            tmcs = step.get("tmcs")
            if isinstance(tmcs, list):
                for tmc in tmcs:
                    if isinstance(tmc, dict):
                        self._append_polyline_points(points, tmc.get("polyline"))
        return self._dedupe_consecutive_points(points)

    def _route_steps(self, path: dict[str, Any]) -> list[dict[str, Any]]:
        steps = path.get("steps")
        if isinstance(steps, list):
            return [step for step in steps if isinstance(step, dict)]
        if isinstance(steps, dict):
            return [steps]
        segments = path.get("segments")
        if isinstance(segments, list):
            collected: list[dict[str, Any]] = []
            for segment in segments:
                if not isinstance(segment, dict):
                    continue
                segment_steps = segment.get("walking", {}).get("steps")
                if isinstance(segment_steps, list):
                    collected.extend(
                        step for step in segment_steps if isinstance(step, dict)
                    )
            return collected
        return []

    def _append_polyline_points(self, points: list[str], value: Any) -> None:
        if not isinstance(value, str):
            return
        for point in value.replace("|", ";").split(";"):
            point = point.strip()
            if self._is_location(point):
                points.append(point)

    def _dedupe_consecutive_points(self, points: list[str]) -> list[str]:
        deduped: list[str] = []
        for point in points:
            if not deduped or deduped[-1] != point:
                deduped.append(point)
        return deduped

    def _sample_route_path_points(self, points: list[str], *, max_points: int = 5) -> list[str]:
        if len(points) <= 2:
            return []
        middle = points[1:-1]
        if len(middle) <= max_points:
            return middle
        if max_points <= 1:
            return [middle[len(middle) // 2]]
        step = (len(middle) - 1) / (max_points - 1)
        return [middle[round(index * step)] for index in range(max_points)]

    async def _resolve_place(self, value: str) -> dict[str, str]:
        if self._is_location(value):
            return {"location": value, "city_name": "", "city_code": "", "adcode": ""}
        places = await self.search_places(keyword=value)
        for item in places.get("items") or []:
            if not isinstance(item, dict):
                continue
            location = item.get("location")
            if isinstance(location, str) and self._is_location(location):
                return {
                    "location": location,
                    "city_name": str(item.get("city_name") or ""),
                    "city_code": str(item.get("city_code") or ""),
                    "adcode": str(item.get("adcode") or ""),
                }
        raise AmapClientError(f"高德地点解析失败：{value}")

    def _normalize_transport_mode(self, transport_mode: str) -> str:
        if transport_mode in {"walking", "transit", "driving"}:
            return transport_mode
        if transport_mode == "cycling":
            return "bicycling"
        if transport_mode == "motorcycle":
            return "electrobike"
        if transport_mode == "mixed":
            return "transit"
        return "driving"

    def _uri_transport_mode(self, transport_mode: str) -> str:
        if transport_mode == "transit" or transport_mode == "mixed":
            return "bus"
        if transport_mode == "walking":
            return "walk"
        if transport_mode == "cycling" or transport_mode == "motorcycle":
            return "ride"
        return "car"

    def _city_code_or_name(self, location: str) -> str:
        return location if "," not in location else ""

    def _place_city_code_or_name(self, place: dict[str, str], fallback: str) -> str:
        return place.get("city_code") or place.get("city_name") or self._city_code_or_name(fallback)

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

    def _join_parts(self, *parts: str) -> str:
        return " ".join(part for part in parts if part)

    def _nested_value(self, data: dict[str, Any], *keys: str) -> Any:
        value: Any = data
        for key in keys:
            if not isinstance(value, dict):
                return None
            value = value.get(key)
        return value

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

    def _route_uri(
        self,
        *,
        origin: str | None,
        destination: str | None,
        origin_name: str | None = None,
        destination_name: str | None = None,
        transport_mode: str = "driving",
        waypoints: list[str] | list[dict[str, str]] | None = None,
    ) -> str | None:
        if not origin or not destination:
            return None
        mode = self._uri_transport_mode(transport_mode)
        waypoint_items = self._normalize_uri_waypoints(waypoints or [])
        if waypoint_items and mode in {"car", "ride"}:
            return self._multi_via_route_landing_url(
                origin=origin,
                destination=destination,
                origin_name=origin_name,
                destination_name=destination_name,
                waypoints=waypoint_items,
            )
        params = {
            "from": self._uri_point(origin, origin_name),
            "to": self._uri_point(destination, destination_name),
            "mode": mode,
            "src": "routecraft",
        }
        return f"https://uri.amap.com/navigation?{urlencode(params)}"

    def _multi_via_route_landing_url(
        self,
        *,
        origin: str,
        destination: str,
        origin_name: str | None,
        destination_name: str | None,
        waypoints: list[dict[str, str]],
    ) -> str:
        slon, slat = self._split_location(origin)
        dlon, dlat = self._split_location(destination)
        waypoint_lons: list[str] = []
        waypoint_lats: list[str] = []
        waypoint_names: list[str] = []
        for index, waypoint in enumerate(waypoints, start=1):
            lon, lat = self._split_location(waypoint["location"])
            waypoint_lons.append(lon)
            waypoint_lats.append(lat)
            waypoint_names.append(waypoint.get("name") or f"途径点{index}")
        schema_params = {
            "sid": "",
            "slat": slat,
            "slon": slon,
            "sname": origin_name or "",
            "did": "",
            "dlat": dlat,
            "dlon": dlon,
            "dname": destination_name or "",
            "m": "",
            "dev": "0",
            "t": "11",
            "vian": str(len(waypoints)),
            "vialons": "|".join(waypoint_lons),
            "vialats": "|".join(waypoint_lats),
            "vianames": "|".join(waypoint_names),
        }
        schema = f"amapuri://drive/multiViaPointPlan?{urlencode(schema_params)}"
        return (
            "https://act.amap.com/activity/2020CommonLanding/index.html?"
            f"id=default&local=1&schema={quote(schema, safe='%')}&whiteList=amap.com"
        )

    def _normalize_uri_waypoints(
        self,
        waypoints: list[str] | list[dict[str, str]],
    ) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []
        for waypoint in waypoints:
            if isinstance(waypoint, str):
                if self._is_location(waypoint):
                    items.append({"location": waypoint, "name": ""})
                continue
            location = waypoint.get("location")
            if self._is_location(location):
                items.append(
                    {
                        "location": str(location),
                        "name": str(waypoint.get("name") or ""),
                    }
                )
        return items

    def _split_location(self, location: str) -> tuple[str, str]:
        lon, lat = location.split(",", 1)
        return lon, lat

    def _dedupe_route_waypoints(
        self,
        waypoints: list[str],
        *,
        origin: str,
        destination: str,
    ) -> list[str]:
        seen = {origin, destination}
        deduped: list[str] = []
        for waypoint in waypoints:
            if waypoint in seen:
                continue
            seen.add(waypoint)
            deduped.append(waypoint)
        return deduped

    def _dedupe_uri_waypoints(
        self,
        waypoints: list[dict[str, str]],
        *,
        origin: str,
        destination: str,
    ) -> list[dict[str, str]]:
        seen = {origin, destination}
        deduped: list[dict[str, str]] = []
        for waypoint in waypoints:
            location = waypoint["location"]
            if location in seen:
                continue
            seen.add(location)
            deduped.append(waypoint)
        return deduped

    def _uri_point(self, location: str, name: str | None = None) -> str:
        normalized_name = (name or "").replace(",", " ").strip()
        return f"{location},{normalized_name}" if normalized_name else location

    def _waypoint_display_name(self, waypoint: str) -> str:
        waypoint = waypoint.strip()
        return "" if self._is_location(waypoint) else waypoint

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
