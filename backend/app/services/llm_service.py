#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 10:50
# @File     : llm_service.py
# @Desc     : OpenAI-compatible LLM client and structured generation helpers.

import json
from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.entities import SystemSetting


@dataclass
class LLMConfig:
    provider: str
    base_url: str
    api_key: str
    model_name: str
    timeout_seconds: int
    enable_real_calls: bool


def _setting_value(db: Session, key: str, default: Any = None) -> Any:
    setting = db.query(SystemSetting).filter(SystemSetting.setting_key == key).one_or_none()
    if setting is None:
        return default
    return setting.setting_value_json if setting.setting_value_json not in (None, "") else default


def get_llm_config(db: Session) -> LLMConfig:
    return LLMConfig(
        provider=str(_setting_value(db, "model_provider", settings.llm_model_provider)),
        base_url=str(_setting_value(db, "model_base_url", settings.llm_model_base_url)).rstrip("/"),
        api_key=str(_setting_value(db, "model_api_key", settings.llm_model_api_key) or ""),
        model_name=str(_setting_value(db, "model_name", settings.llm_model_name) or "gpt-4o-mini"),
        timeout_seconds=int(_setting_value(db, "model_timeout_seconds", settings.llm_request_timeout_seconds)),
        enable_real_calls=settings.llm_enable_real_calls,
    )


def chat_json(db: Session, messages: list[dict[str, str]], fallback: dict[str, Any]) -> tuple[dict[str, Any], str, str]:
    config = get_llm_config(db)
    if not config.enable_real_calls or not config.api_key or not config.base_url:
        return fallback, "local_fallback", "LLM real calls disabled or missing api key."

    payload = {
        "model": config.model_name,
        "messages": messages,
        "temperature": 0.4,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {config.api_key}", "Content-Type": "application/json"}
    with httpx.Client(timeout=config.timeout_seconds) as client:
        response = client.post(f"{config.base_url}/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
    raw = response.text
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        parsed = fallback
    return parsed, config.model_name, raw


def build_generation_prompt(task_payload: dict[str, Any], summary_text: str, source_titles: list[str]) -> list[dict[str, str]]:
    system = (
        "你是AI科普短视频内容策划助手。只基于给定素材生成内容，不编造事实；"
        "输出严格 JSON，字段包含 summary、key_points、risk_notes、topics、script、storyboards。"
    )
    user = {
        "task": task_payload,
        "source_summary": summary_text,
        "source_titles": source_titles,
        "requirements": [
            "生成不少于10个候选选题",
            "脚本适合60秒短视频",
            "分镜6到10个",
            "标记不确定事实和夸张表达风险",
        ],
    }
    return [{"role": "system", "content": system}, {"role": "user", "content": json.dumps(user, ensure_ascii=False)}]
