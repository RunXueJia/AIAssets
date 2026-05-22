import asyncio
import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from typing import Any, Protocol
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.core.config import get_settings
from app.integrations.cache import TtlCache
from app.schemas.weather import WeatherCitySummary

APP_TZ = timezone(timedelta(hours=8))


class WeatherClientError(Exception):
    pass


class WeatherClientProtocol(Protocol):
    provider: str
    mock: bool

    async def query_city_weather(
        self,
        *,
        city: str,
        weather_date: date | None,
    ) -> WeatherCitySummary: ...


class MockWeatherClient:
    provider = "mock"
    mock = True

    async def query_city_weather(
        self,
        *,
        city: str,
        weather_date: date | None,
    ) -> WeatherCitySummary:
        return self.build_summary(city=city, weather_date=weather_date)

    def build_summary(self, *, city: str, weather_date: date | None) -> WeatherCitySummary:
        date_key = weather_date.isoformat() if weather_date else "today"
        digest = int(hashlib.sha256(f"{city}:{date_key}".encode()).hexdigest()[:8], 16)
        conditions = ["多云", "晴到多云", "阴", "小雨", "阵雨"]
        condition = conditions[digest % len(conditions)]
        low_temp = 17 + digest % 8
        high_temp = low_temp + 5 + digest % 4
        wind_levels = ["微风", "东北风2级", "东南风3级", "西北风2级"]
        wind = wind_levels[digest % len(wind_levels)]
        travel_tip = "适合常规出行"
        if "雨" in condition:
            travel_tip = "建议携带雨具并预留室内备选"
        summary = (
            f"{city}{self._date_text(weather_date)}天气{condition}，"
            f"气温{low_temp}-{high_temp}℃，{wind}，{travel_tip}。"
        )
        return WeatherCitySummary(
            city_name=city,
            weather_date=weather_date,
            weather_summary=summary,
            alert_level="none",
            alerts=[],
            condition=condition,
            temperature_range=f"{low_temp}-{high_temp}℃",
            wind=wind,
            humidity=f"{55 + digest % 25}%",
            provider=self.provider,
            source_updated_at=_iso_now(),
            mock=True,
            raw={"provider": self.provider},
        )

    def _date_text(self, weather_date: date | None) -> str:
        return f" {weather_date.isoformat()} " if weather_date else "今日"


