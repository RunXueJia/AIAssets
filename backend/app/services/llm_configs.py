import time
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.security import decrypt_secret, encrypt_secret
from app.integrations.llm import (
    SUPPORTED_API_FORMATS,
    LlmRuntimeConfig,
    OpenAICompatibleGenerationClient,
)
from app.models import LlmConfig
from app.repositories.llm_configs import LlmConfigsRepository
from app.schemas.llm_configs import (
    LlmConfigCreateRequest,
    LlmConfigDetail,
    LlmConfigListItem,
    LlmConfigMutationResponse,
    LlmConfigStatusResponse,
    LlmConfigUpdateRequest,
    PaginationResponse,
)


class LlmConfigsService:
    def __init__(self, repo: LlmConfigsRepository | None = None) -> None:
        self.repo = repo or LlmConfigsRepository()

    async def list_configs(
        self,
        db: AsyncSession,
        *,
        page: int,
        page_size: int,
        status: str | None = None,
    ) -> dict[str, Any]:
        page, page_size = max(page, 1), min(max(page_size, 1), 100)
        total, configs = await self.repo.list_configs(
            db,
            page=page,
            page_size=page_size,
            status=self._blank_to_none(status),
        )
        items = [self._list_item(config).model_dump(mode="json") for config in configs]
        return PaginationResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=items,
        ).model_dump(mode="json")

    async def create_config(
        self,
        db: AsyncSession,
        *,
        payload: LlmConfigCreateRequest,
        operator_id: int,
    ) -> dict[str, Any]:
        if payload.is_default:
            await self.repo.clear_default(db)
        self._validate_api_format(payload.api_format)
        config = LlmConfig(
            name=payload.name,
            provider=payload.provider,
            api_format=payload.api_format,
            base_url=payload.base_url,
            model_name=payload.model_name,
            api_key_encrypted=self._encrypt_api_key(payload.api_key),
            api_key_masked=self._mask_api_key(payload.api_key),
            status="disabled",
            is_default=payload.is_default,
            timeout_s=payload.timeout_s,
            max_tokens=payload.max_tokens,
            temperature=payload.temperature,
            created_by=operator_id,
            updated_by=operator_id,
        )
        await self.repo.create_config(db, config=config)
        await db.commit()
        return LlmConfigMutationResponse(
            id=config.id,
            api_key_masked=config.api_key_masked,
        ).model_dump(mode="json")

    async def get_detail(self, db: AsyncSession, *, config_id: int) -> dict[str, Any]:
        config = await self._require_config(db, config_id=config_id)
        return self._detail(config).model_dump(mode="json")

    async def update_config(
        self,
        db: AsyncSession,
        *,
        config_id: int,
        payload: LlmConfigUpdateRequest,
        operator_id: int,
    ) -> dict[str, Any]:
        config = await self._require_config(db, config_id=config_id)
        if payload.is_default is True:
            await self.repo.clear_default(db)

        update_data = payload.model_dump(exclude_unset=True)
        api_key = update_data.pop("api_key", None)
        api_format = update_data.get("api_format")
        if api_format is not None:
            self._validate_api_format(api_format)
        for field, value in update_data.items():
            setattr(config, field, value)
        if api_key is not None and api_key.strip():
            config.api_key_encrypted = self._encrypt_api_key(api_key)
            config.api_key_masked = self._mask_api_key(api_key)
        config.updated_by = operator_id
        await db.commit()
        return LlmConfigMutationResponse(
            id=config.id,
            api_key_masked=config.api_key_masked,
        ).model_dump(mode="json")

    async def test_config(
        self,
        db: AsyncSession,
        *,
        config_id: int,
        test_prompt: str = "请回复 OK",
    ) -> dict[str, Any]:
        config = await self._require_config(db, config_id=config_id)
        started_at = time.perf_counter()
        client = self.client_from_config(config, max_tokens=16)
        try:
            payload = await client._chat_completion_async(test_prompt)
            message = client._extract_content(payload) or "OK"
            config.last_test_status = "success"
            config.last_test_message = message[:500]
        except Exception as exc:
            config.last_test_status = "failed"
            config.last_test_message = str(exc)[:500]
        config.last_test_at = datetime.now()
        await db.commit()
        return {
            "status": config.last_test_status,
            "message": config.last_test_message,
            "duration_ms": int((time.perf_counter() - started_at) * 1000),
            "tested_at": config.last_test_at.isoformat(),
        }

    async def stream_test_config(
        self,
        db: AsyncSession,
        *,
        config_id: int,
        test_prompt: str = "请回复 OK",
    ) -> AsyncIterator[dict[str, Any]]:
        config = await self._require_config(db, config_id=config_id)
        started_at = time.perf_counter()
        client = self.client_from_config(config, max_tokens=512)
        content_parts: list[str] = []
        yield {
            "type": "start",
            "status": "streaming",
            "config_id": config.id,
            "api_format": self._config_api_format(config),
            "model_name": config.model_name,
        }
        try:
            async for token in client.stream_text_tokens(test_prompt):
                content_parts.append(token)
                yield {"type": "token", "content": token}
            message = "".join(content_parts).strip() or "OK"
            config.last_test_status = "success"
            config.last_test_message = message[:500]
            config.last_test_at = datetime.now()
            await db.commit()
            yield {
                "type": "done",
                "status": "success",
                "message": config.last_test_message,
                "duration_ms": int((time.perf_counter() - started_at) * 1000),
                "tested_at": config.last_test_at.isoformat(),
            }
        except Exception as exc:
            config.last_test_status = "failed"
            config.last_test_message = str(exc)[:500]
            config.last_test_at = datetime.now()
            await db.commit()
            yield {
                "type": "error",
                "status": "failed",
                "message": config.last_test_message,
                "duration_ms": int((time.perf_counter() - started_at) * 1000),
                "tested_at": config.last_test_at.isoformat(),
            }

    async def get_generation_client(self, db: AsyncSession) -> OpenAICompatibleGenerationClient:
        config = await self.repo.get_active_default_config(db)
        if config is None:
            raise AppException("未找到已启用的 LLM 配置", code=500, status_code=500)
        return self.client_from_config(config)

    def client_from_config(
        self,
        config: LlmConfig,
        *,
        max_tokens: int | None = None,
    ) -> OpenAICompatibleGenerationClient:
        if not config.api_key_encrypted.startswith("xor-v1:"):
            raise AppException(
                "LLM API Key 是旧版不可解密存储，请在后台重新保存该配置的 API Key",
                code=500,
                status_code=500,
            )
        api_key = self._decrypt_api_key(config.api_key_encrypted)
        return OpenAICompatibleGenerationClient(
            LlmRuntimeConfig(
                provider=config.provider,
                api_format=self._config_api_format(config),
                base_url=config.base_url,
                model_name=config.model_name,
                api_key=api_key,
                timeout_s=config.timeout_s,
                max_tokens=max_tokens if max_tokens is not None else config.max_tokens,
                temperature=float(config.temperature or 0),
            )
        )

    async def change_status(
        self,
        db: AsyncSession,
        *,
        config_id: int,
        status: str,
    ) -> dict[str, Any]:
        config = await self._require_config(db, config_id=config_id)
        config.status = status
        await db.commit()
        return LlmConfigStatusResponse(id=config.id, status=config.status).model_dump(mode="json")

    async def _require_config(self, db: AsyncSession, *, config_id: int) -> LlmConfig:
        config = await self.repo.get_config(db, config_id=config_id)
        if config is None:
            raise AppException("LLM 配置不存在", code=404, status_code=404)
        return config

    def _list_item(self, config: LlmConfig) -> LlmConfigListItem:
        return LlmConfigListItem(
            id=config.id,
            name=config.name,
            provider=config.provider,
            api_format=self._config_api_format(config),
            base_url=config.base_url,
            model_name=config.model_name,
            api_key_masked=config.api_key_masked,
            status=config.status,
            is_default=config.is_default,
            last_test_status=config.last_test_status,
            last_test_at=config.last_test_at,
        )

    def _detail(self, config: LlmConfig) -> LlmConfigDetail:
        return LlmConfigDetail(
            **self._list_item(config).model_dump(),
            timeout_s=config.timeout_s,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            last_test_message=config.last_test_message,
        )

    def _mask_api_key(self, api_key: str) -> str:
        if len(api_key) <= 8:
            return f"{api_key[:2]}****"
        return f"{api_key[:3]}****{api_key[-4:]}"

    def _encrypt_api_key(self, api_key: str) -> str:
        return encrypt_secret(api_key, get_settings().llm_secret_key)

    def _decrypt_api_key(self, api_key_encrypted: str) -> str:
        return decrypt_secret(api_key_encrypted, get_settings().llm_secret_key)

    def _validate_api_format(self, api_format: str) -> None:
        if api_format not in SUPPORTED_API_FORMATS:
            raise AppException(f"不支持的 LLM API 格式：{api_format}", code=400, status_code=400)

    def _config_api_format(self, config: LlmConfig) -> str:
        return getattr(config, "api_format", None) or "openai_chat_completions"

    def _blank_to_none(self, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None
