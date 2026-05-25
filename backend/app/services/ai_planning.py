import asyncio
import re
from datetime import datetime, timedelta, timezone
from html import escape as escape_html
from typing import Any

from app.schemas.ai_planning import (
    TripPlanningContext,
    TripPlanningExternalContext,
    TripPlanningResult,
)
from app.schemas.amap import AmapExportRouteMapRequest, AmapRouteLinkRequest, AmapRouteRequest
from app.schemas.generation import GenerateStreamRequest, GenerationStage
from app.schemas.realtime import RealtimeCategory
from app.services.amap import AmapService
from app.services.realtime import RealtimeService
from app.services.weather import WeatherService

APP_TZ = timezone(timedelta(hours=8))

PROMPT_TEMPLATE = """你是路书匠 AI 规划引擎。
请基于用户需求、天气、路线、实时信息和偏好约束，生成可执行的出行规划。

用户需求：
- 起点：{origin}
- 目的地：{destination}
- 范围：{range_text}
- 交通方式：{transport_mode}
- 出行日期：{travel_date}
- 人数：{people_count}
- 偏好：{preferences}
- 避免项：{avoidances}

已聚合上下文：
- 天气：{weather_summary}
- 路线：{route_summary}
- 地图链接：{amap_route_url}
- 导航途径点：{navigation_waypoint_summary}
- 景点：{attractions_summary}
- 实时信息：{realtime_summary}

输出要求：
1. 先给天气与风险提示。
2. 给出路径点规划、公共交通或驾车建议。
3. 给出途径景点说明。
4. 实时信息部分必须使用 Markdown 有序列表格式，每条以“1.”、“2.”开头。
5. 最终输出 Markdown 和 JSON 摘要。
"""


