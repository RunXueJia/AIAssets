import asyncio
from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api.v1.endpoints import admin_records, planning_records
from app.core.exceptions import AppException
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
    assert "/planning/records/{record_id}/route_map" in planning_paths
    assert "/planning/records/{record_id}/regenerate" in planning_paths
    assert "/admin/generation_records" in admin_paths
    assert "/admin/generation_records/{record_id}" in admin_paths
    assert "/admin/generation_records/{record_id}/retry" in admin_paths
    assert "/admin/generation_records/{record_id}" in admin_paths


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
        "stream_url": "/api/v1/planning/generate_stream",
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
