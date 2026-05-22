import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.request import Request, urlopen

from app.core.config import get_settings
from app.schemas.generation import GenerateStreamRequest, GenerationStage


class LlmClientError(Exception):
    pass


class GenerationLlmClientProtocol(Protocol):
    async def stream_stage_tokens(
        self,
        request: GenerateStreamRequest,
        stage: GenerationStage,
    ) -> AsyncIterator[str]: ...


@dataclass
class LlmRuntimeConfig:
    provider: str
    base_url: str
    model_name: str
    api_key: str
    timeout_s: int = 60
    max_tokens: int | None = None
    temperature: float = 0.7


class OpenAICompatibleGenerationClient:
    def __init__(self, config: LlmRuntimeConfig) -> None:
        self.config = config

    async def stream_stage_tokens(
        self,
        request: GenerateStreamRequest,
        stage: GenerationStage,
    ) -> AsyncIterator[str]:
        prompt = self._stage_prompt(request, stage)
        payload = await self._chat_completion_async(prompt)
        content = self._extract_content(payload)
        if not content:
            raise LlmClientError("LLM 未返回内容")
        for line in self._chunks(content):
            yield line

    async def _chat_completion_async(self, prompt: str) -> dict[str, Any]:
        return await asyncio.to_thread(self._chat_completion, prompt)

    def _chat_completion(self, prompt: str) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": self.config.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "你是路书匠出行规划助手，输出简洁、可执行的中文规划内容。",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": self.config.temperature,
            "stream": False,
        }
        if self.config.max_tokens:
            body["max_tokens"] = self.config.max_tokens
        endpoint = self.config.base_url.rstrip("/") + "/chat/completions"
        request = Request(
            endpoint,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "RouteCraft/1.0",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.config.timeout_s) as response:
                raw_body = response.read()
                text = raw_body.decode("utf-8", errors="replace").strip()
                if not text:
                    raise LlmClientError(
                        f"LLM 接口返回空响应（endpoint: {endpoint}）"
                    )
                try:
                    payload = json.loads(text)
                except json.JSONDecodeError as exc:
                    headers = getattr(response, "headers", None)
                    content_type = ""
                    if headers is not None and hasattr(headers, "get"):
                        content_type = str(headers.get("Content-Type") or "")
                    snippet = " ".join(text.split())
                    if len(snippet) > 200:
                        snippet = f"{snippet[:200]}..."
                    detail = "LLM 接口返回非 JSON 响应"
                    if content_type:
                        detail = f"{detail}（Content-Type: {content_type}）"
                    raise LlmClientError(f"{detail}: {snippet}") from exc
                if not isinstance(payload, dict):
                    raise LlmClientError("LLM 响应格式错误")
                return payload
        except Exception as exc:
            if isinstance(exc, LlmClientError):
                raise
            raise LlmClientError(f"LLM 调用失败: {exc}") from exc

    def _extract_content(self, payload: dict[str, Any]) -> str:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise LlmClientError("LLM 响应缺少 choices")
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        if not isinstance(message, dict):
            raise LlmClientError("LLM 响应缺少 message")
        content = message.get("content")
        return content if isinstance(content, str) else ""

    def _chunks(self, content: str) -> list[str]:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        return lines or [content.strip()]

    def _stage_prompt(self, request: GenerateStreamRequest, stage: GenerationStage) -> str:
        labels = {
            "understanding": "理解用户需求",
            "weather": "结合天气给出风险提示",
            "route": "规划路线和路径点",
            "transport": "规划交通方式",
            "map_export": "说明地图链接和路线图用途",
            "attractions": "生成途径景点说明",
            "realtime": "整理实时信息检索结果",
            "summary": "汇总最终规划建议",
        }
        return (
            f"阶段：{labels[stage]}\n"
            f"起点：{request.origin}\n"
            f"目的地：{request.destination}\n"
            f"范围：{request.range}\n"
            f"交通方式：{request.transport_mode}\n"
            f"日期：{request.travel_date.isoformat() if request.travel_date else '未指定'}\n"
            f"人数：{request.people_count or '未指定'}\n"
            f"偏好：{'、'.join(request.preferences) or '无'}\n"
            f"避免项：{'、'.join(request.avoidances) or '无'}\n"
            "请只输出该阶段的 1-3 条中文要点。"
        )


def create_llm_client_from_settings() -> GenerationLlmClientProtocol:
    settings = get_settings()
    if not settings.llm_base_url or not settings.llm_model_name or not settings.llm_api_key:
        raise LlmClientError(
            "未配置真实 LLM：请设置 BACKEND_LLM_BASE_URL、"
            "BACKEND_LLM_MODEL_NAME、BACKEND_LLM_API_KEY"
        )
    return OpenAICompatibleGenerationClient(
        LlmRuntimeConfig(
            provider=settings.llm_provider,
            base_url=settings.llm_base_url,
            model_name=settings.llm_model_name,
            api_key=settings.llm_api_key,
            timeout_s=settings.llm_timeout_s,
            max_tokens=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
        )
    )
