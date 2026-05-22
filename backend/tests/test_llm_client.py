from unittest.mock import patch
from urllib.error import URLError

import pytest

from app.integrations.llm.client import (
    API_FORMAT_ANTHROPIC_MESSAGES,
    API_FORMAT_GEMINI_GENERATE_CONTENT,
    API_FORMAT_OPENAI_RESPONSES,
    LlmClientError,
    LlmRuntimeConfig,
    OpenAICompatibleGenerationClient,
)
from app.schemas.generation import GenerateStreamRequest


class _FakeResponse:
    def __init__(self, body: bytes, content_type: str = "application/json") -> None:
        self._body = body
        self.headers = {"Content-Type": content_type}

    def read(self) -> bytes:
        return self._body

    def __iter__(self):
        return iter(self._body.splitlines(keepends=True))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FailingStreamResponse(_FakeResponse):
    def __init__(self, lines: list[bytes], error: Exception) -> None:
        super().__init__(b"", "text/event-stream")
        self._lines = lines
        self._error = error

    def __iter__(self):
        yield from self._lines
        raise self._error


def _client() -> OpenAICompatibleGenerationClient:
    return OpenAICompatibleGenerationClient(
        LlmRuntimeConfig(
            provider="openai-compatible",
            base_url="https://api.example.com/v1",
            model_name="gpt-4.1-mini",
            api_key="test-key",
        )
    )


def test_chat_completion_rejects_empty_response() -> None:
    client = _client()

    with patch("app.integrations.llm.client.urlopen", return_value=_FakeResponse(b"")):
        with pytest.raises(LlmClientError) as exc_info:
            client._chat_completion("hello")

    assert "空响应" in str(exc_info.value)


def test_chat_completion_rejects_non_json_response() -> None:
    client = _client()

    with patch(
        "app.integrations.llm.client.urlopen",
        return_value=_FakeResponse(b"<html>bad gateway</html>", "text/html"),
    ):
        with pytest.raises(LlmClientError) as exc_info:
            client._chat_completion("hello")

    assert "非 JSON 响应" in str(exc_info.value)
    assert "text/html" in str(exc_info.value)


def test_responses_api_stream_extracts_output_text_delta() -> None:
    client = OpenAICompatibleGenerationClient(
        LlmRuntimeConfig(
            provider="openai",
            api_format=API_FORMAT_OPENAI_RESPONSES,
            base_url="https://api.example.com/v1",
            model_name="gpt-4.1-mini",
            api_key="test-key",
        )
    )
    body = (
        b'data: {"type":"response.output_text.delta","delta":"O"}\n\n'
        b'data: {"type":"response.output_text.delta","delta":"K"}\n\n'
        b"data: [DONE]\n\n"
    )

    with patch("app.integrations.llm.client.urlopen", return_value=_FakeResponse(body)):
        assert list(client._stream_text_sync("hello")) == ["O", "K"]


def test_stream_retries_transient_connection_reset_before_first_token() -> None:
    client = _client()
    body = b'data: {"choices":[{"delta":{"content":"OK"}}]}\n\n'

    with patch(
        "app.integrations.llm.client.urlopen",
        side_effect=[URLError("connection reset"), _FakeResponse(body, "text/event-stream")],
    ) as mocked_urlopen:
        assert list(client._stream_text_sync("hello")) == ["OK"]

    assert mocked_urlopen.call_count == 2


def test_stream_does_not_retry_after_tokens_were_emitted() -> None:
    client = _client()
    response = _FailingStreamResponse(
        [b'data: {"choices":[{"delta":{"content":"O"}}]}\n', b"\n"],
        URLError("connection reset"),
    )

    with patch("app.integrations.llm.client.urlopen", return_value=response) as mocked_urlopen:
        stream = client._stream_text_sync("hello")
        assert next(stream) == "O"
        with pytest.raises(LlmClientError) as exc_info:
            next(stream)

    assert mocked_urlopen.call_count == 1
    assert "connection reset" in str(exc_info.value)


def test_anthropic_messages_stream_extracts_text_delta() -> None:
    client = OpenAICompatibleGenerationClient(
        LlmRuntimeConfig(
            provider="anthropic",
            api_format=API_FORMAT_ANTHROPIC_MESSAGES,
            base_url="https://api.anthropic.com/v1",
            model_name="claude-3-5-sonnet-latest",
            api_key="test-key",
        )
    )
    body = (
        b'event: content_block_delta\n'
        b'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"OK"}}\n\n'
    )

    with patch("app.integrations.llm.client.urlopen", return_value=_FakeResponse(body)):
        assert list(client._stream_text_sync("hello")) == ["OK"]


def test_gemini_stream_extracts_candidate_parts() -> None:
    client = OpenAICompatibleGenerationClient(
        LlmRuntimeConfig(
            provider="gemini",
            api_format=API_FORMAT_GEMINI_GENERATE_CONTENT,
            base_url="https://generativelanguage.googleapis.com/v1beta",
            model_name="gemini-1.5-flash",
            api_key="test-key",
        )
    )
    body = (
        b'data: {"candidates":[{"content":{"parts":[{"text":"O"}]}}]}\n\n'
        b'data: {"candidates":[{"content":{"parts":[{"text":"K"}]}}]}\n\n'
    )

    with patch("app.integrations.llm.client.urlopen", return_value=_FakeResponse(body)):
        assert list(client._stream_text_sync("hello")) == ["O", "K"]


def test_realtime_stage_prompt_requires_ordered_markdown_list() -> None:
    prompt = _client()._stage_prompt(
        GenerateStreamRequest(origin="杭州东站", destination="西湖景区", range="一天"),
        "realtime",
    )

    assert "Markdown 有序列表" in prompt
    assert "1." in prompt
    assert "2." in prompt
