import asyncio
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.api.v1.endpoints import llm_configs
from app.schemas.llm_configs import LlmConfigCreateRequest, LlmConfigUpdateRequest
from app.services.llm_configs import LlmConfigsService


def make_config(**overrides):
    values = {
        "id": 1,
        "name": "默认模型",
        "provider": "openai-compatible",
        "base_url": "https://api.example.com/v1",
        "model_name": "gpt-4.1-mini",
        "api_key_encrypted": "hash",
        "api_key_masked": "sk-****abcd",
        "status": "disabled",
        "is_default": True,
        "timeout_s": 60,
        "max_tokens": 8000,
        "temperature": 0.7,
        "last_test_status": None,
        "last_test_message": None,
        "last_test_at": None,
        "created_by": 1,
        "updated_by": 1,
        "created_at": datetime(2026, 5, 21, 9, 0, 0),
        "deleted_at": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_llm_config_router_exposes_integration_contract_paths() -> None:
    paths = {route.path for route in llm_configs.router.routes}

    assert "/admin/llm_configs" in paths
    assert "/admin/llm_configs/{config_id}" in paths
    assert "/admin/llm_configs/{config_id}/test" in paths
    assert "/admin/llm_configs/{config_id}/enable" in paths
    assert "/admin/llm_configs/{config_id}/disable" in paths


def test_list_llm_configs_returns_paginated_payload() -> None:
    repo = SimpleNamespace(list_configs=AsyncMock(return_value=(1, [make_config()])))
    service = LlmConfigsService(repo=repo)

    data = asyncio.run(
        service.list_configs(db=SimpleNamespace(), page=1, page_size=20, status="disabled")
    )

    assert data["total"] == 1
    assert data["items"][0]["api_key_masked"] == "sk-****abcd"


def test_create_llm_config_masks_api_key_and_commits() -> None:
    async def create_config(_db, *, config):
        config.id = 1
        return config

    repo = SimpleNamespace(clear_default=AsyncMock(), create_config=create_config)
    db = SimpleNamespace(commit=AsyncMock())
    service = LlmConfigsService(repo=repo)

    data = asyncio.run(
        service.create_config(
            db,
            payload=LlmConfigCreateRequest(
                name="默认模型",
                provider="openai-compatible",
                base_url="https://api.example.com/v1",
                model_name="gpt-4.1-mini",
                api_key="sk-test-abcd",
                is_default=True,
            ),
            operator_id=1,
        )
    )

    assert data == {"id": 1, "api_key_masked": "sk-****abcd"}
    db.commit.assert_awaited_once()


def test_update_llm_config_changes_fields() -> None:
    config = make_config()
    repo = SimpleNamespace(get_config=AsyncMock(return_value=config), clear_default=AsyncMock())
    db = SimpleNamespace(commit=AsyncMock())
    service = LlmConfigsService(repo=repo)

    data = asyncio.run(
        service.update_config(
            db,
            config_id=1,
            payload=LlmConfigUpdateRequest(
                name="新模型",
                provider="deepseek",
                api_key="sk-new-key",
            ),
            operator_id=1,
        )
    )

    assert config.name == "新模型"
    assert config.provider == "deepseek"
    assert data["api_key_masked"] == "sk-****-key"
    db.commit.assert_awaited_once()


def test_update_llm_config_ignores_empty_api_key() -> None:
    config = make_config()
    repo = SimpleNamespace(get_config=AsyncMock(return_value=config), clear_default=AsyncMock())
    db = SimpleNamespace(commit=AsyncMock())
    service = LlmConfigsService(repo=repo)

    data = asyncio.run(
        service.update_config(
            db,
            config_id=1,
            payload=LlmConfigUpdateRequest(api_key=" "),
            operator_id=1,
        )
    )

    assert config.api_key_encrypted == "hash"
    assert config.api_key_masked == "sk-****abcd"
    assert data["api_key_masked"] == "sk-****abcd"
    db.commit.assert_awaited_once()


def test_test_config_uses_provided_test_prompt() -> None:
    config = make_config(api_key_encrypted="xor-v1:test")
    repo = SimpleNamespace(get_config=AsyncMock(return_value=config))
    db = SimpleNamespace(commit=AsyncMock())
    service = LlmConfigsService(repo=repo)

    class DummyClient:
        async def _chat_completion_async(self, prompt: str):
            self.prompt = prompt
            return {"choices": [{"message": {"content": "OK"}}]}

        def _extract_content(self, payload):
            return payload["choices"][0]["message"]["content"]

    dummy_client = DummyClient()
    service.client_from_config = lambda _config, max_tokens=None: dummy_client  # type: ignore[method-assign]

    data = asyncio.run(
        service.test_config(db, config_id=1, test_prompt="自定义测试内容")
    )

    assert dummy_client.prompt == "自定义测试内容"
    assert data["status"] == "success"
    assert data["message"] == "OK"
    db.commit.assert_awaited_once()
