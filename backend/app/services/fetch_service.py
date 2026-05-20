#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 10:50
# @File     : fetch_service.py
# @Desc     : Public web fetching and article extraction service.

import hashlib
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings


@dataclass
class FetchedSource:
    title: str
    site_name: str
    url: str
    published_at: datetime | None
    summary_text: str
    relevance_reason: str
    key_points: list[str]
    raw_content: str
    status: str = "usable"
    need_human_confirm: bool = False
    fetch_status: str = "success"
    fetch_error_message: str | None = None

    @property
    def source_hash(self) -> str:
        return hashlib.sha256(self.url.encode("utf-8")).hexdigest()


def _extract_text(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    meta_title = soup.find("meta", attrs={"property": "og:title"}) or soup.find("meta", attrs={"name": "title"})
    if meta_title and meta_title.get("content"):
        title = str(meta_title["content"]).strip()
    chunks = [text.strip() for text in soup.stripped_strings if text.strip()]
    content = "\n".join(chunks)
    return title[:255] or "未命名公开来源", content[: settings.fetch_max_content_chars]


def fetch_public_sources(direction: str, topic: str | None, audience: str | None) -> list[FetchedSource]:
    keyword = topic or direction
    sources: list[FetchedSource] = []
    headers = {
        "User-Agent": "hours24-ai-growth-engine/0.1 (+https://localhost)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    with httpx.Client(timeout=settings.fetch_timeout_seconds, follow_redirects=True, headers=headers) as client:
        for url in settings.fetch_seed_url_list:
            try:
                response = client.get(url)
                response.raise_for_status()
                title, content = _extract_text(response.text)
                parsed = urlparse(str(response.url))
                summary = content[:500] if content else f"公开页面与“{keyword}”相关，等待人工确认。"
                sources.append(
                    FetchedSource(
                        title=title,
                        site_name=parsed.netloc or "公开网页",
                        url=str(response.url),
                        published_at=None,
                        summary_text=summary,
                        relevance_reason=f"根据抓取关键词“{keyword}”进入素材池，适用于目标受众：{audience or '未指定'}。",
                        key_points=[keyword, "公开来源", "需人工确认事实"],
                        raw_content=content,
                        need_human_confirm=True,
                    )
                )
            except Exception as exc:
                parsed = urlparse(url)
                sources.append(
                    FetchedSource(
                        title=f"抓取失败：{parsed.netloc or url}",
                        site_name=parsed.netloc or "公开网页",
                        url=url,
                        published_at=None,
                        summary_text="抓取失败，已记录原因。",
                        relevance_reason=f"与“{keyword}”相关的抓取种子页面。",
                        key_points=[],
                        raw_content="",
                        status="uncertain",
                        need_human_confirm=True,
                        fetch_status="failed",
                        fetch_error_message=str(exc)[:500],
                    )
                )
    return sources
