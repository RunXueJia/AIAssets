import asyncio
from datetime import datetime, timedelta, timezone
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
- 景点：{attractions_summary}
- 实时信息：{realtime_summary}

输出要求：
1. 先给天气与风险提示。
2. 给出路径点规划、公共交通或驾车建议。
3. 给出途径景点说明。
4. 给出实时信息来源摘要。
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
        weather_task = self._weather_context(request)
        route_task = self._route_context(request)
        attractions_task = self._attractions_context(request)
        realtime_task = self._realtime_context(request)
        weather, route, attractions, realtime = await asyncio.gather(
            weather_task,
            route_task,
            attractions_task,
            realtime_task,
        )
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
            attractions_summary=external.attractions.get("attractions_summary", "暂无景点摘要"),
            realtime_summary=external.realtime.get("realtime_info_summary", "暂无实时信息摘要"),
        )

    async def _weather_context(self, request: GenerateStreamRequest) -> dict[str, Any]:
        city = await self._weather_city_name(request)
        return await self.weather_service.query_weather(
            city=city,
            weather_date=request.travel_date,
        )

    async def _route_context(self, request: GenerateStreamRequest) -> dict[str, Any]:
        return await self.amap_service.calculate_route(
            AmapRouteRequest(
                origin=request.origin,
                destination=request.destination,
                transport_mode=request.transport_mode,
                waypoints=[],
            )
        )

    async def _map_export_context(
        self,
        *,
        record_id: int,
        request: GenerateStreamRequest,
        route: dict[str, Any],
    ) -> dict[str, Any]:
        link = await self.amap_service.create_route_link(
            AmapRouteLinkRequest(
                origin_name=request.origin,
                origin=request.origin,
                destination_name=request.destination,
                destination=request.destination,
                transport_mode=request.transport_mode,
            )
        )
        export = await self.amap_service.export_route_map(
            AmapExportRouteMapRequest(
                record_id=record_id,
                export_type="static",
                origin=self._location_from_route(route, "origin"),
                destination=self._location_from_route(route, "destination"),
                waypoints=self._locations_from_route_waypoints(route),
            )
        )
        return {
            **export,
            "amap_route_url": link.get("amap_route_url") or export.get("amap_route_url"),
            "route_snapshot_id": route.get("route_snapshot_id"),
            "source_updated_at": self._iso_now(),
        }

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
        summaries = [
            item.get("realtime_info_summary")
            for item in [news, traffic, guide, pitfall]
            if item.get("realtime_info_summary")
        ]
        fallback_reasons = [
            item.get("fallback_reason")
            for item in [news, traffic, guide, pitfall]
            if item.get("fallback_reason")
        ]
        return {
            "news_traffic": news_traffic,
            "guide_pitfall": guide_pitfall,
            "realtime_info_summary": " ".join(summaries),
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

    def _empty_realtime_context(self) -> dict[str, Any]:
        return {
            "news_traffic": [],
            "guide_pitfall": [],
            "realtime_info_summary": "未提供实时检索上下文。",
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
        if weather.get("fallback_reason") or realtime.get("fallback_reason"):
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
        return locations

    def _iso_now(self) -> str:
        return datetime.now(APP_TZ).isoformat()
