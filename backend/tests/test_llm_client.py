from unittest.mock import patch

import pytest

from app.integrations.llm.client import (
    LlmClientError,
    LlmRuntimeConfig,
    OpenAICompatibleGenerationClient,
)


class _FakeResponse:
    def __init__(self, body: bytes, content_type: str = "application/json") -> None:
        self._body = body
        self.headers = {"Content-Type": content_type}

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


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
