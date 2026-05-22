import asyncio
from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api.v1.endpoints import admin_records, planning_records
from app.core.exceptions import AppException
from app.models import GenerationOutput, RouteMapExport
from app.schemas.records import RegenerateRecordRequest
from app.services.records import RecordsService


def make_record(**overrides):
    values = {
        "id": 101,
        "record_no": "PL202605210001",
        "user_id": 12,
        "source_client": "web",
        "origin_text": "杭州东站",
        "destination_text": "西湖景区",
        "range_text": "一天，步行少一点",
        "transport_mode": "mixed",
        "status": "completed",
        "current_stage": "summary",
        "summary_title": "杭州东站到西湖一日轻松路线",
        "summary_text": "建议上午抵达西湖东线。",
        "duration_ms": 18500,
        "error_message": None,
        "created_at": datetime(2026, 5, 21, 10, 0, 0),
        "completed_at": datetime(2026, 5, 21, 10, 0, 18),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_record_routers_expose_integration_contract_paths() -> None:
    planning_paths = {route.path for route in planning_records.router.routes}
    admin_paths = {route.path for route in admin_records.router.routes}

    assert "/planning/records" in planning_paths
    assert "/planning/records/{record_id}" in planning_paths
    assert "/planning/records/{record_id}/stream" in planning_paths
    assert "/planning/records/{record_id}/generate_stream" in planning_paths
    assert "/planning/records/{record_id}/route_map" in planning_paths
    assert "/planning/records/{record_id}/regenerate" in planning_paths
    assert "/planning/records/{record_id}/retry" in planning_paths
    assert "/admin/generation_records" in admin_paths
    assert "/admin/generation_records/{record_id}" in admin_paths
    assert "/admin/generation_records/{record_id}/retry" in admin_paths
    assert "/admin/generation_records/{record_id}" in admin_paths


def test_map_url_columns_accept_long_amap_links() -> None:
    long_url = "https://act.amap.com/activity/2020CommonLanding/index.html?" + ("x" * 2200)

    output = GenerationOutput(record_id=101, amap_route_url=long_url)
    export = RouteMapExport(record_id=101, export_type="static", amap_route_url=long_url)

    assert output.amap_route_url == long_url
    assert export.amap_route_url == long_url


def test_list_planning_records_returns_paginated_payload() -> None:
    repo = SimpleNamespace(list_user_records=AsyncMock(return_value=(1, [make_record()])))
    service = RecordsService(repo=repo)

    data = asyncio.run(
        service.list_planning_records(
            db=SimpleNamespace(),
            user_id=12,
            page=1,
            page_size=20,
            status="completed",
            keyword="西湖",
        )
    )

    assert data["total"] == 1
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["items"][0]["record_no"] == "PL202605210001"
    assert data["items"][0]["created_at"] == "2026-05-21T10:00:00"


def test_get_planning_record_detail_raises_404_when_missing() -> None:
    repo = SimpleNamespace(get_record=AsyncMock(return_value=None))
    service = RecordsService(repo=repo)

    with pytest.raises(AppException) as exc_info:
        asyncio.run(
            service.get_planning_record_detail(
                db=SimpleNamespace(),
                user_id=12,
                record_id=404,
            )
        )

    assert exc_info.value.code == 404
    assert exc_info.value.message == "记录不存在"


def test_get_admin_generation_record_detail_includes_llm_call_logs() -> None:
    record = make_record()
    repo = SimpleNamespace(
        get_record=AsyncMock(return_value=record),
        get_record_detail_components=AsyncMock(
            return_value={
                "input": SimpleNamespace(
                    origin_text=record.origin_text,
                    destination_text=record.destination_text,
                    range_text=record.range_text,
                    travel_date=date(2026, 6, 1),
                    people_count=2,
                    preferences=["自然风光"],
                    avoidances=["少换乘"],
                ),
                "output": None,
                "route_snapshots": [],
                "map_exports": [],
                "weather_snapshots": [],
                "news_snapshots": [],
                "errors": [],
                "llm_call_logs": [
                    SimpleNamespace(
                        id=1,
                        provider="openai-compatible",
                        model_name="gpt-4.1-mini",
                        call_type="stream",
                        status="success",
                        prompt_tokens=1800,
                        completion_tokens=2600,
                        total_tokens=4400,
                        duration_ms=18500,
                        created_at=datetime(2026, 5, 21, 10, 0, 0),
                    )
                ],
            }
        ),
    )
    service = RecordsService(repo=repo)

    data = asyncio.run(
        service.get_admin_generation_record_detail(db=SimpleNamespace(), record_id=101)
    )

    assert data["record"]["id"] == 101
    assert data["input"]["travel_date"] == "2026-06-01"
    assert data["llm_call_logs"][0]["total_tokens"] == 4400


def test_regenerate_record_copies_parent_input_and_applies_overrides() -> None:
    parent_record = make_record(status="completed")
    parent_input = SimpleNamespace(
        origin_text="杭州东站",
        destination_text="西湖景区",
        range_text="一天，步行少一点",
        transport_mode="mixed",
        travel_date=date(2026, 6, 1),
        date_text=None,
        people_count=2,
        preferences=["自然风光"],
        avoidances=["少换乘"],
        raw_input={"range": "一天，步行少一点", "preferences": ["自然风光"]},
    )
    db = SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock())

    async def create_regeneration_record(
        _db,
        *,
        parent_record,
        record_no,
        input_payload,
        raw_input,
    ):
        assert parent_record.id == 101
        assert record_no.startswith("PL")
        assert input_payload["range_text"] == "一天，尽量少走路"
        assert input_payload["preferences"] == ["自然风光", "咖啡"]
        assert raw_input["range"] == "一天，尽量少走路"
        return make_record(id=102, status="pending", parent_record_id=101)

    repo = SimpleNamespace(
        get_record=AsyncMock(return_value=parent_record),
        get_record_input=AsyncMock(return_value=parent_input),
        create_regeneration_record=create_regeneration_record,
    )
    service = RecordsService(repo=repo)

    data = asyncio.run(
        service.regenerate_record(
            db=db,
            user_id=12,
            record_id=101,
            payload=RegenerateRecordRequest(
                override_input={
                    "range": "一天，尽量少走路",
                    "preferences": ["自然风光", "咖啡"],
                }
            ),
        )
    )

    assert data == {
        "record_id": 102,
        "parent_record_id": 101,
        "status": "pending",
        "stream_url": "/api/v1/planning/records/102/stream",
        "request_payload": {
            "origin": "杭州东站",
            "destination": "西湖景区",
            "range": "一天，尽量少走路",
            "transport_mode": "mixed",
            "travel_date": "2026-06-01",
            "people_count": 2,
            "preferences": ["自然风光", "咖啡"],
            "avoidances": ["少换乘"],
        },
    }
    db.commit.assert_awaited_once()