class TencentWeatherClient:
    provider = "tencent"
    mock = False

    def __init__(
        self,
        *,
        endpoint: str = "https://wis.qq.com/weather/common",
        timeout_s: float = 8,
        max_retries: int = 1,
        cache: TtlCache | None = None,
    ) -> None:
        self.endpoint = endpoint
        self.timeout_s = timeout_s
        self.max_retries = max_retries
        self.cache = cache or TtlCache(ttl_s=600)

    async def query_city_weather(
        self,
        *,
        city: str,
        weather_date: date | None,
    ) -> WeatherCitySummary:
        location = self._split_city(city)
        cache_key = (
            "tencent-weather:"
            f"{location['province']}:{location['city']}:{location['county']}:"
            f"{weather_date.isoformat() if weather_date else 'today'}"
        )
        cached = self.cache.get(cache_key)
        if cached is not None:
            return WeatherCitySummary.model_validate(cached)
        payload = await self._fetch_weather(location)
        summary = self._parse_weather(city=city, weather_date=weather_date, payload=payload)
        self.cache.set(cache_key, summary.model_dump(mode="json"))
        return summary

    async def _fetch_weather(self, location: dict[str, str]) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                return await asyncio.to_thread(self._fetch_weather_sync, location)
            except WeatherClientError as exc:
                last_error = exc
            if attempt < self.max_retries:
                await asyncio.sleep(0.2 * (2**attempt))
        raise WeatherClientError(str(last_error or "腾讯天气请求失败"))

    def _fetch_weather_sync(self, location: dict[str, str]) -> dict[str, Any]:
        params = urlencode(
            {
                "source": "pc",
                "weather_type": "observe|forecast_1h|forecast_24h|index|alarm|limit|tips|rise",
                "province": location["province"],
                "city": location["city"],
                "county": location["county"],
            }
        )
        request = Request(f"{self.endpoint}?{params}", headers={"User-Agent": "RouteCraft/1.0"})
        try:
            with urlopen(request, timeout=self.timeout_s) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise WeatherClientError(f"腾讯天气请求失败: {exc}") from exc

    def _parse_weather(
        self,
        *,
        city: str,
        weather_date: date | None,
        payload: dict[str, Any],
    ) -> WeatherCitySummary:
        if payload.get("status") != 200:
            raise WeatherClientError(str(payload.get("message") or "腾讯天气返回失败"))
        data = payload.get("data")
        if not isinstance(data, dict):
            raise WeatherClientError("腾讯天气返回缺少 data")
        observe = data.get("observe") if isinstance(data.get("observe"), dict) else {}
        forecast = self._select_forecast(data.get("forecast_24h"), weather_date)
        cast_date = self._parse_date(forecast.get("time")) if forecast else weather_date
        condition = (
            forecast.get("day_weather")
            or forecast.get("night_weather")
            or observe.get("weather")
            or observe.get("weather_short")
            or ""
        )
        temperature_range = self._temperature_range(
            forecast.get("min_degree") if forecast else None,
            forecast.get("max_degree") if forecast else None,
            observe.get("degree"),
        )
        wind = (
            f"{forecast.get('day_wind_direction')}{forecast.get('day_wind_power')}"
            if forecast and forecast.get("day_wind_direction")
            else self._observe_wind(observe)
        )
        summary = (
            f"{city}{self._date_text(cast_date)}天气{condition or '待更新'}，"
            f"气温{temperature_range or '待更新'}，{wind or '风力待更新'}。"
        )
        return WeatherCitySummary(
            city_name=city,
            weather_date=cast_date,
            weather_summary=summary,
            alert_level=self._alert_level(data.get("alarm")),
            alerts=self._alerts(data.get("alarm")),
            condition=condition or None,
            temperature_range=temperature_range,
            wind=wind,
            humidity=str(observe.get("humidity")) if observe.get("humidity") else None,
            provider=self.provider,
            source_updated_at=self._source_updated_at(observe.get("update_time")),
            mock=False,
            date_matched=cast_date == weather_date if weather_date else True,
            raw={"provider": self.provider, "weather": data},
        )

    def _select_forecast(self, value: Any, weather_date: date | None) -> dict[str, Any]:
        if not isinstance(value, dict) or not value:
            return {}
        forecasts = [item for item in value.values() if isinstance(item, dict)]
        if not forecasts:
            return {}
        if weather_date is None:
            return forecasts[0]
        for item in forecasts:
            if item.get("time") == weather_date.isoformat():
                return item
        max_forecast_date = max(
            (
                parsed
                for item in forecasts
                if (parsed := self._parse_date(item.get("time"))) is not None
            ),
            default=None,
        )
        if max_forecast_date is not None and weather_date > max_forecast_date:
            return forecasts[-1]
        raise WeatherClientError("腾讯天气未返回目标日期预报")

    def _split_city(self, city: str) -> dict[str, str]:
        parts = [part.strip() for part in city.replace("/", " ").split() if part.strip()]
        if len(parts) >= 3:
            return {"province": parts[0], "city": parts[1], "county": parts[2]}
        if len(parts) == 2:
            return {"province": parts[0], "city": parts[1], "county": parts[1]}
        city_name = city.strip()
        return {"province": city_name, "city": city_name, "county": city_name}

    def _temperature_range(self, low: Any, high: Any, current: Any) -> str | None:
        if low not in (None, "") and high not in (None, ""):
            return f"{low}-{high}℃"
        if current not in (None, ""):
            return f"{current}℃"
        return None

    def _observe_wind(self, observe: dict[str, Any]) -> str | None:
        direction = observe.get("wind_direction_name")
        power = observe.get("wind_power")
        if direction and power:
            return f"{direction}{power}级"
        return str(direction or power) if direction or power else None

    def _source_updated_at(self, value: Any) -> str:
        if not isinstance(value, str) or not value:
            return _iso_now()
        for fmt in ("%Y%m%d%H%M%S", "%Y%m%d%H%M"):
            try:
                return datetime.strptime(value, fmt).replace(tzinfo=APP_TZ).isoformat()
            except ValueError:
                continue
        return _iso_now()

    def _alert_level(self, value: Any) -> str:
        alerts = self._alerts(value)
        if not alerts:
            return "none"
        return alerts[0]["level"] or "unknown"

    def _alerts(self, value: Any) -> list[dict[str, str | None]]:
        if not isinstance(value, dict) or not value:
            return []
        result = []
        for item in value.values():
            if not isinstance(item, dict):
                continue
            result.append(
                {
                    "title": str(item.get("title") or item.get("type_name") or "天气预警"),
                    "level": item.get("level_name") or item.get("level"),
                    "description": str(item.get("detail") or item.get("content") or ""),
                    "source": "tencent",
                }
            )
        return result

    def _parse_date(self, value: Any) -> date | None:
        if not isinstance(value, str) or not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None

    def _date_text(self, weather_date: date | None) -> str:
        return f" {weather_date.isoformat()} " if weather_date else "今日"


