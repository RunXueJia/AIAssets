import asyncio
import logging
from datetime import date, datetime, timedelta, timezone

from app.integrations.weather import (
    WeatherClientError,
    WeatherClientProtocol,
    create_weather_client,
)
from app.schemas.weather import WeatherBatchSummary, WeatherCitySummary

APP_TZ = timezone(timedelta(hours=8))
logger = logging.getLogger(__name__)


class WeatherService:
    def __init__(
        self,
        client: WeatherClientProtocol | None = None,
        fallback_client: WeatherClientProtocol | None = None,
    ) -> None:
        self.client = client or create_weather_client()
        self.fallback_client = fallback_client

    async def query_weather(
        self,
        *,
        city: str,
        weather_date: date | None,
    ) -> dict:
        summary = await self._query_city(city=city, weather_date=weather_date)
        return summary.model_dump(mode="json")

    async def summarize_route_weather(
        self,
        *,
        destination_city: str,
        route_cities: list[str],
        weather_date: date | None,
    ) -> dict:
        city_names = self._dedupe_cities(
            destination_city=destination_city,
            route_cities=route_cities,
        )
        summaries = await asyncio.gather(
            *[
                self._query_city(city=city_name, weather_date=weather_date)
                for city_name in city_names
            ]
        )
        destination = summaries[0]
        route_summaries = summaries[1:]
        alert_level = self._highest_alert_level(summaries)
        alerts = [alert for item in summaries for alert in item.alerts]
        result = WeatherBatchSummary(
            destination_city=destination.city_name,
            route_city_names=[item.city_name for item in route_summaries],
            destination=destination,
            route_cities=route_summaries,
            items=summaries,
            weather_summary=self._batch_summary(destination, route_summaries, alert_level),
            alert_level=alert_level,
            alerts=alerts,
            provider=self._provider_for(summaries),
            source_updated_at=self._latest_source_updated_at(summaries),
            mock=all(item.mock for item in summaries),
            fallback_reason=self._fallback_reason_for(summaries),
        )
        return result.model_dump(mode="json")

    async def _query_city(
        self,
        *,
        city: str,
        weather_date: date | None,
    ) -> WeatherCitySummary:
        city_name = city.strip()
        try:
            return await self.client.query_city_weather(
                city=city_name,
                weather_date=weather_date,
            )
        except (WeatherClientError, Exception) as exc:
            logger.warning("weather provider fallback: %s", exc)
            if self.fallback_client is None:
                raise
            fallback = await self.fallback_client.query_city_weather(
                city=city_name,
                weather_date=weather_date,
            )
            fallback.fallback_reason = str(exc)
            return fallback

    def _dedupe_cities(self, *, destination_city: str, route_cities: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for city in [destination_city, *route_cities]:
            city_name = city.strip()
            if not city_name or city_name in seen:
                continue
            seen.add(city_name)
            result.append(city_name)
        return result

    def _batch_summary(
        self,
        destination: WeatherCitySummary,
        route_summaries: list[WeatherCitySummary],
        alert_level: str,
    ) -> str:
        parts = [f"目的地{destination.city_name}：{destination.weather_summary}"]
        if route_summaries:
            route_text = "；".join(
                f"{item.city_name}{item.condition or item.weather_summary}"
                for item in route_summaries
            )
            parts.append(f"沿途城市：{route_text}。")
        if alert_level != "none":
            parts.append("存在天气预警，建议出行前再次复核。")
        return "".join(parts)

    def _highest_alert_level(self, summaries: list[WeatherCitySummary]) -> str:
        if not summaries:
            return "none"
        return max((item.alert_level or "none" for item in summaries), key=self._alert_rank)

    def _alert_rank(self, level: str) -> int:
        normalized = level.lower()
        if "red" in normalized or "红" in normalized:
            return 4
        if "orange" in normalized or "橙" in normalized:
            return 3
        if "yellow" in normalized or "黄" in normalized:
            return 2
        if "blue" in normalized or "蓝" in normalized:
            return 1
        return 0

    def _provider_for(self, summaries: list[WeatherCitySummary]) -> str:
        providers = {item.provider for item in summaries}
        if len(providers) == 1:
            return providers.pop()
        return "mixed"

    def _latest_source_updated_at(self, summaries: list[WeatherCitySummary]) -> str:
        values = [item.source_updated_at for item in summaries if item.source_updated_at]
        return max(values) if values else datetime.now(APP_TZ).isoformat()

    def _fallback_reason_for(self, summaries: list[WeatherCitySummary]) -> str | None:
        reasons = [item.fallback_reason for item in summaries if item.fallback_reason]
        return "；".join(dict.fromkeys(reasons)) if reasons else None


weather_service = WeatherService()
