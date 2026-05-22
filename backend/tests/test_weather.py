import asyncio
from datetime import date

from app.integrations.weather import MockWeatherClient
from app.integrations.weather.client import (
    AmapWeatherClient,
    TencentWeatherClient,
    WeatherClientError,
    create_weather_client,
)
from app.schemas.weather import WeatherCitySummary
from app.services.weather import WeatherService


class FailingWeatherClient:
    provider = "failing"
    mock = False

    async def query_city_weather(
        self,
        *,
        city: str,
        weather_date: date | None,
    ) -> WeatherCitySummary:
        raise RuntimeError("boom")


def test_weather_service_uses_mock_fallback_when_client_fails() -> None:
    service = WeatherService(client=FailingWeatherClient(), fallback_client=MockWeatherClient())

    data = asyncio.run(
        service.query_weather(city="杭州", weather_date=date.fromisoformat("2026-06-01"))
    )

    assert data["city_name"] == "杭州"
    assert data["weather_date"] == "2026-06-01"
    assert data["weather_summary"]
    assert data["mock"] is True
    assert data["fallback_reason"] == "boom"


def test_weather_service_builds_destination_and_route_batch_summary() -> None:
    service = WeatherService(client=MockWeatherClient())

    data = asyncio.run(
        service.summarize_route_weather(
            destination_city="杭州",
            route_cities=["湖州", "杭州", "苏州"],
            weather_date=date.fromisoformat("2026-06-01"),
        )
    )

    assert data["destination_city"] == "杭州"
    assert data["route_city_names"] == ["湖州", "苏州"]
    assert len(data["items"]) == 3
    assert "目的地杭州" in data["weather_summary"]
    assert data["mock"] is True


def test_create_weather_client_rejects_runtime_mock_provider(monkeypatch) -> None:
    monkeypatch.setenv("BACKEND_WEATHER_PROVIDER", "mock")
    from app.core.config import get_settings

    get_settings.cache_clear()
    try:
        create_weather_client()
    except WeatherClientError as exc:
        assert "不允许使用 Mock" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected WeatherClientError")
    finally:
        get_settings.cache_clear()


def test_create_weather_client_rejects_unknown_provider(monkeypatch) -> None:
    monkeypatch.setenv("BACKEND_WEATHER_PROVIDER", "unknown")
    from app.core.config import get_settings

    get_settings.cache_clear()
    try:
        create_weather_client()
    except WeatherClientError as exc:
        assert "不支持的天气供应商" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected WeatherClientError")
    finally:
        get_settings.cache_clear()


def test_amap_weather_client_parses_matching_forecast_date() -> None:
    client = AmapWeatherClient(api_key="test")
    payload = {
        "status": "1",
        "forecasts": [
            {
                "city": "杭州",
                "reporttime": "2026-05-21 09:00:00",
                "casts": [
                    {
                        "date": "2026-06-01",
                        "dayweather": "多云",
                        "nightweather": "阵雨",
                        "daytemp": "28",
                        "nighttemp": "20",
                        "daywind": "东",
                        "daypower": "3",
                    }
                ],
            }
        ],
    }

    summary = client._parse_forecast(
        city="杭州",
        weather_date=date.fromisoformat("2026-06-01"),
        payload=payload,
    )

    assert summary.city_name == "杭州"
    assert summary.weather_date == date.fromisoformat("2026-06-01")
    assert summary.condition == "多云转阵雨"
    assert summary.temperature_range == "20-28℃"
    assert summary.date_matched is True


def test_amap_weather_client_rejects_unmatched_in_range_date() -> None:
    client = AmapWeatherClient(api_key="test")
    payload = {
        "status": "1",
        "forecasts": [
            {
                "city": "杭州",
                "casts": [{"date": "2026-06-01", "dayweather": "多云"}],
            }
        ],
    }

    try:
        client._parse_forecast(
            city="杭州",
            weather_date=date.fromisoformat("2026-05-31"),
            payload=payload,
        )
    except WeatherClientError as exc:
        assert "目标日期" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected WeatherClientError")


def test_amap_weather_client_uses_latest_cast_for_far_future_date() -> None:
    client = AmapWeatherClient(api_key="test")
    payload = {
        "status": "1",
        "forecasts": [
            {
                "city": "杭州",
                "casts": [
                    {"date": "2026-06-01", "dayweather": "多云", "nightweather": "多云"},
                    {"date": "2026-06-02", "dayweather": "晴", "nightweather": "晴"},
                ],
            }
        ],
    }

    summary = client._parse_forecast(
        city="杭州",
        weather_date=date.fromisoformat("2026-06-10"),
        payload=payload,
    )

    assert summary.weather_date == date.fromisoformat("2026-06-02")
    assert summary.date_matched is False


def test_tencent_weather_real_api_returns_observe_data() -> None:
    client = TencentWeatherClient()

    summary = asyncio.run(client.query_city_weather(city="四川 成都 成华区", weather_date=None))

    assert summary.provider == "tencent"
    assert summary.mock is False
    assert summary.city_name == "四川 成都 成华区"
    assert summary.weather_summary
    assert summary.source_updated_at
