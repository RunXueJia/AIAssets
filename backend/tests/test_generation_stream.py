import asyncio
import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.generation import get_generation_service, router
from app.core.exceptions import register_exception_handlers
from app.integrations.llm import LlmClientError
from app.schemas.ai_planning import TripPlanningContext, TripPlanningResult
from app.schemas.generation import GenerateStreamRequest
from app.services.generation import GenerationService, InMemoryGenerationRecordStore


class RealApiTestLlmClient:
    async def stream_stage_tokens(self, request, stage):  # noqa: ANN001
        yield f"{stage}: {request.origin} 到 {request.destination}"


class FailingTransportLlmClient:
    async def stream_stage_tokens(self, request, stage):  # noqa: ANN001
        if stage == "transport":
            raise LlmClientError("LLM 流式调用失败: connection reset")
        yield f"{stage}: {request.origin} 到 {request.destination}"


class DeterministicPlanningService:
    async def build_result(self, record_id, request):  # noqa: ANN001
        weather = {
            "city_name": request.destination,
            "weather_summary": f"{request.destination}今日多云，适合出行。",
            "alert_level": "none",
            "alerts": [],
            "provider": "unit-test",
            "mock": False,
            "source_updated_at": "2026-05-21T10:00:00+08:00",
        }
        route = {
            "origin": request.origin,
            "destination": request.destination,
            "origin_location": "120.21201,30.29191",
            "destination_location": "120.143222,30.236064",
            "distance_m": 12800,
            "duration_s": 2400,
            "route_summary": "约12.8公里，预计40分钟",
            "waypoints": [],
            "provider": "unit-test",
            "mock": False,
            "source_updated_at": "2026-05-21T10:00:00+08:00",
        }
        transport = {
            "transport_mode": request.transport_mode,
            "transport_summary": "建议公共交通为主，减少步行距离。",
            "segments": [],
            "source_updated_at": "2026-05-21T10:00:00+08:00",
        }
        map_export = {
            "amap_route_url": "https://uri.amap.com/navigation?from=120.21201,30.29191&to=120.143222,30.236064",
            "image_url": "https://restapi.amap.com/v3/staticmap?location=120.143222%2C30.236064",
            "export_type": "static",
            "status": "completed",
            "provider": "unit-test",
            "mock": False,
            "source_updated_at": "2026-05-21T10:00:00+08:00",
        }
        attractions = {
            "attractions_summary": "推荐关注西湖风景名胜区。",
            "items": [{"name": request.destination, "reason": "用户指定目的地"}],
            "provider": "unit-test",
            "mock": False,
            "source_updated_at": "2026-05-21T10:00:00+08:00",
        }
        realtime = {
            "news_traffic": [{"title": "西湖周边交通提醒", "source": "unit-test"}],
            "guide_pitfall": [{"title": "预约与错峰提醒", "source": "unit-test"}],
            "realtime_info_summary": "西湖周边建议错峰进入。",
            "provider": "unit-test",
            "mock": False,
            "source_updated_at": "2026-05-21T10:00:00+08:00",
        }
        final_markdown = f"## {request.origin}到{request.destination}规划草案\n\n约12.8公里。"
        result_json = {
            "record_id": record_id,
            "summary_title": f"{request.origin}到{request.destination}规划草案",
        }
        snapshots = {
            "weather": weather,
            "route": route,
            "transport": transport,
            "map_export": map_export,
            "attractions": attractions,
            "realtime": realtime,
            "summary": {
                "summary_title": result_json["summary_title"],
                "summary_text": "约12.8公里，预计40分钟。",
                "risk_summary": "出行前复核天气、交通管制和地图导航信息",
                "final_markdown": final_markdown,
                "result_json": result_json,
                "source_updated_at": "2026-05-21T10:00:00+08:00",
            },
        }
        context = TripPlanningContext(
            request=request.model_dump(mode="json"),
            weather=weather,
            route=route,
            transport=transport,
            map_export=map_export,
            attractions=attractions,
            realtime=realtime,
            risks=["出行前复核天气、交通管制和地图导航信息"],
            prompt="unit-test prompt",
        )
        return TripPlanningResult(
            summary_title=result_json["summary_title"],
            summary_text="约12.8公里，预计40分钟。",
            snapshots=snapshots,
            final_markdown=final_markdown,
            result_json=result_json,
            weather_summary=weather["weather_summary"],
            route_summary=route["route_summary"],
            attractions_summary=attractions["attractions_summary"],
            realtime_info_summary=realtime["realtime_info_summary"],
            risk_summary="出行前复核天气、交通管制和地图导航信息",
            amap_route_url=map_export["amap_route_url"],
            context=context,
        )

    def snapshot_for_stage(self, result, stage):  # noqa: ANN001
        if stage not in result.snapshots:
            return None
        return stage, result.snapshots[stage]

    def output_payload(self, result):  # noqa: ANN001
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