def test_list_stream_events_returns_resume_payload() -> None:
    record = make_record(status="streaming")
    event = SimpleNamespace(
        id=1,
        sequence_no=2,
        event_type="token",
        stage="route",
        content="路线内容",
        payload={"record_id": 101, "stage": "route", "content": "路线内容"},
        created_at=datetime(2026, 5, 21, 10, 0, 1),
    )
    repo = SimpleNamespace(
        get_record=AsyncMock(return_value=record),
        list_stream_events_after=AsyncMock(return_value=[event]),
    )
    service = RecordsService(repo=repo)

    data = asyncio.run(
        service.list_stream_events(
            db=SimpleNamespace(),
            user_id=12,
            record_id=101,
            after_sequence=1,
        )
    )

    assert data == [
        {
            "id": 1,
            "sequence_no": 2,
            "event": "token",
            "stage": "route",
            "content": "路线内容",
            "data": {"record_id": 101, "stage": "route", "content": "路线内容"},
            "created_at": "2026-05-21T10:00:01",
        }
    ]
    repo.list_stream_events_after.assert_awaited_once()


def test_retry_planning_record_requires_failed_status() -> None:
    repo = SimpleNamespace(get_record=AsyncMock(return_value=make_record(status="completed")))
    service = RecordsService(repo=repo)

    with pytest.raises(AppException) as exc_info:
        asyncio.run(
            service.retry_planning_record(
                db=SimpleNamespace(),
                user_id=12,
                record_id=101,
            )
        )

    assert exc_info.value.code == 409


def test_retry_planning_record_copies_failed_input() -> None:
    parent_record = make_record(status="failed")
    parent_input = SimpleNamespace(
        origin_text="巢湖",
        destination_text="拉萨",
        range_text="30天",
        transport_mode="motorcycle",
        travel_date=date(2026, 5, 31),
        date_text=None,
        people_count=1,
        preferences=["自然风光"],
        avoidances=[],
        raw_input={"origin": "巢湖", "destination": "拉萨", "range": "30天"},
    )
    db = SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock())

    async def create_regeneration_record(
        _db,
        *,
        parent_record,
        record_no,
        input_payload,
        raw_input,
    ):
        assert parent_record.id == 101
        assert input_payload["transport_mode"] == "motorcycle"
        assert raw_input["origin"] == "巢湖"
        return make_record(id=103, status="pending", parent_record_id=101)

    repo = SimpleNamespace(
        get_record=AsyncMock(return_value=parent_record),
        get_record_input=AsyncMock(return_value=parent_input),
        create_regeneration_record=create_regeneration_record,
    )
    service = RecordsService(repo=repo)

    data = asyncio.run(
        service.retry_planning_record(
            db=db,
            user_id=12,
            record_id=101,
        )
    )

    assert data["record_id"] == 103
    assert data["parent_record_id"] == 101
    assert data["stream_url"] == "/api/v1/planning/records/103/stream"
    assert data["request_payload"]["transport_mode"] == "motorcycle"


def test_existing_record_stream_request_uses_record_snapshot() -> None:
    detail = {
        "record": {
            "origin_text": "旧起点",
            "destination_text": "旧终点",
            "range_text": "旧范围",
            "transport_mode": "driving",
        },
        "input": {
            "origin_text": "杭州东站",
            "destination_text": "西湖景区",
            "range_text": "一天，尽量少走路",
            "travel_date": "2026-06-01",
            "people_count": 2,
            "preferences": ["自然风光", "咖啡"],
            "avoidances": ["少换乘"],
        },
    }

    request = planning_records._request_from_detail(detail)

    assert request.origin == "杭州东站"
    assert request.destination == "西湖景区"
    assert request.range == "一天，尽量少走路"
    assert request.transport_mode == "driving"
    assert request.travel_date == date(2026, 6, 1)
    assert request.people_count == 2
    assert request.preferences == ["自然风光", "咖啡"]
    assert request.avoidances == ["少换乘"]