class AiPlanningService:
    def __init__(
        self,
        *,
        weather_service: WeatherService | None = None,
        amap_service: AmapService | None = None,
        realtime_service: RealtimeService | None = None,
    ) -> None:
        self.weather_service = weather_service or WeatherService()
        self.amap_service = amap_service or AmapService()
        self.realtime_service = realtime_service or RealtimeService()

    async def build_result(
        self,
        record_id: int,
        request: GenerateStreamRequest,
    ) -> TripPlanningResult:
        external = await self.build_external_context(record_id=record_id, request=request)
        context = self.build_context(request=request, external=external)
        summary_title = f"{request.origin}到{request.destination}规划草案"
        summary_text = self._summary_text(context)
        risk_summary = "；".join(context.risks) if context.risks else "暂无明显风险。"
        final_markdown = self._final_markdown(
            summary_title=summary_title,
            summary_text=summary_text,
            context=context,
            risk_summary=risk_summary,
        )
        snapshots = {
            "weather": context.weather,
            "route": context.route,
            "transport": context.transport,
            "map_export": context.map_export,
            "attractions": context.attractions,
            "realtime": context.realtime,
            "summary": {
                "summary_title": summary_title,
                "summary_text": summary_text,
                "risk_summary": risk_summary,
                "final_markdown": final_markdown,
                "result_json": {},
                "source_updated_at": self._iso_now(),
            },
        }
        result_json: dict[str, Any] = {
            "record_id": record_id,
            "summary_title": summary_title,
            "summary_text": summary_text,
            "weather": context.weather,
            "route": context.route,
            "transport": context.transport,
            "map_export": context.map_export,
            "attractions": context.attractions,
            "realtime": context.realtime,
            "risks": context.risks,
            "prompt": context.prompt,
        }
        snapshots["summary"]["result_json"] = result_json
        return TripPlanningResult(
            summary_title=summary_title,
            summary_text=summary_text,
            snapshots=snapshots,
            final_markdown=final_markdown,
            result_json=result_json,
            weather_summary=context.weather.get("weather_summary"),
            route_summary=context.route.get("route_summary"),
            attractions_summary=context.attractions.get("attractions_summary"),
            realtime_info_summary=context.realtime.get("realtime_info_summary"),
            risk_summary=risk_summary,
            amap_route_url=context.map_export.get("amap_route_url"),
            context=context,
        )

    async def build_external_context(
        self,
        *,
        record_id: int,
        request: GenerateStreamRequest,
    ) -> TripPlanningExternalContext:
        realtime_task = asyncio.create_task(
            self._safe_context(
                self._realtime_context(request),
                fallback=self._empty_realtime_context(),
                provider="realtime",
            )
        )
        weather = await self._safe_context(
            self._weather_context(request),
            fallback=self._empty_weather_context(request),
            provider="weather",
        )
        attractions = await self._safe_context(
            self._attractions_context(request),
            fallback=self._empty_attractions_context(request),
            provider="amap",
        )
        route = await self._safe_context(
            self._route_context(request),
            fallback=self._empty_route_context(request),
            provider="amap",
        )
        realtime = await realtime_task
        map_export = await self._map_export_context(
            record_id=record_id,
            request=request,
            route=route,
        )
        transport = self._transport_context(request=request, route=route)
        return TripPlanningExternalContext(
            weather=weather,
            route=route,
            transport=transport,
            map_export=map_export,
            attractions=attractions,
            realtime=realtime,
        )

    def build_context(
        self,
        request: GenerateStreamRequest,
        external: TripPlanningExternalContext | None = None,
    ) -> TripPlanningContext:
        external = external or TripPlanningExternalContext(
            weather=self._empty_weather_context(request),
            route=self._empty_route_context(request),
            transport=self._empty_transport_context(request),
            map_export=self._empty_map_export_context(),
            attractions=self._empty_attractions_context(request),
            realtime=self._empty_realtime_context(),
        )
        risks = self._risk_items(
            weather=external.weather,
            route=external.route,
            realtime=external.realtime,
        )
        return TripPlanningContext(
            request=request.model_dump(mode="json"),
            weather=external.weather,
            route=external.route,
            transport=external.transport,
            map_export=external.map_export,
            attractions=external.attractions,
            realtime=external.realtime,
            risks=risks,
            prompt=self.render_prompt(request, external=external),
        )

    def snapshot_for_stage(
        self,
        result: TripPlanningResult,
        stage: GenerationStage,
    ) -> tuple[str, dict[str, Any]] | None:
        if stage not in result.snapshots:
            return None
        return stage, result.snapshots[stage]

    def output_payload(self, result: TripPlanningResult) -> dict[str, Any]:
        return {
            "final_markdown": result.final_markdown,
            "result_json": result.result_json,
            "weather_summary": result.weather_summary,
            "route_summary": result.route_summary,
            "attractions_summary": result.attractions_summary,
            "realtime_info_summary": result.realtime_info_summary,
            "risk_summary": result.risk_summary,
            "amap_route_url": result.amap_route_url,
        }

    def render_prompt(
        self,
        request: GenerateStreamRequest,
        *,
        external: TripPlanningExternalContext | None = None,
    ) -> str:
        external = external or TripPlanningExternalContext(
            weather=self._empty_weather_context(request),
            route=self._empty_route_context(request),
            transport=self._empty_transport_context(request),
            map_export=self._empty_map_export_context(),
            attractions=self._empty_attractions_context(request),
            realtime=self._empty_realtime_context(),
        )
        return PROMPT_TEMPLATE.format(
            origin=request.origin,
            destination=request.destination,
            range_text=request.range,
            transport_mode=request.transport_mode,
            travel_date=request.travel_date.isoformat() if request.travel_date else "未指定",
            people_count=request.people_count or "未指定",
            preferences="、".join(request.preferences) or "无",
            avoidances="、".join(request.avoidances) or "无",
            weather_summary=external.weather.get("weather_summary", "暂无天气摘要"),
            route_summary=external.route.get("route_summary", "暂无路线摘要"),
            amap_route_url=external.map_export.get("amap_route_url", "暂无地图链接"),
            navigation_waypoint_summary=self._navigation_waypoint_summary(external),
            attractions_summary=external.attractions.get("attractions_summary", "暂无景点摘要"),
            realtime_summary=external.realtime.get("realtime_info_summary", "暂无实时信息摘要"),
        )

    async def _safe_context(
        self,
        awaitable: Any,
        *,
        fallback: dict[str, Any],
        provider: str,
    ) -> dict[str, Any]:
        try:
            return await awaitable
        except Exception as exc:
            return {
                **fallback,
                "provider": provider,
                "mock": False,
                "fallback_reason": str(exc),
                "source_updated_at": self._iso_now(),
            }

    async def _weather_context(self, request: GenerateStreamRequest) -> dict[str, Any]:
        city = await self._weather_city_name(request)
        return await self.weather_service.query_weather(
            city=city,
            weather_date=request.travel_date,
        )

    async def _route_context(
        self,
        request: GenerateStreamRequest,
    ) -> dict[str, Any]:
        base_route = await self._calculate_route(request, waypoints=[])
        waypoint_attractions = await self._safe_route_waypoint_attractions_context(
            request=request,
            route=base_route,
        )
        waypoint_candidates = self._route_waypoint_candidates(
            request,
            waypoint_attractions=waypoint_attractions,
            route=base_route,
        )
        route = base_route
        if waypoint_candidates:
            try:
                route = await self._calculate_route(request, waypoints=waypoint_candidates)
            except Exception as exc:
                route = {
                    **base_route,
                    "fallback_reason": self._append_fallback_reason(
                        base_route.get("fallback_reason"),
                        f"途径点路线计算失败：{exc}",
                    ),
                }
        route["recommended_waypoint_items"] = self._items_for_locations(
            waypoint_attractions,
            waypoint_candidates,
        )
        route["recommended_waypoint_source"] = (waypoint_attractions or {}).get("source")
        route["waypoint_search"] = self._waypoint_search_export(waypoint_attractions)
        return route

    async def _calculate_route(
        self,
        request: GenerateStreamRequest,
        *,
        waypoints: list[str],
    ) -> dict[str, Any]:
        return await self.amap_service.calculate_route(
            AmapRouteRequest(
                origin=request.origin,
                destination=request.destination,
                transport_mode=request.transport_mode,
                waypoints=waypoints,
            )
        )

    async def _safe_route_waypoint_attractions_context(
        self,
        *,
        request: GenerateStreamRequest,
        route: dict[str, Any],
    ) -> dict[str, Any]:
        if request.transport_mode not in {"driving", "mixed", "cycling", "motorcycle"}:
            return self._empty_route_waypoint_attractions_context(request)
        try:
            return await self._route_waypoint_attractions_context(request, route=route)
        except Exception as exc:
            return {
                **self._empty_route_waypoint_attractions_context(request),
                "provider": "amap",
                "fallback_reason": str(exc),
                "source_updated_at": self._iso_now(),
            }

    def _route_waypoint_candidates(
        self,
        request: GenerateStreamRequest,
        *,
        waypoint_attractions: dict[str, Any] | None,
        route: dict[str, Any] | None = None,
    ) -> list[str]:
        if request.transport_mode not in {"driving", "mixed", "cycling", "motorcycle"}:
            return []
        if not waypoint_attractions:
            return []
        return self._locations_from_attractions(
            waypoint_attractions,
            request=request,
            route=route,
        )

    async def _map_export_context(
        self,
        *,
        record_id: int,
        request: GenerateStreamRequest,
        route: dict[str, Any],
        waypoint_attractions: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        waypoint_attractions = waypoint_attractions or self._route_waypoint_search_from_route(route)
        origin_location = self._location_from_route(route, "origin")
        destination_location = self._location_from_route(route, "destination")
        route_waypoints = self._locations_from_route_waypoints(route)
        navigation_waypoints = self._navigation_waypoints(
            route=route,
            waypoint_attractions=waypoint_attractions,
            request=request,
        )
        navigation_waypoint_items = self._items_for_locations(
            waypoint_attractions,
            navigation_waypoints,
        )
        try:
            link = await self.amap_service.create_route_link(
                AmapRouteLinkRequest(
                    origin_name=request.origin,
                    origin=origin_location or request.origin,
                    destination_name=request.destination,
                    destination=destination_location or request.destination,
                    transport_mode=request.transport_mode,
                    waypoints=self._link_waypoints(
                        waypoint_items=navigation_waypoint_items,
                        waypoint_locations=navigation_waypoints,
                    ),
                )
            )
        except Exception as exc:
            link = {
                "amap_route_url": None,
                "provider": "amap",
                "mock": False,
                "fallback_reason": str(exc),
            }
        try:
            export = await self.amap_service.export_route_map(
                AmapExportRouteMapRequest(
                    record_id=record_id,
                    export_type="static",
                    origin=origin_location,
                    destination=destination_location,
                    waypoints=navigation_waypoints or route_waypoints,
                )
            )
        except Exception as exc:
            export = {
                **self._empty_map_export_context(),
                "provider": "amap",
                "mock": False,
                "fallback_reason": str(exc),
            }
        fallback_reasons = [
            item.get("fallback_reason")
            for item in [route, link, export]
            if item.get("fallback_reason")
        ]
        map_export = {
            **export,
            "amap_route_url": self._preferred_amap_route_url(
                link=link,
                export=export,
                waypoint_locations=navigation_waypoints,
            ),
            "route_snapshot_id": route.get("route_snapshot_id"),
            "navigation_waypoints": navigation_waypoints,
            "navigation_waypoint_items": navigation_waypoint_items,
            "route_waypoints": route_waypoints,
            "waypoint_search": self._waypoint_search_export(waypoint_attractions),
            "source_updated_at": self._iso_now(),
        }
        if fallback_reasons:
            map_export["fallback_reason"] = "；".join(dict.fromkeys(fallback_reasons))
        if map_export.get("amap_route_url") is None and origin_location and destination_location:
            map_export["amap_route_url"] = self._fallback_amap_route_url(
                origin=origin_location,
                destination=destination_location,
                transport_mode=request.transport_mode,
            )
        return map_export

    def _preferred_amap_route_url(
        self,
        *,
        link: dict[str, Any],
        export: dict[str, Any],
        waypoint_locations: list[str],
    ) -> str | None:
        link_url = link.get("amap_route_url")
        export_url = export.get("amap_route_url")
        if isinstance(link_url, str):
            return link_url
        if waypoint_locations and isinstance(export_url, str):
            return export_url
        return export_url if isinstance(export_url, str) else None

    def _navigation_waypoints(
        self,
        *,
        route: dict[str, Any],
        waypoint_attractions: dict[str, Any] | None,
        request: GenerateStreamRequest,
    ) -> list[str]:
        requested = route.get("requested_waypoints")
        if isinstance(requested, list):
            origin_location = self._location_from_route(route, "origin")
            destination_location = self._location_from_route(route, "destination")
            values = [
                item
                for item in requested
                if isinstance(item, str)
                and "," in item
                and not self._near_endpoint(item, origin_location, destination_location)
            ]
            if values:
                return values
        if waypoint_attractions:
            return self._locations_from_attractions(
                waypoint_attractions,
                request=request,
                route=route,
            )
        return []

    def _fallback_amap_route_url(
        self,
        *,
        origin: str,
        destination: str,
        transport_mode: str,
    ) -> str:
        from urllib.parse import urlencode

        mode = {
            "transit": "bus",
            "mixed": "bus",
            "walking": "walk",
            "cycling": "ride",
            "motorcycle": "ride",
        }.get(transport_mode, "car")
        return (
            "https://uri.amap.com/navigation?"
            f"{urlencode({'from': origin, 'to': destination, 'mode': mode, 'src': 'routecraft'})}"
        )

    def _transport_context(
        self,
        *,
        request: GenerateStreamRequest,
        route: dict[str, Any],
    ) -> dict[str, Any]:
        if request.transport_mode in {"transit", "mixed"}:
            summary = "公共交通与步行组合更稳妥，高峰时段建议提前出发。"
        elif request.transport_mode == "driving":
            summary = "驾车路线建议避开景区核心拥堵路段，预留停车时间。"
        elif request.transport_mode == "motorcycle":
            summary = "摩托车路线建议提前确认当地限行、禁摩路段和停车点。"
        else:
            summary = "按轻量步行节奏安排路线，必要时增加休息点。"
        return {
            "transport_mode": request.transport_mode,
            "transport_summary": summary,
            "segments": [
                {
                    "from": request.origin,
                    "to": request.destination,
                    "mode": request.transport_mode,
                    "duration_s": route.get("duration_s", 0),
                }
            ],
            "source_updated_at": self._iso_now(),
        }

    async def _attractions_context(self, request: GenerateStreamRequest) -> dict[str, Any]:
        data = await self.amap_service.search_places(
            keyword=request.destination,
            city=request.destination,
        )
        items = data.get("items") or []
        attractions = [
            {
                "name": item.get("name") or request.destination,
                "reason": item.get("type") or item.get("address") or "与目的地相关",
                "location": item.get("location"),
            }
            for item in items[:5]
            if isinstance(item, dict)
        ]
        if not attractions:
            attractions = [{"name": request.destination, "reason": "真实 POI 未返回可用结果"}]
        names = "、".join(item["name"] for item in attractions[:3])
        return {
            "attractions_summary": f"推荐关注{names}，并按现场人流调整停留时间。",
            "items": attractions,
            "provider": data.get("provider"),
            "mock": data.get("mock", False),
            "fallback_reason": data.get("fallback_reason"),
            "source_updated_at": data.get("source_updated_at") or self._iso_now(),
        }

    async def _route_waypoint_attractions_context(
        self,
        request: GenerateStreamRequest,
        *,
        route: dict[str, Any],
    ) -> dict[str, Any]:
        queries = self._route_waypoint_queries(request)
        results = []
        for query in queries:
            data = await self.amap_service.search_places(
                keyword=query,
                city=self._route_search_city(request, route=route),
            )
            results.append(
                {
                    "query": query,
                    "items": data.get("items") or [],
                    "source": "amap_poi",
                    "provider": data.get("provider"),
                    "mock": data.get("mock", False),
                    "fallback_reason": data.get("fallback_reason"),
                    "source_updated_at": data.get("source_updated_at"),
                }
            )
        web_result = await self._route_web_waypoint_query_result(request=request, route=route)
        if web_result is not None:
            results.append(web_result)

        candidates = self._route_waypoint_items(
            request=request,
            query_results=results,
            route=route,
        )
        names = "、".join(item["name"] for item in candidates[:3])
        summary = (
            f"沿{request.origin}至{request.destination}方向推荐途径{names}。"
            if names
            else f"暂未检索到{request.origin}至{request.destination}明确沿途景点。"
        )
        fallback_reasons = [
            result.get("fallback_reason")
            for result in results
            if result.get("fallback_reason")
        ]
        return {
            "attractions_summary": summary,
            "items": candidates,
            "source": "route_waypoint_search",
            "queries": queries,
            "source_types": self._waypoint_source_types(results),
            "provider": self._provider_for(results),
            "mock": bool(results) and all(result.get("mock", False) for result in results),
            "fallback_reason": "；".join(dict.fromkeys(fallback_reasons))
            if fallback_reasons
            else None,
            "source_updated_at": self._latest_source_updated_at(results),
        }

    async def _route_web_waypoint_query_result(
        self,
        *,
        request: GenerateStreamRequest,
        route: dict[str, Any],
    ) -> dict[str, Any] | None:
        query = self._route_web_waypoint_query(request)
        if not query:
            return None
        try:
            data = await self.realtime_service.search(
                keyword=query,
                category="guide",
                limit=5,
            )
        except Exception as exc:
            return {
                "query": query,
                "items": [],
                "source": "web_search",
                "provider": "realtime",
                "mock": False,
                "fallback_reason": f"全网途径点搜索失败：{exc}",
                "source_updated_at": self._iso_now(),
            }

        items = await self._resolve_web_waypoint_items(
            request=request,
            route=route,
            query=query,
            web_items=[
                item for item in data.get("items") or [] if isinstance(item, dict)
            ],
        )
        return {
            "query": query,
            "items": items,
            "source": "web_search",
            "provider": data.get("provider"),
            "mock": data.get("mock", False),
            "fallback_reason": data.get("fallback_reason"),
            "source_updated_at": data.get("source_updated_at") or self._iso_now(),
        }

    async def _resolve_web_waypoint_items(
        self,
        *,
        request: GenerateStreamRequest,
        route: dict[str, Any],
        query: str,
        web_items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        origin = request.origin.strip()
        destination = request.destination.strip()
        origin_location = self._location_from_route(route, "origin")
        destination_location = self._location_from_route(route, "destination")
        endpoint_threshold = self._endpoint_exclusion_radius(route)
        resolved: list[dict[str, Any]] = []
        seen_locations: set[str] = set()
        city = self._route_search_city(request, route=route)
        for candidate in self._web_waypoint_candidates(
            request=request,
            web_items=web_items,
        ):
            data = await self.amap_service.search_places(keyword=candidate["name"], city=city)
            for poi in data.get("items") or []:
                if not isinstance(poi, dict):
                    continue
                name = str(poi.get("name") or candidate["name"]).strip()
                location = poi.get("location")
                if not isinstance(location, str) or "," not in location:
                    continue
                if location in seen_locations:
                    continue
                if self._poi_matches_endpoint(name, origin=origin, destination=destination):
                    continue
                if self._near_endpoint(
                    location,
                    origin_location,
                    destination_location,
                    threshold=endpoint_threshold,
                ):
                    continue
                if not self._is_route_waypoint_poi(poi, query=query):
                    continue
                seen_locations.add(location)
                resolved.append(
                    {
                        "name": name or candidate["name"],
                        "reason": candidate.get("reason")
                        or poi.get("type")
                        or poi.get("address")
                        or "全网搜索推荐途径点",
                        "location": location,
                        "address": poi.get("address"),
                        "type": poi.get("type") or "全网搜索途径点",
                        "source": "web_search",
                        "source_query": query,
                        "source_title": candidate.get("source_title"),
                        "source_url": candidate.get("source_url"),
                        "source_site": candidate.get("source_site"),
                    }
                )
                break
            if len(resolved) >= 5:
                break
        return resolved

    def _route_web_waypoint_query(self, request: GenerateStreamRequest) -> str:
        parts = [
            request.origin.strip(),
            "到",
            request.destination.strip(),
            "沿途必经途径点 景点 公园 博物馆 观景台 顺路",
        ]
        if request.preferences:
            parts.append(" ".join(request.preferences[:3]))
        if request.avoidances:
            parts.append("避开 " + " ".join(request.avoidances[:2]))
        return " ".join(part for part in parts if part).strip()

    def _web_waypoint_candidates(
        self,
        *,
        request: GenerateStreamRequest,
        web_items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        seen_names: set[str] = set()
        for item in web_items:
            source_title = str(item.get("title") or "").strip()
            source_url = item.get("url")
            source_site = item.get("source")
            names = self._structured_web_waypoint_names(item)
            if not names:
                names = self._waypoint_names_from_text(
                    " ".join(
                        str(value or "")
                        for value in [item.get("title"), item.get("summary")]
                    ),
                    request=request,
                )
            for name in names:
                normalized = self._clean_waypoint_name(name)
                if not normalized or normalized in seen_names:
                    continue
                if self._poi_matches_endpoint(
                    normalized,
                    origin=request.origin.strip(),
                    destination=request.destination.strip(),
                ):
                    continue
                seen_names.add(normalized)
                candidates.append(
                    {
                        "name": normalized,
                        "reason": item.get("summary") or "全网搜索推荐途径点",
                        "source_title": source_title,
                        "source_url": source_url,
                        "source_site": source_site,
                    }
                )
                if len(candidates) >= 8:
                    return candidates
        return candidates

    def _structured_web_waypoint_names(self, item: dict[str, Any]) -> list[str]:
        raw = item.get("raw")
        if not isinstance(raw, dict):
            return []
        names: list[str] = []
        for key in ("waypoint_candidates", "waypoints", "pois", "attractions"):
            value = raw.get(key)
            if not isinstance(value, list):
                continue
            for entry in value:
                if isinstance(entry, str):
                    names.append(entry)
                elif isinstance(entry, dict):
                    names.append(str(entry.get("name") or ""))
        return names

    def _waypoint_names_from_text(
        self,
        text: str,
        *,
        request: GenerateStreamRequest,
    ) -> list[str]:
        if not text.strip():
            return []
        names: list[str] = []
        suffix_pattern = (
            r"[\u4e00-\u9fffA-Za-z0-9·-]{2,24}"
            r"(?:景区|公园|博物馆|纪念馆|湿地|古镇|古村|广场|观景台|文化园|风景区)"
            r"(?:外围|周边|附近|一带|沿线)?"
        )
        route_place_pattern = (
            r"[\u4e00-\u9fffA-Za-z0-9·-]{2,18}"
            r"(?:环湖段|江北新区|新区|县|镇|古镇|湖|山|岛|河|岸|岭|湾|洲|村)"
            r"(?:外围|周边|附近|一带|沿线)?"
        )
        for match in re.finditer(f"{suffix_pattern}|{route_place_pattern}", text):
            names.append(match.group(0))
        for chunk in re.split(r"[：:、，,；;|/()\[\]【】\n\r]|(?:\s*(?:→|->|－|—|–)\s*)", text):
            normalized = self._clean_waypoint_name(chunk)
            if normalized and len(normalized) <= 20:
                names.append(normalized)

        blocked = {
            request.origin.strip(),
            request.destination.strip(),
            "沿途景点",
            "途径景点",
            "必经景点",
            "推荐景点",
        }
        route_words = (
            "路线",
            "攻略",
            "推荐",
            "沿途",
            "途经",
            "途径",
            "起点",
            "终点",
            "出发",
            "高德",
            "百度",
            "地图",
            "导航",
            "高速",
            "国道",
            "省道",
            "县道",
            "限行",
            "禁行",
            "停车",
            "补给",
            "休整",
            "注意事项",
            "通行规则",
            "Mock",
            "摘要",
            "相关",
            "提醒",
            "参考",
        )
        result = []
        for name in names:
            if name in blocked:
                continue
            if self._poi_matches_endpoint(
                name,
                origin=request.origin.strip(),
                destination=request.destination.strip(),
            ):
                continue
            if any(word in name for word in route_words):
                continue
            if not self._looks_like_waypoint_name(name):
                continue
            if name not in result:
                result.append(name)
        return result[:8]

    def _clean_waypoint_name(self, value: Any) -> str:
        if not isinstance(value, str):
            return ""
        value = value.strip()
        value = re.sub(r"^[\s\d.、:：-]+|[\s.。；;，,]+$", "", value)
        value = re.sub(
            r"^(?:可安排|安排|推荐|建议|可先|先到|再到|继续|经过|路过|绕行|走)\s*",
            "",
            value,
        )
        value = re.sub(r"(?:作为短暂停留点|作为停靠点|短暂停留|拍照|补水|休整)$", "", value)
        value = re.sub(r"(?:外围|周边|附近|一带|沿线)$", "", value)
        return value.strip()

    def _route_waypoint_queries(self, request: GenerateStreamRequest) -> list[str]:
        origin = request.origin.strip()
        destination = request.destination.strip()
        preference_text = " ".join(request.preferences[:3]).strip()
        base_queries = [
            f"{origin} 到 {destination} 沿途景点",
            f"{origin} {destination} 途径景点",
            f"{origin} {destination} 景点",
        ]
        if preference_text:
            base_queries.insert(1, f"{origin} 到 {destination} {preference_text} 景点")
        return list(dict.fromkeys(query for query in base_queries if query.strip()))[:4]

    def _route_search_city(
        self,
        request: GenerateStreamRequest,
        *,
        route: dict[str, Any] | None = None,
    ) -> str | None:
        if route is not None and self._is_long_distance_route(route):
            return None
        destination = request.destination.strip()
        city = self._city_token(destination)
        return city or destination or None

    def _city_token(self, value: str) -> str:
        for token in re.split(r"[\s,/，、]+", value.strip()):
            token = token.strip()
            if token.endswith(("市", "县", "区", "州", "盟")) and len(token) >= 2:
                return token
        match = re.search(r"[\u4e00-\u9fff]{2,8}市", value)
        return match.group(0) if match else ""

    def _route_waypoint_items(
        self,
        *,
        request: GenerateStreamRequest,
        query_results: list[dict[str, Any]],
        route: dict[str, Any],
    ) -> list[dict[str, Any]]:
        origin = request.origin.strip()
        destination = request.destination.strip()
        origin_location = self._location_from_route(route, "origin")
        destination_location = self._location_from_route(route, "destination")
        endpoint_threshold = self._endpoint_exclusion_radius(route)
        items: list[dict[str, Any]] = []
        seen_locations: set[str] = set()
        for result in self._ordered_waypoint_query_results(query_results):
            query = str(result.get("query") or "")
            for raw in result.get("items") or []:
                if not isinstance(raw, dict):
                    continue
                name = str(raw.get("name") or "").strip()
                location = raw.get("location")
                if not isinstance(location, str) or "," not in location:
                    continue
                if location in seen_locations:
                    continue
                if not self._is_route_waypoint_poi(raw, query=query):
                    continue
                if self._poi_matches_endpoint(name, origin=origin, destination=destination):
                    continue
                if self._is_destination_city_poi(
                    raw,
                    request=request,
                    route=route,
                    source=str(result.get("source") or ""),
                ):
                    continue
                if self._near_endpoint(
                    location,
                    origin_location,
                    destination_location,
                    threshold=endpoint_threshold,
                ):
                    continue
                seen_locations.add(location)
                items.append(
                    {
                        "name": name or "沿途景点",
                        "reason": raw.get("type") or raw.get("address") or "沿途景点搜索结果",
                        "location": location,
                        "address": raw.get("address"),
                        "type": raw.get("type"),
                        "source": raw.get("source") or result.get("source") or "amap_poi",
                        "source_query": query,
                        "source_title": raw.get("source_title"),
                        "source_url": raw.get("source_url"),
                        "source_site": raw.get("source_site"),
                    }
                )
                if len(items) >= 5:
                    return items
        return items

    def _ordered_waypoint_query_results(
        self,
        query_results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return sorted(
            query_results,
            key=lambda item: 0 if item.get("source") == "web_search" else 1,
        )

    def _waypoint_source_types(self, results: list[dict[str, Any]]) -> list[str]:
        values = [
            str(result.get("source"))
            for result in results
            if isinstance(result.get("source"), str) and result.get("source")
        ]
        return list(dict.fromkeys(values))

    def _is_route_waypoint_poi(self, item: dict[str, Any], *, query: str) -> bool:
        text = " ".join(str(item.get(key) or "") for key in ("name", "type", "address"))
        excluded_tokens = (
            "停车场",
            "出入口",
            "入口",
            "出口",
            "收费站",
            "服务区",
            "加油站",
            "充电站",
            "厕所",
            "卫生间",
            "售票处",
        )
        if any(token in text for token in excluded_tokens):
            return False
        scenic_tokens = (
            "风景名胜",
            "景点",
            "景区",
            "公园",
            "博物馆",
            "纪念馆",
            "湿地",
            "古镇",
            "古村",
            "文化",
            "旅游",
            "游览",
            "沿途",
            "途经",
            "途径",
        )
        return any(token in text or token in query for token in scenic_tokens)

    def _poi_matches_endpoint(
        self,
        name: str,
        *,
        origin: str,
        destination: str,
    ) -> bool:
        if not name:
            return False
        if name in {origin, destination}:
            return True
        for endpoint in [origin, destination]:
            if not self._is_specific_endpoint_name(endpoint):
                continue
            if endpoint in name:
                return True
            if len(name) >= 3 and name in endpoint:
                return True
        return False

    def _is_specific_endpoint_name(self, value: str) -> bool:
        value = value.strip()
        if len(value) < 4:
            return False
        return not value.endswith(("省", "市", "县", "区", "州", "盟"))

    def _looks_like_waypoint_name(self, name: str) -> bool:
        if len(name) < 2 or len(name) > 18:
            return False
        if not re.search(r"[\u4e00-\u9fff]", name):
            return False
        blocked_parts = (
            "早上",
            "中午",
            "下午",
            "晚上",
            "一天",
            "小时",
            "公里",
            "避开",
            "确认",
            "提前",
            "再次",
            "优先",
            "适合",
            "不要",
            "不必",
        )
        return not any(part in name for part in blocked_parts)

    def _is_destination_city_poi(
        self,
        item: dict[str, Any],
        *,
        request: GenerateStreamRequest,
        route: dict[str, Any],
        source: str,
    ) -> bool:
        if source == "web_search" or not self._is_long_distance_route(route):
            return False
        destination_city_tokens = self._destination_city_tokens(request.destination)
        if not destination_city_tokens:
            return False
        text = " ".join(
            str(item.get(key) or "")
            for key in ("name", "address", "city_name", "adname", "province_name")
        )
        return any(token and token in text for token in destination_city_tokens)

    def _destination_city_tokens(self, destination: str) -> list[str]:
        destination = destination.strip()
        city = self._city_token(destination)
        tokens = [city] if city else []
        if re.fullmatch(r"[\u4e00-\u9fff]{2,4}", destination):
            tokens.extend([destination, f"{destination}市"])
        return list(dict.fromkeys(token for token in tokens if token))

    def _is_long_distance_route(self, route: dict[str, Any]) -> bool:
        distance_m = route.get("distance_m")
        if isinstance(distance_m, int | float) and distance_m >= 80_000:
            return True
        origin_location = self._location_from_route(route, "origin")
        destination_location = self._location_from_route(route, "destination")
        if origin_location and destination_location:
            return self._coordinate_distance(origin_location, destination_location) >= 0.7
        return False

    def _endpoint_exclusion_radius(self, route: dict[str, Any] | None) -> float:
        if route is not None and self._is_long_distance_route(route):
            return 0.12
        return 0.003

    async def _realtime_context(self, request: GenerateStreamRequest) -> dict[str, Any]:
        keyword = f"{request.destination} {request.range}".strip()
        categories: list[RealtimeCategory] = ["news", "traffic", "guide", "pitfall"]
        try:
            news, traffic, guide, pitfall = await asyncio.gather(
                *[
                    self.realtime_service.search(keyword=keyword, category=category, limit=3)
                    for category in categories
                ]
            )
        except Exception:
            raise
        news_traffic = [*news.get("items", []), *traffic.get("items", [])]
        guide_pitfall = [*guide.get("items", []), *pitfall.get("items", [])]
        fallback_reasons = [
            item.get("fallback_reason")
            for item in [news, traffic, guide, pitfall]
            if item.get("fallback_reason")
        ]
        return {
            "news_traffic": news_traffic,
            "guide_pitfall": guide_pitfall,
            "realtime_info_summary": self._realtime_markdown_summary(
                [
                    ("新闻资讯", news),
                    ("交通管制", traffic),
                    ("攻略参考", guide),
                    ("避坑参考", pitfall),
                ]
            ),
            "provider": self._provider_for([news, traffic, guide, pitfall]),
            "mock": all(item.get("mock", False) for item in [news, traffic, guide, pitfall]),
            "fallback_reason": "；".join(dict.fromkeys(fallback_reasons))
            if fallback_reasons
            else None,
            "source_updated_at": self._latest_source_updated_at([news, traffic, guide, pitfall]),
        }

    async def _weather_city_name(self, request: GenerateStreamRequest) -> str:
        destination = request.destination.strip()
        if len([part for part in destination.replace("/", " ").split() if part]) >= 3:
            return destination
        try:
            data = await self.amap_service.search_places(
                keyword=destination,
                city=destination,
            )
        except Exception:
            return destination
        for item in data.get("items") or []:
            if not isinstance(item, dict):
                continue
            province_name = str(item.get("province_name") or "").strip()
            city_name = str(item.get("city_name") or "").strip()
            adname = str(item.get("adname") or "").strip()
            if province_name and city_name and adname:
                return f"{province_name} {city_name} {adname}"
            if city_name:
                return city_name
        return destination

    def _empty_weather_context(self, request: GenerateStreamRequest) -> dict[str, Any]:
        return {
            "city_name": request.destination,
            "weather_date": request.travel_date.isoformat() if request.travel_date else None,
            "alert_level": "none",
            "weather_summary": "未提供天气上下文。",
            "alerts": [],
            "source_updated_at": self._iso_now(),
            "provider": "none",
            "mock": False,
        }

    def _empty_route_context(self, request: GenerateStreamRequest) -> dict[str, Any]:
        return {
            "origin": request.origin,
            "destination": request.destination,
            "transport_mode": request.transport_mode,
            "distance_m": 0,
            "duration_s": 0,
            "route_summary": "未提供路线上下文。",
            "waypoints": [
                {"name": request.origin, "type": "origin"},
                {"name": request.destination, "type": "destination"},
            ],
            "source_updated_at": self._iso_now(),
            "provider": "none",
            "mock": False,
        }

    def _empty_transport_context(self, request: GenerateStreamRequest) -> dict[str, Any]:
        return {
            "transport_mode": request.transport_mode,
            "transport_summary": "未提供交通上下文。",
            "segments": [
                {
                    "from": request.origin,
                    "to": request.destination,
                    "mode": request.transport_mode,
                    "duration_s": 0,
                }
            ],
            "source_updated_at": self._iso_now(),
        }

    def _empty_map_export_context(self) -> dict[str, Any]:
        return {
            "amap_route_url": None,
            "export_type": "none",
            "image_url": None,
            "status": "not_requested",
            "source_updated_at": self._iso_now(),
        }

    def _empty_attractions_context(self, request: GenerateStreamRequest) -> dict[str, Any]:
        return {
            "attractions_summary": f"未提供{request.destination}景点上下文。",
            "items": [{"name": request.destination, "reason": "用户指定目的地"}],
            "source_updated_at": self._iso_now(),
            "provider": "none",
            "mock": False,
        }

    def _empty_route_waypoint_attractions_context(
        self,
        request: GenerateStreamRequest,
    ) -> dict[str, Any]:
        return {
            "attractions_summary": (
                f"未提供{request.origin}至{request.destination}沿途景点上下文。"
            ),
            "items": [],
            "source": "route_waypoint_search",
            "queries": [],
            "source_updated_at": self._iso_now(),
            "provider": "none",
            "mock": False,
        }

    def _empty_realtime_context(self) -> dict[str, Any]:
        return {
            "news_traffic": [],
            "guide_pitfall": [],
            "realtime_info_summary": "1. 未提供实时检索上下文。",
            "source_updated_at": self._iso_now(),
            "provider": "none",
            "mock": False,
        }

    def _summary_text(self, context: TripPlanningContext) -> str:
        if context.route.get("route_summary"):
            return f"{context.route['route_summary']}。建议结合天气、实时信息和现场人流动态调整。"
        return "建议按天气、交通和兴趣点顺序执行，并保留弹性时间。"

    def _risk_items(
        self,
        *,
        weather: dict[str, Any],
        route: dict[str, Any],
        realtime: dict[str, Any],
    ) -> list[str]:
        risks = ["出行前复核天气、交通管制和地图导航信息"]
        if weather.get("alert_level") and weather["alert_level"] != "none":
            risks.append("存在天气预警，需准备室内替代方案")
        if route.get("duration_s", 0) > 3600:
            risks.append("路线耗时较长，建议预留缓冲时间")
        if realtime.get("news_traffic"):
            risks.append("热门区域建议错峰进入")
        if (
            weather.get("fallback_reason")
            or route.get("fallback_reason")
            or realtime.get("fallback_reason")
        ):
            risks.append("部分外部数据已降级，需人工复核最新信息")
        return risks

    def _final_markdown(
        self,
        *,
        summary_title: str,
        summary_text: str,
        context: TripPlanningContext,
        risk_summary: str,
    ) -> str:
        route_link = context.map_export.get("amap_route_url")
        lines = [
            f"## {summary_title}",
            "",
            summary_text,
            "",
            "### 天气与风险",
            context.weather.get("weather_summary", "暂无天气摘要"),
            risk_summary,
            "",
            "### 路线与交通",
            context.route.get("route_summary", "暂无路线摘要"),
            context.transport.get("transport_summary", "暂无交通摘要"),
        ]
        if route_link:
            lines.append(f"高德路线：{route_link}")
        waypoint_summary = self._navigation_waypoint_summary(context)
        if waypoint_summary != "暂无明确导航途径点。":
            lines.append(f"导航途径点：{waypoint_summary}")
        lines.extend(
            [
                "",
                "### 途径景点",
                context.attractions.get("attractions_summary", "暂无景点摘要"),
                "",
                "### 实时信息",
                context.realtime.get("realtime_info_summary", "暂无实时信息摘要"),
            ]
        )
        return "\n".join(lines)

    def _realtime_markdown_summary(self, sections: list[tuple[str, dict[str, Any]]]) -> str:
        items: list[str] = []
        for label, data in sections:
            summary = self._realtime_section_summary(label=label, data=data)
            if summary:
                items.append(summary)
        if not items:
            items.append("暂未检索到实时信息，建议出行前再次复核。")
        return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))

    def _realtime_section_summary(self, *, label: str, data: dict[str, Any]) -> str:
        summary = self._clean_realtime_summary(data.get("realtime_info_summary"))
        items = [item for item in data.get("items") or [] if isinstance(item, dict)]
        if not items:
            return summary

        titles = [
            escape_html(str(item.get("title") or "").strip(), quote=False)
            for item in items[:3]
            if str(item.get("title") or "").strip()
        ]
        sources = [
            escape_html(str(item.get("source") or "").strip(), quote=False)
            for item in items[:3]
            if str(item.get("source") or "").strip()
        ]
        if titles:
            text = f"{label}：重点关注{'；'.join(titles)}。"
        else:
            text = f"{label}：{summary or '已检索到相关信息，出行前建议复核。'}"
        if sources:
            text += f" 来源：{'、'.join(dict.fromkeys(sources))}。"
        return text

    def _clean_realtime_summary(self, value: Any) -> str:
        if not isinstance(value, str):
            return ""
        return escape_html(" ".join(value.strip().split()), quote=False)

    def _provider_for(self, items: list[dict[str, Any]]) -> str:
        providers = {item.get("provider") for item in items if item.get("provider")}
        if len(providers) == 1:
            return str(next(iter(providers)))
        return "mixed" if providers else "none"

    def _latest_source_updated_at(self, items: list[dict[str, Any]]) -> str:
        values = [item.get("source_updated_at") for item in items if item.get("source_updated_at")]
        return str(max(values)) if values else self._iso_now()

    def _location_from_route(self, route: dict[str, Any], key: str) -> str | None:
        value = route.get(f"{key}_location") or route.get(key)
        if value is None:
            raw = route.get("raw")
            if isinstance(raw, dict):
                value = raw.get(key)
        return value if isinstance(value, str) and "," in value else None

    def _locations_from_route_waypoints(self, route: dict[str, Any]) -> list[str]:
        locations = []
        for waypoint in route.get("waypoints") or []:
            if isinstance(waypoint, str) and "," in waypoint:
                locations.append(waypoint)
            elif isinstance(waypoint, dict):
                location = waypoint.get("location")
                if isinstance(location, str) and "," in location:
                    locations.append(location)
        if not locations:
            raw = route.get("raw")
            if isinstance(raw, dict):
                for waypoint in raw.get("waypoints") or []:
                    if isinstance(waypoint, str) and "," in waypoint:
                        locations.append(waypoint)
        return locations

    def _items_for_locations(
        self,
        attractions: dict[str, Any] | None,
        locations: list[str],
    ) -> list[dict[str, Any]]:
        if not attractions or not locations:
            return []
        by_location = {
            item.get("location"): item
            for item in attractions.get("items") or []
            if isinstance(item, dict) and isinstance(item.get("location"), str)
        }
        items = []
        for location in locations:
            item = by_location.get(location)
            if not item:
                continue
            items.append(
                {
                    "name": item.get("name") or "途径点",
                    "location": location,
                    "reason": item.get("reason"),
                    "address": item.get("address"),
                    "type": item.get("type"),
                    "source": item.get("source"),
                    "source_query": item.get("source_query"),
                    "source_title": item.get("source_title"),
                    "source_url": item.get("source_url"),
                    "source_site": item.get("source_site"),
                }
            )
        return items

    def _link_waypoints(
        self,
        *,
        waypoint_items: list[dict[str, Any]],
        waypoint_locations: list[str],
    ) -> list[Any]:
        if waypoint_items:
            return [
                {
                    "name": str(item.get("name") or ""),
                    "location": str(item.get("location") or ""),
                }
                for item in waypoint_items
                if isinstance(item.get("location"), str)
            ]
        return waypoint_locations

    def _waypoint_search_export(
        self,
        waypoint_attractions: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if not waypoint_attractions:
            return {
                "source": "none",
                "queries": [],
                "items": [],
            }
        return {
            "source": waypoint_attractions.get("source") or "route_waypoint_search",
            "queries": waypoint_attractions.get("queries") or [],
            "items": waypoint_attractions.get("items") or [],
            "source_types": waypoint_attractions.get("source_types") or [],
            "provider": waypoint_attractions.get("provider"),
            "mock": waypoint_attractions.get("mock", False),
            "fallback_reason": waypoint_attractions.get("fallback_reason"),
            "source_updated_at": waypoint_attractions.get("source_updated_at"),
        }

    def _navigation_waypoint_summary(
        self,
        external_or_context: TripPlanningExternalContext | TripPlanningContext,
    ) -> str:
        map_export = external_or_context.map_export
        route = external_or_context.route
        items = map_export.get("navigation_waypoint_items") or route.get(
            "recommended_waypoint_items"
        ) or []
        names = [
            self._waypoint_display_text(item)
            for item in items
            if isinstance(item, dict) and item.get("name")
        ]
        if names:
            return "、".join(names[:5]) + "。"
        locations = map_export.get("navigation_waypoints") or route.get("requested_waypoints") or []
        if locations:
            return "、".join(str(item) for item in locations[:5]) + "。"
        return "暂无明确导航途径点。"

    def _waypoint_display_text(self, item: dict[str, Any]) -> str:
        name = str(item.get("name") or "途径点")
        source = item.get("source")
        if source == "web_search":
            return f"{name}（全网）"
        if source == "amap_poi":
            return f"{name}（高德）"
        return name

    def _route_waypoint_search_from_route(self, route: dict[str, Any]) -> dict[str, Any] | None:
        value = route.get("waypoint_search")
        return value if isinstance(value, dict) else None

    def _append_fallback_reason(self, current: Any, message: str) -> str:
        values = [value for value in [current, message] if isinstance(value, str) and value]
        return "；".join(dict.fromkeys(values))

    def _locations_from_attractions(
        self,
        attractions: dict[str, Any],
        *,
        request: GenerateStreamRequest,
        route: dict[str, Any] | None = None,
    ) -> list[str]:
        origin = request.origin.strip()
        destination = request.destination.strip()
        origin_location = self._location_from_route(route or {}, "origin")
        destination_location = self._location_from_route(route or {}, "destination")
        endpoint_threshold = self._endpoint_exclusion_radius(route or {})
        locations: list[str] = []
        seen: set[str] = set()
        for item in attractions.get("items") or []:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            location = item.get("location")
            if not isinstance(location, str) or "," not in location:
                continue
            if name and name in {origin, destination}:
                continue
            if self._near_endpoint(
                location,
                origin_location,
                destination_location,
                threshold=endpoint_threshold,
            ):
                continue
            if location in seen:
                continue
            seen.add(location)
            locations.append(location)
        return locations[:5]

    def _near_endpoint(
        self,
        location: str,
        origin_location: str | None,
        destination_location: str | None,
        *,
        threshold: float = 0.003,
    ) -> bool:
        return any(
            endpoint is not None and self._coordinate_distance(location, endpoint) < threshold
            for endpoint in [origin_location, destination_location]
        )

    def _coordinate_distance(self, left: str, right: str) -> float:
        try:
            left_lng, left_lat = (float(value) for value in left.split(",", 1))
            right_lng, right_lat = (float(value) for value in right.split(",", 1))
        except ValueError:
            return 999
        return ((left_lng - right_lng) ** 2 + (left_lat - right_lat) ** 2) ** 0.5

    def _iso_now(self) -> str:
        return datetime.now(APP_TZ).isoformat()
