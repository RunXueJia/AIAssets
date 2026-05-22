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
    assert output["final_markdown"]
    assert output["result_json"]["summary_title"]
