from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.repositories.records import RecordsRepository
from app.schemas.records import (
    AdminRecordListItem,
    PaginationResponse,
    PlanningRecordListItem,
    RecordInputSnapshot,
    RecordOutputSnapshot,
    RecordSummary,
    RegenerateRecordRequest,
    RegenerateRecordResponse,
)


class RecordsService:
    def __init__(self, repo: RecordsRepository | None = None) -> None:
        self.repo = repo or RecordsRepository()

    async def list_planning_records(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        page: int,
        page_size: int,
        status: str | None = None,
        keyword: str | None = None,
    ) -> dict[str, Any]:
        page, page_size = self._normalize_pagination(page, page_size)
        total, records = await self.repo.list_user_records(
            db,
            user_id=user_id,
            page=page,
            page_size=page_size,
            status=self._blank_to_none(status),
            keyword=self._blank_to_none(keyword),
        )
        items = [self._planning_list_item(record) for record in records]
        return self._page(total=total, page=page, page_size=page_size, items=items)

    async def get_planning_record_detail(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        record_id: int,
    ) -> dict[str, Any]:
        record = await self.repo.get_record(db, record_id=record_id, user_id=user_id)
        if record is None:
            raise AppException("记录不存在", code=404)
        components = await self.repo.get_record_detail_components(db, record_id=record.id)
        return self._detail(record, components)

    async def get_planning_route_map(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        record_id: int,
    ) -> dict[str, Any]:
        record = await self.repo.get_record(db, record_id=record_id, user_id=user_id)
        if record is None:
            raise AppException("记录不存在", code=404, status_code=404)

        components = await self.repo.get_record_detail_components(db, record_id=record.id)
        map_exports = components["map_exports"]
        output = components["output"]
        default_export = map_exports[0] if map_exports else None
        return self._json_safe(
            {
                "record_id": record.id,
                "amap_route_url": getattr(default_export, "amap_route_url", None)
                or getattr(output, "amap_route_url", None),
                "image_url": getattr(default_export, "image_url", None),
                "export_type": getattr(default_export, "export_type", None),
                "status": getattr(default_export, "status", None),
                "width": getattr(default_export, "width", None),
                "height": getattr(default_export, "height", None),
            }
        )

    async def regenerate_record(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        record_id: int,
        payload: RegenerateRecordRequest,
    ) -> dict[str, Any]:
        parent_record = await self.repo.get_record(db, record_id=record_id, user_id=user_id)
        if parent_record is None:
            raise AppException("记录不存在", code=404)

        parent_input = await self.repo.get_record_input(db, record_id=record_id)
        input_payload, raw_input = self._build_regeneration_payload(
            parent_record,
            parent_input,
            payload.override_input,
        )
        try:
            new_record = await self.repo.create_regeneration_record(
                db,
                parent_record=parent_record,
                record_no=self._new_record_no(),
                input_payload=input_payload,
                raw_input=raw_input,
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise

        return RegenerateRecordResponse(
            record_id=new_record.id,
            parent_record_id=parent_record.id,
            status=new_record.status,
            stream_url="/api/v1/planning/generate_stream",
            request_payload=self._stream_request_payload(input_payload),
        ).model_dump(mode="json")

    async def list_admin_generation_records(
        self,
        db: AsyncSession,
        *,
        page: int,
        page_size: int,
        status: str | None = None,
        transport_mode: str | None = None,
        user_keyword: str | None = None,
    ) -> dict[str, Any]:
        page, page_size = self._normalize_pagination(page, page_size)
        total, rows = await self.repo.list_admin_records(
            db,
            page=page,
            page_size=page_size,
            status=self._blank_to_none(status),
            transport_mode=self._blank_to_none(transport_mode),
            user_keyword=self._blank_to_none(user_keyword),
        )
        items = [
            self._admin_list_item(record, username=username, nickname=nickname)
            for record, username, nickname in rows
        ]
        return self._page(total=total, page=page, page_size=page_size, items=items)

    async def get_admin_generation_record_detail(
        self,
        db: AsyncSession,
        *,
        record_id: int,
    ) -> dict[str, Any]:
        record = await self.repo.get_record(db, record_id=record_id)
        if record is None:
            raise AppException("记录不存在", code=404)
        components = await self.repo.get_record_detail_components(
            db,
            record_id=record.id,
            include_llm_logs=True,
        )
        return self._detail(record, components, include_llm_logs=True)

    async def retry_admin_generation_record(
        self,
        db: AsyncSession,
        *,
        record_id: int,
    ) -> dict[str, Any]:
        parent_record = await self.repo.get_record(db, record_id=record_id)
        if parent_record is None:
            raise AppException("记录不存在", code=404, status_code=404)
        if parent_record.status != "failed":
            raise AppException("只有失败记录可以重试", code=409, status_code=409)

        parent_input = await self.repo.get_record_input(db, record_id=record_id)
        input_payload, raw_input = self._build_regeneration_payload(
            parent_record,
            parent_input,
            None,
        )
        try:
            new_record = await self.repo.create_regeneration_record(
                db,
                parent_record=parent_record,
                record_no=self._new_record_no(),
                input_payload=input_payload,
                raw_input=raw_input,
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise

        return RegenerateRecordResponse(
            record_id=new_record.id,
            parent_record_id=parent_record.id,
            status=new_record.status,
            stream_url="/api/v1/planning/generate_stream",
            request_payload=self._stream_request_payload(input_payload),
        ).model_dump(mode="json")

    async def delete_admin_generation_record(
        self,
        db: AsyncSession,
        *,
        record_id: int,
    ) -> None:
        record = await self.repo.get_record(db, record_id=record_id)
        if record is None:
            raise AppException("记录不存在", code=404, status_code=404)
        await self.repo.soft_delete_record(db, record=record)
        await db.commit()

    def _page(
        self,
        *,
        total: int,
        page: int,
        page_size: int,
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return PaginationResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=items,
        ).model_dump(mode="json")

    def _detail(
        self,
        record: Any,
        components: dict[str, Any],
        *,
        include_llm_logs: bool = False,
    ) -> dict[str, Any]:
        data = {
            "record": self._record_summary(record),
            "input": self._input_snapshot(record, components.get("input")),
            "output": self._output_snapshot(components.get("output")),
            "snapshots": {
                "routes": [self._route_snapshot(item) for item in components["route_snapshots"]],
                "map_exports": [self._map_export(item) for item in components["map_exports"]],
                "weather": [
                    self._weather_snapshot(item) for item in components["weather_snapshots"]
                ],
                "realtime_info": self._realtime_info(components["news_snapshots"]),
            },
            "errors": [self._error_item(item) for item in components["errors"]],
        }
        if include_llm_logs:
            data["llm_call_logs"] = [
                self._llm_call_log(item) for item in components.get("llm_call_logs", [])
            ]
        return self._json_safe(data)

    def _planning_list_item(self, record: Any) -> dict[str, Any]:
        return PlanningRecordListItem(
            id=record.id,
            record_no=record.record_no,
            origin_text=record.origin_text,
            destination_text=record.destination_text,
            range_text=record.range_text,
            transport_mode=record.transport_mode,
            status=record.status,
            summary_title=record.summary_title,
            summary_text=record.summary_text,
            created_at=record.created_at,
            completed_at=record.completed_at,
        ).model_dump(mode="json")

    def _admin_list_item(
        self,
        record: Any,
        *,
        username: str | None,
        nickname: str | None,
    ) -> dict[str, Any]:
        return AdminRecordListItem(
            id=record.id,
            record_no=record.record_no,
            user_id=record.user_id,
            user_nickname=nickname or username,
            origin_text=record.origin_text,
            destination_text=record.destination_text,
            transport_mode=record.transport_mode,
            status=record.status,
            duration_ms=record.duration_ms,
            error_message=record.error_message,
            created_at=record.created_at,
        ).model_dump(mode="json")

    def _record_summary(self, record: Any) -> dict[str, Any]:
        return RecordSummary(
            id=record.id,
            record_no=record.record_no,
            status=record.status,
            current_stage=record.current_stage,
            origin_text=record.origin_text,
            destination_text=record.destination_text,
            transport_mode=record.transport_mode,
            duration_ms=record.duration_ms,
            created_at=record.created_at,
        ).model_dump(mode="json")

    def _input_snapshot(self, record: Any, input_snapshot: Any | None) -> dict[str, Any]:
        source = input_snapshot or record
        return RecordInputSnapshot(
            origin_text=getattr(source, "origin_text", None),
            destination_text=getattr(source, "destination_text", None),
            range_text=getattr(source, "range_text", None),
            travel_date=getattr(source, "travel_date", None),
            people_count=getattr(source, "people_count", None),
            preferences=getattr(source, "preferences", None) or [],
            avoidances=getattr(source, "avoidances", None) or [],
        ).model_dump(mode="json")

    def _output_snapshot(self, output: Any | None) -> dict[str, Any]:
        if output is None:
            return RecordOutputSnapshot().model_dump(mode="json")
        return RecordOutputSnapshot(
            final_markdown=output.final_markdown,
            result_json=output.result_json or {},
            weather_summary=output.weather_summary,
            route_summary=output.route_summary,
            attractions_summary=output.attractions_summary,
            realtime_info_summary=output.realtime_info_summary,
            risk_summary=output.risk_summary,
            amap_route_url=output.amap_route_url,
        ).model_dump(mode="json")

    def _route_snapshot(self, item: Any) -> dict[str, Any]:
        return {
            "id": item.id,
            "provider": item.provider,
            "route_type": item.route_type,
            "origin_location": item.origin_location,
            "destination_location": item.destination_location,
            "waypoints": item.waypoints or [],
            "distance_m": item.distance_m,
            "duration_s": item.duration_s,
            "request_params": item.request_params or {},
            "response_data": item.response_data or {},
            "source_updated_at": item.source_updated_at,
            "created_at": item.created_at,
        }

    def _map_export(self, item: Any) -> dict[str, Any]:
        return {
            "id": item.id,
            "route_snapshot_id": item.route_snapshot_id,
            "export_type": item.export_type,
            "status": item.status,
            "amap_route_url": item.amap_route_url,
            "image_url": item.image_url,
            "width": item.width,
            "height": item.height,
            "error_message": item.error_message,
            "created_at": item.created_at,
        }

    def _weather_snapshot(self, item: Any) -> dict[str, Any]:
        return {
            "id": item.id,
            "provider": item.provider,
            "city_name": item.city_name,
            "location": item.location,
            "weather_date": item.weather_date,
            "weather_summary": item.weather_summary,
            "alert_level": item.alert_level,
            "alerts": item.alerts or [],
            "request_params": item.request_params or {},
            "response_data": item.response_data or {},
            "source_updated_at": item.source_updated_at,
            "created_at": item.created_at,
        }

    def _realtime_info(self, items: list[Any]) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = {
            "news_traffic": [],
            "guide_pitfall": [],
        }
        for item in items:
            snapshot = {
                "id": item.id,
                "provider": item.provider,
                "query_text": item.query_text,
                "category": item.category,
                "item_count": item.item_count,
                "top_titles": item.top_titles or [],
                "source_sites": item.source_sites or [],
                "credibility_score": item.credibility_score,
                "response_data": item.response_data or {},
                "source_updated_at": item.source_updated_at,
                "created_at": item.created_at,
            }
            if item.category in {"guide", "pitfall"}:
                grouped["guide_pitfall"].append(snapshot)
            else:
                grouped["news_traffic"].append(snapshot)
        return grouped

    def _error_item(self, item: Any) -> dict[str, Any]:
        return {
            "id": item.id,
            "stage": item.stage,
            "error_source": item.error_source,
            "error_code": item.error_code,
            "error_message": item.error_message,
            "error_detail": item.error_detail or {},
            "retryable": item.retryable,
            "handled_by": item.handled_by,
            "handled_at": item.handled_at,
            "created_at": item.created_at,
        }

    def _llm_call_log(self, item: Any) -> dict[str, Any]:
        return {
            "id": item.id,
            "provider": item.provider,
            "model_name": item.model_name,
            "call_type": item.call_type,
            "status": item.status,
            "prompt_tokens": item.prompt_tokens,
            "completion_tokens": item.completion_tokens,
            "total_tokens": item.total_tokens,
            "duration_ms": item.duration_ms,
            "created_at": item.created_at,
        }

    def _build_regeneration_payload(
        self,
        parent_record: Any,
        parent_input: Any | None,
        override_input: dict[str, Any] | None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        override_input = override_input or {}
        raw_input = deepcopy(getattr(parent_input, "raw_input", None) or {})

        input_payload = {
            "origin_text": self._override_value(
                override_input,
                ["origin", "origin_text"],
                getattr(parent_input, "origin_text", None) or parent_record.origin_text,
            ),
            "destination_text": self._override_value(
                override_input,
                ["destination", "destination_text"],
                getattr(parent_input, "destination_text", None) or parent_record.destination_text,
            ),
            "range_text": self._override_value(
                override_input,
                ["range", "range_text"],
                getattr(parent_input, "range_text", None) or parent_record.range_text,
            ),
            "transport_mode": self._override_value(
                override_input,
                ["transport_mode"],
                getattr(parent_input, "transport_mode", None) or parent_record.transport_mode,
            ),
            "travel_date": self._coerce_date(
                self._override_value(
                    override_input,
                    ["travel_date"],
                    getattr(parent_input, "travel_date", None),
                )
            ),
            "date_text": self._override_value(
                override_input,
                ["date_text"],
                getattr(parent_input, "date_text", None),
            ),
            "people_count": self._override_value(
                override_input,
                ["people_count"],
                getattr(parent_input, "people_count", None),
            ),
            "preferences": self._override_value(
                override_input,
                ["preferences"],
                getattr(parent_input, "preferences", None) or [],
            ),
            "avoidances": self._override_value(
                override_input,
                ["avoidances"],
                getattr(parent_input, "avoidances", None) or [],
            ),
        }
        raw_input.update(override_input)
        raw_input.update(
            {
                "origin": input_payload["origin_text"],
                "destination": input_payload["destination_text"],
                "range": input_payload["range_text"],
                "transport_mode": input_payload["transport_mode"],
                "travel_date": input_payload["travel_date"],
                "people_count": input_payload["people_count"],
                "preferences": input_payload["preferences"],
                "avoidances": input_payload["avoidances"],
            }
        )
        return input_payload, self._json_safe(raw_input)

    def _normalize_pagination(self, page: int, page_size: int) -> tuple[int, int]:
        return max(page, 1), min(max(page_size, 1), 100)

    def _blank_to_none(self, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    def _override_value(
        self,
        override_input: dict[str, Any],
        keys: list[str],
        default: Any,
    ) -> Any:
        for key in keys:
            if key in override_input:
                return override_input[key]
        return default

    def _coerce_date(self, value: Any) -> date | None:
        if isinstance(value, datetime):
            return value.date()
        if value is None or isinstance(value, date):
            return value
        if isinstance(value, str) and value:
            return date.fromisoformat(value)
        return None

    def _new_record_no(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        return f"PL{timestamp}{uuid4().hex[:6]}"

    def _stream_request_payload(self, input_payload: dict[str, Any]) -> dict[str, Any]:
        return self._json_safe(
            {
                "origin": input_payload["origin_text"],
                "destination": input_payload["destination_text"],
                "range": input_payload["range_text"],
                "transport_mode": input_payload["transport_mode"],
                "travel_date": input_payload.get("travel_date"),
                "people_count": input_payload.get("people_count"),
                "preferences": input_payload.get("preferences") or [],
                "avoidances": input_payload.get("avoidances") or [],
            }
        )

    def _json_safe(self, value: Any) -> Any:
        if isinstance(value, datetime | date):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, dict):
            return {key: self._json_safe(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._json_safe(item) for item in value]
        return value
