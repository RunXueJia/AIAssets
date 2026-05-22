import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from itertools import count
from typing import Any, Protocol
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.integrations.llm import (
    GenerationLlmClientProtocol,
    LlmClientError,
    create_llm_client_from_settings,
)
from app.models.generation import GenerationRecord
from app.repositories.records import RecordsRepository
from app.schemas.generation import GenerateStreamRequest, GenerationStage, GenerationStreamEvent
from app.services.ai_planning import AiPlanningService
from app.services.llm_configs import LlmConfigsService

STAGE_NAMES: dict[GenerationStage, str] = {
    "understanding": "需求理解",
    "weather": "天气预警",
    "route": "路线规划",
    "transport": "公共交通/路径规划",
    "map_export": "高德路线链接和路径图",
    "attractions": "途径景点",
    "realtime": "实时信息检索",
    "summary": "汇总",
}
APP_TZ = timezone(timedelta(hours=8))


class RecordStoreProtocol(Protocol):
    snapshots: dict[str, dict[str, Any]]

    async def create_record(self, request: GenerateStreamRequest) -> Any: ...

    async def use_existing_record(self, record_id: int, request: GenerateStreamRequest) -> Any: ...

    async def append_event(self, event: GenerationStreamEvent) -> None: ...

    async def save_snapshot(self, snapshot_type: str, data: dict[str, Any]) -> None: ...

    async def save_output(self, output_payload: dict[str, Any]) -> None: ...

    async def mark_streaming(self, record_id: int, stage: GenerationStage) -> None: ...

    async def mark_completed(
        self,
        record_id: int,
        duration_ms: int,
        *,
        summary_title: str | None,
        summary_text: str | None,
    ) -> str: ...

    async def mark_failed(
        self,
        record_id: int,
        *,
        stage: str | None,
        error_code: str,
        error_message: str,
        error_detail: dict[str, Any] | None = None,
    ) -> None: ...

    async def cancel_record(self, record_id: int) -> bool: ...

    async def is_canceled(self, record_id: int) -> bool: ...


@dataclass
class MockGenerationRecord:
    id: int
    record_no: str
    status: str
    request: GenerateStreamRequest
    current_stage: GenerationStage | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(APP_TZ))
    duration_ms: int | None = None


class InMemoryGenerationRecordStore:
    """In-memory adapter used by narrow service and router tests."""

    def __init__(self) -> None:
        self._ids = count(101)
        self._records: dict[int, MockGenerationRecord] = {}
        self._lock = asyncio.Lock()
        self.snapshots: dict[str, dict[str, Any]] = {}
        self.events: list[GenerationStreamEvent] = []
        self.output_payload: dict[str, Any] | None = None

    async def create_record(self, request: GenerateStreamRequest) -> MockGenerationRecord:
        async with self._lock:
            record_id = next(self._ids)
            record = MockGenerationRecord(
                id=record_id,
                record_no=f"PL{datetime.now(APP_TZ):%Y%m%d}{record_id:04d}",
                status="pending",
                request=request,
            )
            self._records[record_id] = record
            return record

    async def use_existing_record(
        self,
        record_id: int,
        request: GenerateStreamRequest,
    ) -> MockGenerationRecord:
        async with self._lock:
            record = self._records.get(record_id)
            if record is None:
                record = MockGenerationRecord(
                    id=record_id,
                    record_no=f"PL{datetime.now(APP_TZ):%Y%m%d}{record_id:04d}",
                    status="pending",
                    request=request,
                )
                self._records[record_id] = record
            return record

    async def append_event(self, event: GenerationStreamEvent) -> None:
        self.events.append(event)

    async def save_snapshot(self, snapshot_type: str, data: dict[str, Any]) -> None:
        self.snapshots[snapshot_type] = data

    async def save_output(self, output_payload: dict[str, Any]) -> None:
        self.output_payload = output_payload

    async def mark_streaming(self, record_id: int, stage: GenerationStage) -> None:
        async with self._lock:
            if record := self._records.get(record_id):
                if record.status != "canceled":
                    record.status = "streaming"
                    record.current_stage = stage

    async def mark_completed(
        self,
        record_id: int,
        duration_ms: int,
        *,
        summary_title: str | None,
        summary_text: str | None,
    ) -> str:
        async with self._lock:
            if record := self._records.get(record_id):
                if record.status != "canceled":
                    record.status = "completed"
                    record.duration_ms = duration_ms
                return record.status
        return "not_found"

    async def mark_failed(
        self,
        record_id: int,
        *,
        stage: str | None,
        error_code: str,
        error_message: str,
        error_detail: dict[str, Any] | None = None,
    ) -> None:
        async with self._lock:
            if record := self._records.get(record_id):
                record.status = "failed"
                record.current_stage = stage  # type: ignore[assignment]

    async def cancel_record(self, record_id: int) -> bool:
        async with self._lock:
            record = self._records.get(record_id)
            if record is None:
                record = MockGenerationRecord(
                    id=record_id,
                    record_no=f"PL{datetime.now(APP_TZ):%Y%m%d}{record_id:04d}",
                    status="pending",
                    request=GenerateStreamRequest(
                        origin="mock",
                        destination="mock",
                        range="mock",
                    ),
                )
                self._records[record_id] = record
            record.status = "canceled"
            return True

    async def is_canceled(self, record_id: int) -> bool:
        async with self._lock:
            return self._records.get(record_id, None) is not None and (
                self._records[record_id].status == "canceled"
            )


