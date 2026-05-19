import json
import time
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import decrypt_text
from app.integrations.llm.openai_compatible import OpenAICompatibleClient
from app.models.llm import LLMCallLog, LLMModel, LLMStreamChunk, PromptTemplate
from app.services.llm_output_parser import LLMOutputParser
from app.services.prompt_render import PromptRenderService


class LLMGatewayService:
    def __init__(self) -> None:
        self.prompt_render = PromptRenderService()
        self.parser = LLMOutputParser()

    async def stream_prompt(
        self,
        db: AsyncSession,
        *,
        model: LLMModel,
        template: PromptTemplate,
        variables: dict,
        target_type: str | None = None,
        target_id: str | None = None,
        task_id: str | None = None,
    ) -> AsyncIterator[str]:
        provider = model.provider
        messages = self.prompt_render.render(template, variables)
        request_payload = {
            "model": model.model_name,
            "messages": messages,
            "temperature": model.temperature,
            "max_tokens": model.max_output_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        call_log = LLMCallLog(
            task_id=task_id,
            target_type=target_type,
            target_id=target_id,
            scene=template.scene,
            provider_id=provider.id,
            model_id=model.id,
            prompt_template_id=template.id,
            prompt_version=template.version,
            request_payload={**request_payload, "messages": "[redacted]"},
            status="streaming",
        )
        db.add(call_log)
        await db.commit()
        await db.refresh(call_log)

        client = OpenAICompatibleClient(
            provider.base_url,
            decrypt_text(provider.api_key_encrypted),
            provider.timeout_seconds,
        )
        sequence = 0
        raw_parts: list[str] = []
        started_at = time.perf_counter()
        first_token_ms: int | None = None
        done = False
        try:
            async for line in client.stream_chat(request_payload):
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                yield f"data: {data}\n\n"
                if data == "[DONE]":
                    done = True
                    db.add(
                        LLMStreamChunk(
                            call_log_id=call_log.id,
                            sequence=sequence,
                            chunk_json={"data": "[DONE]"},
                            is_done=True,
                        )
                    )
                    continue
                sequence += 1
                chunk = json.loads(data)
                choices = chunk.get("choices") or []
                delta = ""
                finish_reason = None
                if choices:
                    delta = choices[0].get("delta", {}).get("content") or ""
                    finish_reason = choices[0].get("finish_reason")
                if delta and first_token_ms is None:
                    first_token_ms = int((time.perf_counter() - started_at) * 1000)
                raw_parts.append(delta)
                usage = chunk.get("usage") or {}
                if usage:
                    call_log.input_tokens = usage.get("prompt_tokens")
                    call_log.output_tokens = usage.get("completion_tokens")
                db.add(
                    LLMStreamChunk(
                        call_log_id=call_log.id,
                        sequence=sequence,
                        chunk_json=chunk,
                        delta_content=delta,
                        finish_reason=finish_reason,
                    )
                )
                await db.flush()
            call_log.stream_completed = done
            call_log.raw_output = "".join(raw_parts)
            call_log.first_token_ms = first_token_ms
            call_log.duration_ms = int((time.perf_counter() - started_at) * 1000)
            if not done:
                call_log.status = "interrupted"
                call_log.error_message = "上游 SSE 未返回 [DONE]"
            else:
                await self._parse_and_update(call_log, template.output_schema)
            await db.commit()
        except Exception as exc:
            call_log.status = "failed"
            call_log.error_message = str(exc)
            call_log.duration_ms = int((time.perf_counter() - started_at) * 1000)
            await db.commit()
            raise

    async def _parse_and_update(self, call_log: LLMCallLog, output_schema: dict) -> None:
        if not call_log.raw_output.strip():
            call_log.status = "success"
            return
        try:
            parsed = self.parser.parse_json(call_log.raw_output)
            is_valid, error = self.parser.validate(parsed, output_schema)
            call_log.parsed_output = parsed
            call_log.status = "success" if is_valid else "failed"
            call_log.error_message = error
        except Exception as exc:
            call_log.status = "failed"
            call_log.error_message = f"JSON 解析失败: {exc}"
