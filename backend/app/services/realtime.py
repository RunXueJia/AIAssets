import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse

from app.integrations.realtime import (
    MockRealtimeClient,
    RealtimeClientError,
    RealtimeClientProtocol,
    create_realtime_client,
)
from app.schemas.realtime import (
    RealtimeCategory,
    RealtimeItem,
    RealtimeSearchResult,
    RealtimeSourceSummary,
)

APP_TZ = timezone(timedelta(hours=8))
logger = logging.getLogger(__name__)


class RealtimeService:
    def __init__(
        self,
        client: RealtimeClientProtocol | None = None,
        fallback_client: MockRealtimeClient | None = None,
    ) -> None:
        self.client = client or create_realtime_client()
        self.fallback_client = fallback_client

    async def search(
        self,
        *,
        keyword: str,
        category: RealtimeCategory,
        limit: int = 5,
    ) -> dict:
        raw_items, provider, mock, fallback_reason = await self._search_raw(
            keyword=keyword,
            category=category,
            limit=limit,
        )
        items = [
            self._normalize_item(raw=item, category=category, provider=provider)
            for item in raw_items[:limit]
        ]
        items.sort(key=lambda item: (item.published_at or "", item.credibility_score), reverse=True)
        result = RealtimeSearchResult(
            keyword=keyword,
            category=category,
            items=items,
            sources=self._source_summaries(items),
            realtime_info_summary=self._summary(keyword=keyword, category=category, items=items),
            provider=provider,
            source_updated_at=datetime.now(APP_TZ).isoformat(),
            mock=mock,
            fallback_reason=fallback_reason,
        )
        return result.model_dump(mode="json")

    async def _search_raw(
        self,
        *,
        keyword: str,
        category: RealtimeCategory,
        limit: int,
    ) -> tuple[list[dict[str, Any]], str, bool, str | None]:
        try:
            items = await self.client.search(
                keyword=keyword.strip(),
                category=category,
                limit=limit,
            )
            return items, self.client.provider, self.client.mock, None
        except (RealtimeClientError, Exception) as exc:
            logger.warning("realtime provider fallback: %s", exc)
            if self.fallback_client is None:
                raise
            items = await self.fallback_client.search(
                keyword=keyword.strip(),
                category=category,
                limit=limit,
            )
            return items, self.fallback_client.provider, self.fallback_client.mock, str(exc)

    def _normalize_item(
        self,
        *,
        raw: dict[str, Any],
        category: RealtimeCategory,
        provider: str,
    ) -> RealtimeItem:
        url = self._string_or_none(raw.get("url"))
        source = self._source(raw=raw, url=url, provider=provider)
        score = self._credibility_score(raw=raw, source=source, url=url, category=category)
        return RealtimeItem(
            title=self._string_or_default(raw.get("title"), self._category_title(category)),
            url=url,
            source=source,
            published_at=self._published_at(raw.get("published_at") or raw.get("published_date")),
            category=category,
            classification=self._classification(category),
            summary=self._string_or_default(raw.get("summary") or raw.get("content"), "暂无摘要。"),
            tags=self._tags(raw_tags=raw.get("tags"), category=category),
            credibility_score=score,
            credibility_label=self._credibility_label(score),
            source_type=self._string_or_none(raw.get("source_type")),
            raw=raw.get("raw") if isinstance(raw.get("raw"), dict) else {},
        )

    def _source(self, *, raw: dict[str, Any], url: str | None, provider: str) -> str:
        source = self._string_or_none(raw.get("source"))
        if source:
            return source
        if url:
            return urlparse(url).netloc or provider
        return provider

    def _published_at(self, value: Any) -> str | None:
        if isinstance(value, datetime):
            published_at = value if value.tzinfo else value.replace(tzinfo=APP_TZ)
            return published_at.isoformat()
        if not isinstance(value, str) or not value:
            return None
        normalized = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return value
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=APP_TZ)
        return parsed.isoformat()

    def _credibility_score(
        self,
        *,
        raw: dict[str, Any],
        source: str,
        url: str | None,
        category: RealtimeCategory,
    ) -> float:
        raw_score = raw.get("credibility_score", raw.get("score"))
        score = self._coerce_score(raw_score)
        if score is None:
            score = {
                "news": 76.0,
                "traffic": 80.0,
                "guide": 68.0,
                "pitfall": 64.0,
            }[category]

        source_text = f"{source} {url or ''}".lower()
        if any(token in source_text for token in ["gov", "政府", "交通", "公安", "文旅"]):
            score += 10
        if category in {"guide", "pitfall"} and any(
            token in source_text for token in ["blog", "bbs", "forum", "社区"]
        ):
            score -= 5
        return round(min(max(score, 0), 100), 1)

    def _coerce_score(self, value: Any) -> float | None:
        if isinstance(value, int | float):
            score = float(value)
            if 0 <= score <= 1:
                return score * 100
            return score
        return None

    def _credibility_label(self, score: float) -> str:
        if score >= 85:
            return "high"
        if score >= 70:
            return "medium"
        return "low"

    def _tags(self, *, raw_tags: Any, category: RealtimeCategory) -> list[str]:
        tags = [category, self._classification(category)]
        if isinstance(raw_tags, list):
            tags.extend(str(tag) for tag in raw_tags if tag)
        return list(dict.fromkeys(tags))

    def _source_summaries(self, items: list[RealtimeItem]) -> list[RealtimeSourceSummary]:
        grouped: dict[str, list[RealtimeItem]] = {}
        for item in items:
            grouped.setdefault(item.source, []).append(item)
        summaries = []
        for source, source_items in grouped.items():
            latest_values = [item.published_at for item in source_items if item.published_at]
            avg = sum(item.credibility_score for item in source_items) / len(source_items)
            summaries.append(
                RealtimeSourceSummary(
                    source=source,
                    item_count=len(source_items),
                    latest_published_at=max(latest_values) if latest_values else None,
                    credibility_avg=round(avg, 1),
                )
            )
        return sorted(summaries, key=lambda item: item.credibility_avg, reverse=True)

    def _summary(
        self,
        *,
        keyword: str,
        category: RealtimeCategory,
        items: list[RealtimeItem],
    ) -> str:
        label = self._category_label(category)
        if not items:
            return f"暂未检索到{keyword}相关{label}信息，建议出行前再次复核。"
        titles = "；".join(item.title for item in items[:3])
        sources = "、".join(dict.fromkeys(item.source for item in items[:3]))
        return f"{keyword}相关{label}共整理{len(items)}条，重点关注：{titles}。来源：{sources}。"

    def _classification(self, category: RealtimeCategory) -> str:
        values = {
            "news": "实时资讯",
            "traffic": "交通提醒",
            "guide": "攻略参考",
            "pitfall": "避坑参考",
        }
        return values[category]

    def _category_label(self, category: RealtimeCategory) -> str:
        return self._classification(category)

    def _category_title(self, category: RealtimeCategory) -> str:
        titles = {
            "news": "目的地实时资讯",
            "traffic": "景区周边交通提醒",
            "guide": "攻略参考提醒",
            "pitfall": "避坑参考提醒",
        }
        return titles[category]

    def _string_or_none(self, value: Any) -> str | None:
        return value if isinstance(value, str) and value else None

    def _string_or_default(self, value: Any, default: str) -> str:
        return value if isinstance(value, str) and value else default


realtime_service = RealtimeService()