class FailingPlanningService:
    async def build_result(self, record_id, request):  # noqa: ANN001
        raise RuntimeError("planning failed")


def _client() -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1")

    def override_service() -> GenerationService:
        return GenerationService(
            record_store=InMemoryGenerationRecordStore(),
            llm_client=RealApiTestLlmClient(),
            planning_service=DeterministicPlanningService(),
            token_delay_s=0,
        )

    app.dependency_overrides[get_generation_service] = override_service
    return TestClient(app)


def _parse_sse_events(body: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    for chunk in body.strip().split("\n\n"):
        lines = chunk.splitlines()
        event_name = lines[0].removeprefix("event: ")
        payload = json.loads(lines[1].removeprefix("data: "))
        events.append((event_name, payload))
    return events


def test_generate_stream_returns_documented_sse_events() -> None:
    client = _client()

    response = client.post(
        "/api/v1/planning/generate_stream",
        json={
            "origin": "杭州东站",
            "destination": "西湖景区",
            "range": "一天，步行少一点",
            "transport_mode": "mixed",
            "travel_date": "2026-06-01",
            "people_count": 2,
            "preferences": ["自然风光", "低强度", "美食"],
            "avoidances": ["少换乘", "避开热门景点"],
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    events = _parse_sse_events(response.text)
    event_names = [event_name for event_name, _ in events]

    assert event_names[0] == "record_created"
    assert events[0][1]["status"] == "pending"
    assert events[0][1]["record_id"] >= 101

    assert "stage" in event_names
    assert "token" in event_names
    assert "snapshot" in event_names
    assert event_names[-1] == "done"
    assert events[-1][1]["status"] == "completed"
    assert events[-1][1]["record_id"] == events[0][1]["record_id"]

    snapshot_types = [
        payload["type"] for event_name, payload in events if event_name == "snapshot"
    ]
    assert "route" in snapshot_types
    assert "attractions" in snapshot_types
    assert "realtime" in snapshot_types


def test_generate_stream_accepts_missing_range() -> None:
    client = _client()

    response = client.post(
        "/api/v1/planning/generate_stream",
        json={
            "origin": "杭州东站",
            "destination": "西湖景区",
            "transport_mode": "mixed",
        },
    )

    assert response.status_code == 200

    events = _parse_sse_events(response.text)
    assert events[0][0] == "record_created"
    assert events[-1][0] == "done"
    assert events[-1][1]["status"] == "completed"


def test_cancel_generation_returns_unified_response() -> None:
    client = _client()

    response = client.post("/api/v1/planning/cancel/101")

    assert response.status_code == 200
    assert response.json() == {
        "code": 200,
        "message": "已取消",
        "data": {
            "record_id": 101,
            "status": "canceled",
        },
    }


def test_generate_stream_requires_auth_without_override() -> None:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1")
    client = TestClient(app)

    response = client.post(
        "/api/v1/planning/generate_stream",
        json={"origin": "杭州东站", "destination": "西湖景区", "range": "一天"},
    )

    assert response.status_code == 401
    assert response.json()["message"] == "请先登录"


def test_service_persists_events_snapshots_and_output_in_store() -> None:
    store = InMemoryGenerationRecordStore()
    service = GenerationService(
        record_store=store,
        llm_client=RealApiTestLlmClient(),
        planning_service=DeterministicPlanningService(),
        token_delay_s=0,
    )

    async def collect() -> list[tuple[str, dict]]:
        events = []
        async for event in service.stream_generation(
            request=GenerateStreamRequest(
                origin="杭州东站",
                destination="西湖景区",
                range="一天",
            )
        ):
            events.append((event.event, event.data))
        return events

    events = asyncio.run(collect())

    assert events[-1][1]["status"] == "completed"
    assert store.events
    assert store.snapshots["route"]["route_summary"]
    assert store.snapshots["realtime"]["realtime_info_summary"]
    assert store.output_payload is not None
    assert store.output_payload["final_markdown"].startswith("## ")


def test_service_can_stream_into_existing_pending_record() -> None:
    store = InMemoryGenerationRecordStore()
    service = GenerationService(
        record_store=store,
        llm_client=RealApiTestLlmClient(),
        planning_service=DeterministicPlanningService(),
        token_delay_s=0,
    )

    async def collect() -> list[tuple[str, dict]]:
        request = GenerateStreamRequest(origin="A", destination="B", range="一天")
        await store.use_existing_record(201, request)
        events = []
        async for event in service.stream_generation(request, existing_record_id=201):
            events.append((event.event, event.data))
        return events

    events = asyncio.run(collect())

    assert events[0][0] == "stage"
    assert all(event_name != "record_created" for event_name, _ in events)
    assert events[-1][1]["record_id"] == 201
    assert events[-1][1]["status"] == "completed"


def test_service_marks_record_failed_when_planning_context_fails() -> None:
    store = InMemoryGenerationRecordStore()
    service = GenerationService(
        record_store=store,
        llm_client=RealApiTestLlmClient(),
        planning_service=FailingPlanningService(),
        token_delay_s=0,
    )

    async def collect() -> list[tuple[str, dict]]:
        events = []
        async for event in service.stream_generation(
            request=GenerateStreamRequest(origin="A", destination="B", range="一天")
        ):
            events.append((event.event, event.data))
        return events

    events = asyncio.run(collect())

    assert events[-2][0] == "error"
    assert events[-2][1]["error_code"] == "GENERATION_FAILED"
    assert events[-1][1]["status"] == "failed"


def test_service_continues_when_single_llm_stage_stream_fails() -> None:
    store = InMemoryGenerationRecordStore()
    service = GenerationService(
        record_store=store,
        llm_client=FailingTransportLlmClient(),
        planning_service=DeterministicPlanningService(),
        token_delay_s=0,
    )

    async def collect() -> list[tuple[str, dict]]:
        events = []
        async for event in service.stream_generation(
            request=GenerateStreamRequest(origin="A", destination="B", range="一天")
        ):
            events.append((event.event, event.data))
        return events

    events = asyncio.run(collect())
    transport_errors = [
        payload
        for event_name, payload in events
        if event_name == "error" and payload.get("stage") == "transport"
    ]
    transport_tokens = [
        payload
        for event_name, payload in events
        if event_name == "token" and payload.get("stage") == "transport"
    ]

    assert events[-1][0] == "done"
    assert events[-1][1]["status"] == "completed"
    assert transport_errors[0]["error_code"] == "LLM_STAGE_FAILED"
    assert "系统规划结果" in transport_tokens[-1]["content"]
    assert store.output_payload is not None


def test_service_reports_canceled_if_cancel_happens_before_completion() -> None:
    class CancelOnSaveOutputStore(InMemoryGenerationRecordStore):
        async def save_output(self, output_payload):
            await super().save_output(output_payload)
            if self._records:
                record_id = next(iter(self._records))
                await self.cancel_record(record_id)

    store = CancelOnSaveOutputStore()
    service = GenerationService(
        record_store=store,
        llm_client=RealApiTestLlmClient(),
        planning_service=DeterministicPlanningService(),
        token_delay_s=0,
    )

    async def collect() -> list[tuple[str, dict]]:
        events = []
        async for event in service.stream_generation(
            request=GenerateStreamRequest(origin="A", destination="B", range="一天")
        ):
            events.append((event.event, event.data))
        return events

    events = asyncio.run(collect())

    assert events[-1][0] == "done"
    assert events[-1][1]["status"] == "canceled"