class AmapWeatherClient:
    provider = "amap"
    mock = False

    def __init__(
        self,
        *,
        api_key: str,
        endpoint: str = "https://restapi.amap.com/v3/weather/weatherInfo",
        timeout_s: float = 8,
        max_retries: int = 1,
        cache: TtlCache | None = None,
    ) -> None:
        self.api_key = api_key
        self.endpoint = endpoint
        self.timeout_s = timeout_s
        self.max_retries = max_retries
        self.cache = cache or TtlCache(ttl_s=600)

    async def query_city_weather(
        self,
        *,
        city: str,
        weather_date: date | None,
    ) -> WeatherCitySummary:
        cache_key = f"amap-weather:{city}:{weather_date.isoformat() if weather_date else 'today'}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return WeatherCitySummary.model_validate(cached)
        payload = await self._fetch_forecast(city)
        summary = self._parse_forecast(city=city, weather_date=weather_date, payload=payload)
        self.cache.set(cache_key, summary.model_dump(mode="json"))
        return summary

    async def _fetch_forecast(self, city: str) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                return await asyncio.to_thread(self._fetch_forecast_sync, city)
            except WeatherClientError as exc:
                last_error = exc
            if attempt < self.max_retries:
                await asyncio.sleep(0.2 * (2**attempt))
        raise WeatherClientError(str(last_error or "天气服务请求失败"))

    def _fetch_forecast_sync(self, city: str) -> dict[str, Any]:
        params = urlencode(
            {
                "key": self.api_key,
                "city": city,
                "extensions": "all",
                "output": "json",
            }
        )
        request = Request(f"{self.endpoint}?{params}", headers={"User-Agent": "RouteCraft/1.0"})
        try:
            with urlopen(request, timeout=self.timeout_s) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise WeatherClientError(f"天气服务请求失败: {exc}") from exc

    def _parse_forecast(
        self,
        *,
        city: str,
        weather_date: date | None,
        payload: dict[str, Any],
    ) -> WeatherCitySummary:
        if payload.get("status") != "1":
            message = payload.get("info") or "天气服务返回失败"
            raise WeatherClientError(str(message))

        forecasts = payload.get("forecasts") or []
        if not forecasts:
            raise WeatherClientError("天气服务未返回城市预报")

        forecast = forecasts[0]
        casts = forecast.get("casts") or []
        cast = self._select_cast(casts, weather_date)
        if cast is None:
            raise WeatherClientError("天气服务未返回目标日期预报")

        cast_date = self._parse_date(cast.get("date")) or weather_date
        day_weather = str(cast.get("dayweather") or "")
        night_weather = str(cast.get("nightweather") or "")
        condition = (
            day_weather
            if day_weather == night_weather
            else f"{day_weather}转{night_weather}"
        )
        day_temp = cast.get("daytemp")
        night_temp = cast.get("nighttemp")
        temperature_range = self._temperature_range(night_temp, day_temp)
        wind = self._wind_text(cast)
        summary = (
            f"{forecast.get('city') or city}{self._date_text(cast_date)}天气{condition}，"
            f"气温{temperature_range or '待更新'}，{wind or '风力待更新'}。"
        )
        return WeatherCitySummary(
            city_name=str(forecast.get("city") or city),
            weather_date=cast_date,
            weather_summary=summary,
            alert_level="none",
            alerts=[],
            condition=condition or None,
            temperature_range=temperature_range,
            wind=wind,
            provider=self.provider,
            source_updated_at=self._report_time(forecast.get("reporttime")),
            mock=False,
            date_matched=cast_date == weather_date if weather_date else True,
            raw={"provider": self.provider, "forecast": forecast},
        )

    def _select_cast(
        self,
        casts: list[dict[str, Any]],
        weather_date: date | None,
    ) -> dict[str, Any] | None:
        if not casts:
            return None
        if weather_date is None:
            return casts[0]
        max_forecast_date = max(
            (
                parsed
                for cast in casts
                if (parsed := self._parse_date(cast.get("date"))) is not None
            ),
            default=None,
        )
        if max_forecast_date is not None and weather_date > max_forecast_date:
            return casts[-1]
        target = weather_date.isoformat()
        return next((cast for cast in casts if cast.get("date") == target), None)

    def _temperature_range(self, low: Any, high: Any) -> str | None:
        if low in (None, "") or high in (None, ""):
            return None
        return f"{low}-{high}℃"

    def _wind_text(self, cast: dict[str, Any]) -> str | None:
        wind = cast.get("daywind") or cast.get("nightwind")
        power = cast.get("daypower") or cast.get("nightpower")
        if wind and power:
            return f"{wind}风{power}级"
        return str(wind or power) if wind or power else None

    def _report_time(self, value: Any) -> str:
        if not isinstance(value, str) or not value:
            return _iso_now()
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=APP_TZ).isoformat()
        except ValueError:
            return _iso_now()

    def _parse_date(self, value: Any) -> date | None:
        if not isinstance(value, str) or not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None

    def _date_text(self, weather_date: date | None) -> str:
        return f" {weather_date.isoformat()} " if weather_date else "今日"


def create_weather_client() -> WeatherClientProtocol:
    settings = get_settings()
    provider = settings.weather_provider.strip().lower()
    api_key = (
        settings.weather_api_key
        or settings.amap_weather_key
        or settings.amap_api_key
        or settings.amap_key
    )
    if provider in {"", "tencent", "qq"}:
        return TencentWeatherClient()
    if provider == "mock":
        raise WeatherClientError("运行时不允许使用 Mock 天气服务，请配置真实天气 API")
    if provider == "amap" and not api_key:
        raise WeatherClientError("未配置高德天气 Key：请设置 BACKEND_AMAP_API_KEY")
    if provider == "amap":
        return AmapWeatherClient(api_key=api_key)
    raise WeatherClientError(f"不支持的天气供应商：{provider}")


def _iso_now() -> str:
    return datetime.now(APP_TZ).isoformat()