class DatabaseGenerationRecordStore:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        user_id: int,
        source_client: str = "web",
        repo: RecordsRepository | None = None,
    ) -> None:
        self.session_factory = session_factory
        self.user_id = user_id
        self.source_client = source_client
        self.repo = repo or RecordsRepository()
        self.record: GenerationRecord | None = None
        self.input_payload: dict[str, Any] = {}
        self.raw_input: dict[str, Any] = {}
        self.sequence_no = 0
        self.snapshots: dict[str, dict[str, Any]] = {}
        self.snapshot_ids: dict[str, int] = {}
        self.llm_service = LlmConfigsService()

    async def create_record(self, request: GenerateStreamRequest) -> GenerationRecord:
        self.input_payload = self._input_payload(request)
        self.raw_input = request.model_dump(mode="json")
        async with self.session_factory() as db:
            record = await self.repo.create_generation_record(
                db,
                record_no=self._new_record_no(),
                user_id=self.user_id,
                source_client=self.source_client,
                input_payload=self.input_payload,
                raw_input=self.raw_input,
            )
            await db.commit()
            self.record = record
            return record

    async def use_existing_record(
        self,
        record_id: int,
        request: GenerateStreamRequest,
    ) -> GenerationRecord:
        self.input_payload = self._input_payload(request)
        self.raw_input = request.model_dump(mode="json")
        async with self.session_factory() as db:
            record = await self.repo.get_record(db, record_id=record_id, user_id=self.user_id)
            if record is None:
                raise ValueError("记录不存在")
            self.record = record
            max_sequence_no = await self.repo.max_stream_sequence(db, record_id=record.id)
            self.sequence_no = max_sequence_no
            return record

    async def append_event(self, event: GenerationStreamEvent) -> None:
        if self.record is None:
            return
        self.sequence_no += 1
        async with self.session_factory() as db:
            await self.repo.append_stream_event(
                db,
                record_id=self.record.id,
                sequence_no=self.sequence_no,
                event_type=event.event,
                stage=event.data.get("stage"),
                content=event.data.get("content"),
                payload=event.data,
            )
            await db.commit()

    async def save_snapshot(self, snapshot_type: str, data: dict[str, Any]) -> None:
        if self.record is None:
            return
        if snapshot_type == "map_export" and "route_snapshot_id" not in data:
            data = {**data, "route_snapshot_id": self.snapshot_ids.get("route")}
        self.snapshots[snapshot_type] = data
        async with self.session_factory() as db:
            snapshot_id = await self.repo.save_generation_snapshot(
                db,
                record_id=self.record.id,
                snapshot_type=snapshot_type,
                data=data,
                input_payload=self.input_payload,
            )
            await db.commit()
            if snapshot_id is not None:
                self.snapshot_ids[snapshot_type] = snapshot_id

    async def save_output(self, output_payload: dict[str, Any]) -> None:
        if self.record is None:
            return
        async with self.session_factory() as db:
            await self.repo.save_generation_output(
                db,
                record_id=self.record.id,
                output_payload=output_payload,
            )
            await db.commit()

    async def mark_streaming(self, record_id: int, stage: GenerationStage) -> None:
        async with self.session_factory() as db:
            await self.repo.mark_record_streaming(db, record_id=record_id, stage=stage)
            await db.commit()

    async def mark_completed(
        self,
        record_id: int,
        duration_ms: int,
        *,
        summary_title: str | None,
        summary_text: str | None,
    ) -> str:
        async with self.session_factory() as db:
            record = await self.repo.mark_record_completed(
                db,
                record_id=record_id,
                duration_ms=duration_ms,
                summary_title=summary_title,
                summary_text=summary_text,
            )
            await db.commit()
            return record.status if record is not None else "not_found"

    async def mark_failed(
        self,
        record_id: int,
        *,
        stage: str | None,
        error_code: str,
        error_message: str,
        error_detail: dict[str, Any] | None = None,
    ) -> None:
        async with self.session_factory() as db:
            await self.repo.mark_record_failed(
                db,
                record_id=record_id,
                stage=stage,
                error_code=error_code,
                error_message=error_message,
                error_detail=error_detail,
            )
            await db.commit()

    async def cancel_record(self, record_id: int) -> bool:
        async with self.session_factory() as db:
            record = await self.repo.mark_record_canceled(
                db,
                record_id=record_id,
                user_id=self.user_id,
            )
            await db.commit()
            return record is not None

    async def is_canceled(self, record_id: int) -> bool:
        async with self.session_factory() as db:
            record = await self.repo.get_record(db, record_id=record_id, user_id=self.user_id)
            return record is not None and record.status == "canceled"

    async def get_llm_client(self) -> GenerationLlmClientProtocol:
        async with self.session_factory() as db:
            return await self.llm_service.get_generation_client(db)

    def _input_payload(self, request: GenerateStreamRequest) -> dict[str, Any]:
        return {
            "origin_text": request.origin,
            "destination_text": request.destination,
            "range_text": request.range,
            "transport_mode": request.transport_mode,
            "travel_date": request.travel_date,
            "date_text": request.travel_date.isoformat() if request.travel_date else None,
            "people_count": request.people_count,
            "preferences": request.preferences,
            "avoidances": request.avoidances,
        }

    def _new_record_no(self) -> str:
        return f"PL{datetime.now(APP_TZ):%Y%m%d%H%M%S%f}{uuid4().hex[:6]}"


