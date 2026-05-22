import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from app.core.config import get_settings
from app.integrations.cache import TtlCache
from app.schemas.realtime import RealtimeCategory

APP_TZ = timezone(timedelta(hours=8))


class RealtimeClientError(Exception):
    pass


class RealtimeClientProtocol(Protocol):
    provider: str
    mock: bool

    async def search(
        self,
        *,
        keyword: str,
        category: RealtimeCategory,
        limit: int,
    ) -> list[dict[str, Any]]: ...


class MockRealtimeClient:
    provider = "mock"
    mock = True

    async def search(
        self,
        *,
        keyword: str,
        category: RealtimeCategory,
        limit: int,
    ) -> list[dict[str, Any]]:
        item = {
            "title": _title_for(category),
            "url": f"https://example.com/{category}/1",
            "source": _source_for(category),
            "published_at": (datetime.now(APP_TZ) - timedelta(hours=6)).isoformat(),
            "summary": f"{keyword} 相关{_category_label(category)} Mock 摘要。",
            "tags": [category, "mock"],
            "category": category,
            "credibility_score": _mock_score_for(category),
            "source_type": _source_type_for(category),
        }
        return [item][:limit]


class TavilyRealtimeClient:
    provider = "tavily"
    mock = False

    def __init__(
        self,
        *,
        api_key: str,
        endpoint: str = "https://api.tavily.com/search",
        timeout_s: float = 10,
        max_retries: int = 1,
        cache: TtlCache | None = None,
    ) -> None:
        self.api_key = api_key
        self.endpoint = endpoint
        self.timeout_s = timeout_s
        self.max_retries = max_retries
        self.cache = cache or TtlCache(ttl_s=300)

    async def search(
        self,
        *,
        keyword: str,
        category: RealtimeCategory,
        limit: int,
    ) -> list[dict[str, Any]]:
        query = self._query(keyword=keyword, category=category)
        cache_key = f"tavily:{query}:{limit}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        payload = await self._request(query=query, limit=limit)
        results = self._parse_results(payload)
        self.cache.set(cache_key, results)
        return results

    async def _request(self, *, query: str, limit: int) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                return await asyncio.to_thread(
                    self._request_sync,
                    query=query,
                    limit=limit,
                )
            except RealtimeClientError as exc:
                last_error = exc
            if attempt < self.max_retries:
                await asyncio.sleep(0.2 * (2**attempt))
        raise RealtimeClientError(str(last_error or "实时检索服务请求失败"))

    def _request_sync(self, *, query: str, limit: int) -> dict[str, Any]:
        body = json.dumps(
            {
                "api_key": self.api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": limit,
                "include_answer": False,
            }
        ).encode("utf-8")
        request = Request(
            self.endpoint,
            data=body,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "RouteCraft/1.0",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_s) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            message = str(exc)
            raise RealtimeClientError(f"实时检索服务请求失败: {message}") from exc

    def _parse_results(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        if not isinstance(payload, dict):
            raise RealtimeClientError("实时检索服务返回格式错误")
        if payload.get("error"):
            raise RealtimeClientError(str(payload["error"]))
        results = payload.get("results")
        if results is None:
            return []
        if not isinstance(results, list):
            raise RealtimeClientError("实时检索结果格式错误")
        items: list[dict[str, Any]] = []
        for result in results:
            if not isinstance(result, dict):
                continue
            url = result.get("url")
            items.append(
                {
                    "title": result.get("title"),
                    "url": url,
                    "source": result.get("source") or self._domain(url),
                    "published_at": result.get("published_date") or result.get("published_at"),
                    "summary": result.get("content") or result.get("snippet"),
                    "score": result.get("score"),
                    "raw": result,
                }
            )
        return items

    def _query(self, *, keyword: str, category: RealtimeCategory) -> str:
        modifiers = {
            "news": "最新 新闻 官方 发布",
            "traffic": "交通 管制 道路 景区 出行 提醒",
            "guide": "攻略 开放时间 门票 预约 游玩建议",
            "pitfall": "避坑 排队 闭园 价格 投诉 体验",
        }
        return f"{keyword} {modifiers[category]}".strip()

    def _domain(self, url: Any) -> str:
        if not isinstance(url, str) or not url:
            return self.provider
        return urlparse(url).netloc or self.provider


def create_realtime_client() -> RealtimeClientProtocol:
    settings = get_settings()
    provider = settings.realtime_provider.strip().lower()
    api_key = settings.realtime_search_api_key or settings.tavily_api_key
    if provider == "mock":
        raise RealtimeClientError("运行时不允许使用 Mock 实时检索服务，请配置真实搜索 API")
    if provider not in {"", "tavily"}:
        raise RealtimeClientError(f"不支持的实时检索供应商：{provider}")
    if not api_key:
        raise RealtimeClientError(
            "未配置实时检索 API Key：请设置 BACKEND_REALTIME_SEARCH_API_KEY "
            "或 BACKEND_TAVILY_API_KEY"
        )
    return TavilyRealtimeClient(api_key=api_key)


def _title_for(category: RealtimeCategory) -> str:
    titles = {
        "news": "目的地实时资讯",
        "traffic": "景区周边交通提醒",
        "guide": "攻略参考提醒",
        "pitfall": "避坑参考提醒",
    }
    return titles[category]


def _source_for(category: RealtimeCategory) -> str:
    sources = {
        "news": "示例新闻源",
        "traffic": "示例交通信息源",
        "guide": "示例攻略社区",
        "pitfall": "示例旅行经验库",
    }
    return sources[category]


def _source_type_for(category: RealtimeCategory) -> str:
    source_types = {
        "news": "news",
        "traffic": "official_notice",
        "guide": "travel_guide",
        "pitfall": "user_experience",
    }
    return source_types[category]


def _mock_score_for(category: RealtimeCategory) -> float:
    scores = {
        "news": 84.0,
        "traffic": 88.0,
        "guide": 76.0,
        "pitfall": 72.0,
    }
    return scores[category]


def _category_label(category: RealtimeCategory) -> str:
    labels = {
        "news": "实时资讯",
        "traffic": "交通提醒",
        "guide": "攻略参考",
        "pitfall": "避坑参考",
    }
    return labels[category]
