import asyncio
from datetime import date

from app.integrations.amap import MockAmapClient
from app.integrations.realtime import MockRealtimeClient
from app.integrations.weather import MockWeatherClient
from app.schemas.generation import GenerateStreamRequest
from app.services.ai_planning import AiPlanningService
from app.services.amap import AmapService
from app.services.realtime import RealtimeService
from app.services.weather import WeatherService


class WaypointAmapClient(MockAmapClient):
    def __init__(self) -> None:
        super().__init__()
        self.route_waypoints: list[str] = []
        self.link_waypoints: list[str] = []

    async def search_places(self, *, keyword: str, city: str | None = None):
        if keyword == "西湖景区":
            return {
                "items": [
                    {
                        "name": "断桥残雪",
                        "address": "杭州西湖",
                        "location": "120.149000,30.260000",
                        "type": "风景名胜",
                        "province_name": "浙江省",
                        "city_name": "杭州市",
                        "adname": "西湖区",
                    },
                    {
                        "name": "苏堤春晓",
                        "address": "杭州西湖",
                        "location": "120.145000,30.245000",
                        "type": "风景名胜",
                        "province_name": "浙江省",
                        "city_name": "杭州市",
                        "adname": "西湖区",
                    },
                ],
                "source_updated_at": "2026-05-22T10:00:00+08:00",
                "mock": True,
                "provider": self.provider,
            }
        return await super().search_places(keyword=keyword, city=city)

    async def calculate_route(self, *, waypoints: list[str], **kwargs):
        self.route_waypoints = waypoints
        data = await super().calculate_route(waypoints=waypoints, **kwargs)
        data["origin_location"] = "120.21201,30.29191"
        data["destination_location"] = "120.143222,30.236064"
        data["waypoints"] = waypoints
        return data

    async def create_route_link(self, *, waypoints: list[str] | None = None, **kwargs):
        self.link_waypoints = waypoints or []
        return await super().create_route_link(waypoints=waypoints, **kwargs)


class FailingAmapClient(MockAmapClient):
    async def calculate_route(self, **_kwargs):  # noqa: ANN003
        raise RuntimeError("RESULTS_ARE_EMPTY")

    async def create_route_link(self, **_kwargs):  # noqa: ANN003
        raise RuntimeError("RESULTS_ARE_EMPTY")


def _service() -> AiPlanningService:
    return AiPlanningService(
        weather_service=WeatherService(client=MockWeatherClient()),
        amap_service=AmapService(client=MockAmapClient()),
        realtime_service=RealtimeService(client=MockRealtimeClient()),
    )


def test_ai_planning_builds_prompt_context_and_result() -> None:
    service = _service()
    request = GenerateStreamRequest(
        origin="杭州东站",
        destination="西湖景区",
        range="一天，步行少一点",
        transport_mode="mixed",
        travel_date=date(2026, 6, 1),
        people_count=2,
        preferences=["自然风光", "低强度"],
        avoidances=["少换乘"],
    )

    result = asyncio.run(service.build_result(101, request))

    assert "杭州东站" in result.context.prompt
    assert result.context.weather["city_name"] == "示例省 西湖景区 示例区"
    assert result.context.route["route_summary"]
    assert result.context.transport["transport_summary"]
    assert result.context.attractions["items"]
    assert result.context.realtime["news_traffic"]
    assert result.context.realtime["realtime_info_summary"].startswith("1. ")
    assert "\n2. " in result.context.realtime["realtime_info_summary"]
    assert result.risk_summary
    assert result.final_markdown.startswith("## 杭州东站到西湖景区规划草案")
    assert result.result_json["record_id"] == 101
    assert result.snapshots["summary"]["final_markdown"] == result.final_markdown


def test_ai_planning_maps_stage_snapshots_and_output_payload() -> None:
    service = _service()
    request = GenerateStreamRequest(origin="A", destination="B", range="一天")
    result = asyncio.run(service.build_result(1, request))

    route_snapshot = service.snapshot_for_stage(result, "route")
    realtime_snapshot = service.snapshot_for_stage(result, "realtime")
    output = service.output_payload(result)

    assert route_snapshot is not None
    assert route_snapshot[0] == "route"
    assert route_snapshot[1]["route_summary"]
    assert realtime_snapshot is not None
    assert realtime_snapshot[1]["realtime_info_summary"]
    assert realtime_snapshot[1]["realtime_info_summary"].startswith("1. ")
    assert output["final_markdown"]
    assert output["result_json"]["summary_title"]


def test_ai_planning_accepts_motorcycle_transport_mode() -> None:
    service = _service()
    request = GenerateStreamRequest(
        origin="杭州东站",
        destination="西湖景区",
        range="半天",
        transport_mode="motorcycle",
    )

    result = asyncio.run(service.build_result(102, request))

    assert result.context.transport["transport_mode"] == "motorcycle"
    assert "摩托车" in result.context.transport["transport_summary"]
    assert result.context.map_export["amap_route_url"]


def test_ai_planning_passes_attraction_waypoints_to_route_link() -> None:
    amap_client = WaypointAmapClient()
    service = AiPlanningService(
        weather_service=WeatherService(client=MockWeatherClient()),
        amap_service=AmapService(client=amap_client),
        realtime_service=RealtimeService(client=MockRealtimeClient()),
    )
    request = GenerateStreamRequest(
        origin="杭州东站",
        destination="西湖景区",
        range="一天",
        transport_mode="driving",
    )

    result = asyncio.run(service.build_result(104, request))

    assert amap_client.route_waypoints == ["120.149000,30.260000", "120.145000,30.245000"]
    assert amap_client.link_waypoints == amap_client.route_waypoints
    assert result.context.route["waypoints"] == amap_client.route_waypoints
    assert result.context.map_export["amap_route_url"]


def test_ai_planning_degrades_when_amap_route_is_empty() -> None:
    service = AiPlanningService(
        weather_service=WeatherService(client=MockWeatherClient()),
        amap_service=AmapService(client=FailingAmapClient()),
        realtime_service=RealtimeService(client=MockRealtimeClient()),
    )
    request = GenerateStreamRequest(
        origin="巢湖",
        destination="拉萨",
        range="30天",
        transport_mode="motorcycle",
    )

    result = asyncio.run(service.build_result(103, request))

    assert result.context.route["distance_m"] == 0
    assert result.context.route["fallback_reason"] == "RESULTS_ARE_EMPTY"
    assert result.context.map_export["fallback_reason"] == "RESULTS_ARE_EMPTY"
    assert "部分外部数据已降级" in result.risk_summary
    assert result.final_markdown.startswith("## 巢湖到拉萨规划草案")