class GenerationService:
    def __init__(
        self,
        record_store: RecordStoreProtocol | None = None,
        llm_client: GenerationLlmClientProtocol | None = None,
        planning_service: AiPlanningService | None = None,
        token_delay_s: float = 0.01,
    ) -> None:
        self.record_store = record_store or InMemoryGenerationRecordStore()
        self.llm_client = llm_client
        self.planning_service = planning_service or AiPlanningService()
        self.token_delay_s = token_delay_s

    async def stream_generation(
        self,
        request: GenerateStreamRequest,
        *,
        existing_record_id: int | None = None,
    ) -> AsyncIterator[GenerationStreamEvent]:
        started_at = datetime.now(APP_TZ)
        if existing_record_id is None:
            record = await self.record_store.create_record(request)
        else:
            record = await self.record_store.use_existing_record(existing_record_id, request)
        current_stage: str | None = None

        if existing_record_id is None:
            record_created = GenerationStreamEvent(
                event="record_created",
                data={
                    "record_id": record.id,
                    "record_no": record.record_no,
                    "status": "pending",
                },
            )
            await self.record_store.append_event(record_created)
            yield record_created

        try:
            llm_client = await self._get_llm_client()
            planning_result = await self.planning_service.build_result(record.id, request)
            for stage in STAGE_NAMES:
                current_stage = stage
                if await self.record_store.is_canceled(record.id):
                    done_event = self._done_event(record.id, started_at, status="canceled")
                    await self.record_store.append_event(done_event)
                    yield done_event
                    return

                await self.record_store.mark_streaming(record.id, stage)
                stage_event = GenerationStreamEvent(
                    event="stage",
                    data={
                        "record_id": record.id,
                        "stage": stage,
                        "stage_name": STAGE_NAMES[stage],
                        "status": "streaming",
                    },
                )
                await self.record_store.append_event(stage_event)
                yield stage_event

                try:
                    async for token in llm_client.stream_stage_tokens(request, stage):
                        if await self.record_store.is_canceled(record.id):
                            done_event = self._done_event(
                                record.id,
                                started_at,
                                status="canceled",
                            )
                            await self.record_store.append_event(done_event)
                            yield done_event
                            return

                        token_event = GenerationStreamEvent(
                            event="token",
                            data={
                                "record_id": record.id,
                                "stage": stage,
                                "content": token,
                            },
                        )
                        await self.record_store.append_event(token_event)
                        yield token_event
                        if self.token_delay_s:
                            await asyncio.sleep(self.token_delay_s)
                except LlmClientError as exc:
                    async for event in self._llm_stage_fallback_events(
                        record_id=record.id,
                        stage=stage,
                        error=exc,
                    ):
                        await self.record_store.append_event(event)
                        yield event

                snapshot = self._snapshot_for_stage(record.id, stage, planning_result)
                if snapshot is not None:
                    snapshot_type = str(snapshot.data["type"])
                    await self.record_store.save_snapshot(snapshot_type, snapshot.data["data"])
                    await self.record_store.append_event(snapshot)
                    yield snapshot

            output_payload = self.planning_service.output_payload(planning_result)
            if await self.record_store.is_canceled(record.id):
                done_event = self._done_event(record.id, started_at, status="canceled")
                await self.record_store.append_event(done_event)
                yield done_event
                return

            await self.record_store.save_output(output_payload)

            duration_ms = self._duration_ms_since(started_at)
            final_status = await self.record_store.mark_completed(
                record.id,
                duration_ms,
                summary_title=planning_result.summary_title,
                summary_text=planning_result.summary_text,
            )
            done_event = self._done_event(
                record.id,
                started_at,
                status="canceled" if final_status == "canceled" else "completed",
            )
            await self.record_store.append_event(done_event)
            yield done_event
        except Exception as exc:
            error_message = "生成过程中发生异常，已保存失败状态。"
            await self.record_store.mark_failed(
                record.id,
                stage=current_stage,
                error_code="GENERATION_FAILED",
                error_message=error_message,
                error_detail={
                    "exception": exc.__class__.__name__,
                    "message": str(exc),
                },
            )
            error_event = GenerationStreamEvent(
                event="error",
                data={
                    "record_id": record.id,
                    "stage": current_stage,
                    "error_code": "GENERATION_FAILED",
                    "message": error_message,
                },
            )
            await self.record_store.append_event(error_event)
            yield error_event
            done_event = self._done_event(record.id, started_at, status="failed")
            await self.record_store.append_event(done_event)
            yield done_event

    async def cancel_generation(self, record_id: int) -> dict[str, Any]:
        canceled = await self.record_store.cancel_record(record_id)
        return {
            "record_id": record_id,
            "status": "canceled" if canceled else "not_found",
        }

    def format_sse(self, event: GenerationStreamEvent) -> str:
        payload = json.dumps(event.data, ensure_ascii=False, separators=(",", ":"))
        return f"event: {event.event}\ndata: {payload}\n\n"

    def _snapshot_for_stage(
        self,
        record_id: int,
        stage: GenerationStage,
        planning_result: Any,
    ) -> GenerationStreamEvent | None:
        snapshot = self.planning_service.snapshot_for_stage(planning_result, stage)
        if snapshot is None:
            return None

        snapshot_type, data = snapshot
        return GenerationStreamEvent(
            event="snapshot",
            data={"record_id": record_id, "type": snapshot_type, "data": data},
        )

    def _done_event(
        self,
        record_id: int,
        started_at: datetime,
        status: str,
    ) -> GenerationStreamEvent:
        return GenerationStreamEvent(
            event="done",
            data={
                "record_id": record_id,
                "status": status,
                "duration_ms": self._duration_ms_since(started_at),
            },
        )

    def _duration_ms_since(self, started_at: datetime) -> int:
        return max(0, int((datetime.now(APP_TZ) - started_at).total_seconds() * 1000))

    async def _llm_stage_fallback_events(
        self,
        *,
        record_id: int,
        stage: GenerationStage,
        error: LlmClientError,
    ) -> AsyncIterator[GenerationStreamEvent]:
        yield GenerationStreamEvent(
            event="error",
            data={
                "record_id": record_id,
                "stage": stage,
                "error_code": "LLM_STAGE_FAILED",
                "message": "当前阶段大模型流式输出中断，已使用系统规划结果继续生成。",
                "detail": str(error),
            },
        )
        yield GenerationStreamEvent(
            event="token",
            data={
                "record_id": record_id,
                "stage": stage,
                "content": self._stage_fallback_text(stage),
            },
        )

    def _stage_fallback_text(self, stage: GenerationStage) -> str:
        return {
            "understanding": "已根据输入需求继续生成规划。",
            "weather": "天气信息已写入结果模块，请以天气快照为准。",
            "route": "路线信息已写入结果模块，请以路线快照为准。",
            "transport": "交通建议已由系统规划结果补充，请继续查看后续路线链接和总结。",
            "map_export": "地图链接已由系统导出，请使用下方高德路线入口。",
            "attractions": "途径景点已由系统检索结果补充。",
            "realtime": "实时信息已由检索结果补充，出行前请再次复核。",
            "summary": "最终摘要已由系统规划结果生成。",
        }[stage]

    def _iso_now(self) -> str:
        return datetime.now(APP_TZ).isoformat()

    async def _get_llm_client(self) -> GenerationLlmClientProtocol:
        if self.llm_client is not None:
            return self.llm_client
        store_getter = getattr(self.record_store, "get_llm_client", None)
        if callable(store_getter):
            return await store_getter()
        return create_llm_client_from_settings()


generation_service = GenerationService()
