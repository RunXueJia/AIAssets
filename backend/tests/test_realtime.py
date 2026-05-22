import asyncio

import pytest

from app.integrations.realtime import MockRealtimeClient
from app.integrations.realtime.client import (
    RealtimeClientError,
    TavilyRealtimeClient,
    create_realtime_client,
)
from app.schemas.realtime import RealtimeCategory
from app.services.realtime import RealtimeService


class FailingRealtimeClient:
    provider = "failing"
    mock = False

    async def search(
        self,
        *,
        keyword: str,
        category: RealtimeCategory,
        limit: int,
    ) -> list[dict]:
        raise RuntimeError("boom")


@pytest.mark.parametrize("category", ["news", "traffic", "guide", "pitfall"])
def test_realtime_service_supports_all_categories(category: RealtimeCategory) -> None:
    service = RealtimeService(client=MockRealtimeClient())

    data = asyncio.run(service.search(keyword="杭州 西湖", category=category, limit=3))

    assert data["category"] == category
    assert data["items"][0]["category"] == category
    assert data["items"][0]["classification"]
    assert data["items"][0]["source"]
    assert data["items"][0]["published_at"]
    assert data["items"][0]["credibility_score"] > 0
    assert data["sources"][0]["source"] == data["items"][0]["source"]
    assert data["mock"] is True


def test_realtime_service_uses_mock_fallback_when_client_fails() -> None:
    service = RealtimeService(client=FailingRealtimeClient(), fallback_client=MockRealtimeClient())

    data = asyncio.run(service.search(keyword="杭州 西湖 交通管制", category="traffic"))

    assert data["category"] == "traffic"
    assert data["provider"] == "mock"
    assert data["mock"] is True
    assert data["fallback_reason"] == "boom"
    assert data["items"][0]["credibility_label"] == "high"


def test_tavily_client_parses_results_and_source_fallback() -> None:
    client = TavilyRealtimeClient(api_key="test")

    items = client._parse_results(
        {
            "results": [
                {
                    "title": "西湖交通提醒",
                    "url": "https://example.gov.cn/a",
                    "published_date": "2026-05-21",
                    "content": "景区周边流量较大。",
                    "score": 0.8,
                }
            ]
        }
    )

    assert items[0]["title"] == "西湖交通提醒"
    assert items[0]["source"] == "example.gov.cn"
    assert items[0]["score"] == 0.8


def test_tavily_client_rejects_error_payload() -> None:
    client = TavilyRealtimeClient(api_key="test")

    with pytest.raises(RealtimeClientError):
        client._parse_results({"error": "invalid api key"})


def test_create_realtime_client_rejects_runtime_mock_provider(monkeypatch) -> None:
    monkeypatch.setenv("BACKEND_REALTIME_PROVIDER", "mock")
    from app.core.config import get_settings

    get_settings.cache_clear()
    try:
        create_realtime_client()
    except RealtimeClientError as exc:
        assert "不允许使用 Mock" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected RealtimeClientError")
    finally:
        get_settings.cache_clear()


def test_tavily_real_search_uses_configured_api_key() -> None:
    service = RealtimeService(client=create_realtime_client())

    data = asyncio.run(service.search(keyword="杭州 西湖 交通管制", category="traffic", limit=2))

    assert data["provider"] == "tavily"
    assert data["mock"] is False
    assert data["category"] == "traffic"
    assert isinstance(data["items"], list)
