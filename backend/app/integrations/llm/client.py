import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from threading import Thread
from typing import Any, Protocol
from urllib.error import HTTPError
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from app.core.config import get_settings
from app.schemas.generation import GenerateStreamRequest, GenerationStage

API_FORMAT_OPENAI_CHAT = "openai_chat_completions"
API_FORMAT_OPENAI_RESPONSES = "openai_responses"
API_FORMAT_ANTHROPIC_MESSAGES = "anthropic_messages"
API_FORMAT_GEMINI_GENERATE_CONTENT = "gemini_generate_content"

SUPPORTED_API_FORMATS = {
    API_FORMAT_OPENAI_CHAT,
    API_FORMAT_OPENAI_RESPONSES,
    API_FORMAT_ANTHROPIC_MESSAGES,
    API_FORMAT_GEMINI_GENERATE_CONTENT,
}

SYSTEM_PROMPT = "你是路书匠出行规划助手，输出简洁、可执行的中文规划内容。"


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
    api_format: str = API_FORMAT_OPENAI_CHAT
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
        has_content = False
        async for token in self.stream_text_tokens(prompt):
            has_content = True
            yield token
        if not has_content:
            raise LlmClientError("LLM 未返回内容")

    async def stream_text_tokens(self, prompt: str) -> AsyncIterator[str]:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[Any] = asyncio.Queue()
        done = object()

        def publish(item: Any) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, item)

        def worker() -> None:
            try:
                for token in self._stream_text_sync(prompt):
                    publish(token)
            except Exception as exc:  # pragma: no cover - surfaced through async queue
                publish(exc)
            finally:
                publish(done)

        Thread(target=worker, daemon=True).start()

        while True:
            item = await queue.get()
            if item is done:
                break
            if isinstance(item, Exception):
                raise item
            yield str(item)

    async def _chat_completion_async(self, prompt: str) -> dict[str, Any]:
        return await asyncio.to_thread(self._chat_completion, prompt)

    def _chat_completion(self, prompt: str) -> dict[str, Any]:
        request, endpoint = self._build_request(prompt, stream=False)
        try:
            with urlopen(request, timeout=self.config.timeout_s) as response:
                return self._decode_json_response(response, endpoint)
        except Exception as exc:
            if isinstance(exc, LlmClientError):
                raise
            if isinstance(exc, HTTPError):
                raise LlmClientError(self._http_error_message(exc)) from exc
            raise LlmClientError(f"LLM 调用失败: {exc}") from exc

    def _stream_text_sync(self, prompt: str):
        request, endpoint = self._build_request(prompt, stream=True)
        try:
            with urlopen(request, timeout=self.config.timeout_s) as response:
                self._ensure_stream_response(response, endpoint)
                for payload in self._iter_stream_payloads(response, endpoint):
                    self._raise_for_error_payload(payload)
                    yield from self._extract_stream_text(payload)
        except Exception as exc:
            if isinstance(exc, LlmClientError):
                raise
            if isinstance(exc, HTTPError):
                raise LlmClientError(self._http_error_message(exc)) from exc
            raise LlmClientError(f"LLM 流式调用失败: {exc}") from exc

    def _build_request(self, prompt: str, *, stream: bool) -> tuple[Request, str]:
        api_format = self._api_format()
        endpoint = self._endpoint(api_format, stream=stream)
        body = self._request_body(api_format, prompt, stream=stream)
        return (
            Request(
                endpoint,
                data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                headers=self._headers(api_format),
                method="POST",
            ),
            endpoint,
        )

    def _api_format(self) -> str:
        api_format = (self.config.api_format or API_FORMAT_OPENAI_CHAT).strip()
        if api_format not in SUPPORTED_API_FORMATS:
            raise LlmClientError(f"不支持的 LLM API 格式：{api_format}")
        return api_format

    def _endpoint(self, api_format: str, *, stream: bool) -> str:
        base_url = self.config.base_url.rstrip("/")
        if api_format == API_FORMAT_OPENAI_CHAT:
            if base_url.endswith("/chat/completions"):
                return self._normalize_url(base_url)
            return self._normalize_url(f"{base_url}/chat/completions")
        if api_format == API_FORMAT_OPENAI_RESPONSES:
            if base_url.endswith("/responses"):
                return self._normalize_url(base_url)
            return self._normalize_url(f"{base_url}/responses")
        if api_format == API_FORMAT_ANTHROPIC_MESSAGES:
            if base_url.endswith("/messages"):
                return self._normalize_url(base_url)
            return self._normalize_url(f"{base_url}/messages")
        if api_format == API_FORMAT_GEMINI_GENERATE_CONTENT:
            suffix = "streamGenerateContent?alt=sse" if stream else "generateContent"
            if ":generateContent" in base_url or ":streamGenerateContent" in base_url:
                return self._normalize_url(base_url)
            model_path = self._gemini_model_path()
            return self._normalize_url(f"{base_url}/{model_path}:{suffix}")
        raise LlmClientError(f"不支持的 LLM API 格式：{api_format}")

    def _headers(self, api_format: str) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "RouteCraft/1.0",
        }
        if api_format == API_FORMAT_ANTHROPIC_MESSAGES:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
            headers["x-api-key"] = self.config.api_key
            headers["anthropic-version"] = "2023-06-01"
        elif api_format == API_FORMAT_GEMINI_GENERATE_CONTENT:
            headers["x-goog-api-key"] = self.config.api_key
        else:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    def _request_body(self, api_format: str, prompt: str, *, stream: bool) -> dict[str, Any]:
        if api_format == API_FORMAT_OPENAI_CHAT:
            body: dict[str, Any] = {
                "model": self.config.model_name,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "temperature": self.config.temperature,
                "stream": stream,
            }
            if self.config.max_tokens:
                body["max_tokens"] = self.config.max_tokens
            return body

        if api_format == API_FORMAT_OPENAI_RESPONSES:
            body = {
                "model": self.config.model_name,
                "instructions": SYSTEM_PROMPT,
                "input": prompt,
                "temperature": self.config.temperature,
                "stream": stream,
            }
            if self.config.max_tokens:
                body["max_output_tokens"] = self.config.max_tokens
            return body

        if api_format == API_FORMAT_ANTHROPIC_MESSAGES:
            body = {
                "model": self.config.model_name,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": self.config.max_tokens or 1024,
                "temperature": self.config.temperature,
                "stream": stream,
            }
            return body

        if api_format == API_FORMAT_GEMINI_GENERATE_CONTENT:
            generation_config: dict[str, Any] = {"temperature": self.config.temperature}
            if self.config.max_tokens:
                generation_config["maxOutputTokens"] = self.config.max_tokens
            return {
                "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": generation_config,
            }

        raise LlmClientError(f"不支持的 LLM API 格式：{api_format}")

    def _decode_json_response(self, response: Any, endpoint: str) -> dict[str, Any]:
        raw_body = response.read()
        text = raw_body.decode("utf-8", errors="replace").strip()
        if not text:
            raise LlmClientError(f"LLM 接口返回空响应（endpoint: {endpoint}）")
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            headers = getattr(response, "headers", None)
            content_type = ""
            if headers is not None and hasattr(headers, "get"):
                content_type = str(headers.get("Content-Type") or "")
            detail = "LLM 接口返回非 JSON 响应"
            if content_type:
                detail = f"{detail}（Content-Type: {content_type}）"
            raise LlmClientError(f"{detail}: {self._snippet(text)}") from exc
        if not isinstance(payload, dict):
            raise LlmClientError("LLM 响应格式错误")
        self._raise_for_error_payload(payload)
        return payload

    def _ensure_stream_response(self, response: Any, endpoint: str) -> None:
        headers = getattr(response, "headers", None)
        content_type = ""
        if headers is not None and hasattr(headers, "get"):
            content_type = str(headers.get("Content-Type") or "").lower()
        if "text/html" not in content_type:
            return
        text = response.read().decode("utf-8", errors="replace").strip()
        raise LlmClientError(
            "LLM 流式接口返回 HTML 页面，请检查 API 地址和 API 格式"
            f"（endpoint: {endpoint}）: {self._snippet(text)}"
        )

    def _iter_stream_payloads(self, response: Any, endpoint: str):
        data_lines: list[str] = []
        for raw_line in response:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line or line == "\r":
                if data_lines:
                    text = "\n".join(data_lines).strip()
                    data_lines = []
                    if text == "[DONE]":
                        return
                    yield self._load_stream_payload(text, endpoint)
                continue
            if line.startswith(":") or line.startswith("event:"):
                continue
            if line.startswith("data:"):
                data_lines.append(line[5:].strip())
                continue
            if line.startswith("{"):
                yield self._load_stream_payload(line, endpoint)

        if data_lines:
            text = "\n".join(data_lines).strip()
            if text != "[DONE]":
                yield self._load_stream_payload(text, endpoint)

    def _load_stream_payload(self, text: str, endpoint: str) -> dict[str, Any]:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise LlmClientError(
                f"LLM 流式响应不是合法 JSON（endpoint: {endpoint}）: {self._snippet(text)}"
            ) from exc
        if not isinstance(payload, dict):
            raise LlmClientError("LLM 流式响应格式错误")
        return payload

    def _raise_for_error_payload(self, payload: dict[str, Any]) -> None:
        error = payload.get("error")
        if isinstance(error, dict):
            message = error.get("message") or error.get("type") or "LLM 接口返回错误"
            raise LlmClientError(str(message))
        if isinstance(error, str) and error:
            raise LlmClientError(error)
        if payload.get("type") == "error":
            raise LlmClientError(str(payload.get("message") or "LLM 接口返回错误"))

    def _extract_content(self, payload: dict[str, Any]) -> str:
        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message") if isinstance(choices[0], dict) else None
            if isinstance(message, dict):
                return self._content_to_text(message.get("content"))

        output_text = payload.get("output_text")
        if isinstance(output_text, str):
            return output_text
        output = payload.get("output")
        if isinstance(output, list):
            return "".join(
                self._content_to_text(item.get("content"))
                for item in output
                if isinstance(item, dict)
            )

        content = payload.get("content")
        if isinstance(content, list):
            return self._content_to_text(content)

        candidates = payload.get("candidates")
        if isinstance(candidates, list) and candidates:
            first = candidates[0] if isinstance(candidates[0], dict) else {}
            candidate_content = first.get("content") if isinstance(first, dict) else {}
            if isinstance(candidate_content, dict):
                return self._content_to_text(candidate_content.get("parts"))

        raise LlmClientError("LLM 响应缺少可解析文本内容")

    def _extract_stream_text(self, payload: dict[str, Any]):
        event_type = payload.get("type")
        if event_type in {
            "response.output_text.delta",
            "response.refusal.delta",
            "response.reasoning_text.delta",
        }:
            delta = payload.get("delta")
            if isinstance(delta, str):
                yield delta
            return

        if event_type == "content_block_delta":
            delta = payload.get("delta")
            if isinstance(delta, dict):
                text = delta.get("text") or delta.get("thinking")
                if isinstance(text, str):
                    yield text
            return

        choices = payload.get("choices")
        if isinstance(choices, list):
            for choice in choices:
                if not isinstance(choice, dict):
                    continue
                delta = choice.get("delta")
                if isinstance(delta, dict):
                    text = self._content_to_text(delta.get("content"))
                    if text:
                        yield text

        candidates = payload.get("candidates")
        if isinstance(candidates, list):
            for candidate in candidates:
                if not isinstance(candidate, dict):
                    continue
                content = candidate.get("content")
                if isinstance(content, dict):
                    text = self._content_to_text(content.get("parts"))
                    if text:
                        yield text

    def _content_to_text(self, content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, dict):
            for key in ("text", "content"):
                value = content.get(key)
                if isinstance(value, str):
                    return value
            return ""
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, str):
                    parts.append(part)
                elif isinstance(part, dict):
                    value = part.get("text") or part.get("content")
                    if isinstance(value, str):
                        parts.append(value)
            return "".join(parts)
        return ""

    def _chunks(self, content: str) -> list[str]:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        return lines or [content.strip()]

    def _gemini_model_path(self) -> str:
        model_name = self.config.model_name.strip()
        if model_name.startswith("models/") or "/" in model_name:
            return quote(model_name, safe="/")
        return f"models/{quote(model_name, safe='')}"

    def _http_error_message(self, exc: HTTPError) -> str:
        text = exc.read().decode("utf-8", errors="replace").strip()
        if text:
            message = self._error_message_from_text(text) or self._snippet(text)
            return f"LLM 调用失败: HTTP {exc.code} {exc.reason}: {message}"
        return f"LLM 调用失败: HTTP {exc.code} {exc.reason}"

    def _error_message_from_text(self, text: str) -> str | None:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None
        error = payload.get("error")
        if isinstance(error, dict):
            message = error.get("message") or error.get("type")
            return str(message) if message else None
        if isinstance(error, str) and error:
            return error
        return None

    def _snippet(self, text: str) -> str:
        snippet = " ".join(text.split())
        if len(snippet) > 200:
            return f"{snippet[:200]}..."
        return snippet

    def _normalize_url(self, url: str) -> str:
        parts = urlsplit(url)
        path = "/".join(part for part in parts.path.split("/") if part)
        normalized_path = f"/{path}" if path else ""
        return urlunsplit(
            (parts.scheme, parts.netloc, normalized_path, parts.query, parts.fragment)
        )

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
            api_format=settings.llm_api_format,
            timeout_s=settings.llm_timeout_s,
            max_tokens=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
        )
    )
