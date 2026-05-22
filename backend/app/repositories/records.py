from datetime import datetime
from typing import Any

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import utc_now
from app.models import (
    GenerationError,
    GenerationInput,
    GenerationOutput,
    GenerationRecord,
    LlmCallLog,
    NewsSnapshot,
    RouteMapExport,
    RouteSnapshot,
    User,
    WeatherSnapshot,
)
from app.models import (
    GenerationStreamEvent as GenerationStreamEventModel,
)


class RecordsRepository:
    async def create_generation_record(
        self,
        db: AsyncSession,
        *,
        record_no: str,
        user_id: int,
        source_client: str,
        input_payload: dict[str, Any],
        raw_input: dict[str, Any],
    ) -> GenerationRecord:
        record = GenerationRecord(
            record_no=record_no,
            user_id=user_id,
            source_client=source_client,
            origin_text=input_payload["origin_text"],
            destination_text=input_payload["destination_text"],
            range_text=input_payload["range_text"],
            transport_mode=input_payload["transport_mode"],
            status="pending",
        )
        db.add(record)
        await db.flush()

        db.add(
            GenerationInput(
                record_id=record.id,
                origin_text=input_payload["origin_text"],
                destination_text=input_payload["destination_text"],
                range_text=input_payload["range_text"],
                transport_mode=input_payload["transport_mode"],
                travel_date=input_payload.get("travel_date"),
                date_text=input_payload.get("date_text"),
                people_count=input_payload.get("people_count"),
                preferences=input_payload.get("preferences") or [],
                avoidances=input_payload.get("avoidances") or [],
                raw_input=raw_input,
            )
        )
        await db.flush()
        return record

    async def append_stream_event(
        self,
        db: AsyncSession,
        *,
        record_id: int,
        sequence_no: int,
        event_type: str,
        stage: str | None,
        content: str | None,
        payload: dict[str, Any] | None,
    ) -> None:
        db.add(
            GenerationStreamEventModel(
                record_id=record_id,
                sequence_no=sequence_no,
                event_type=event_type,
                stage=stage,
                content=content,
                payload=payload,
            )
        )
        await db.flush()

    async def list_stream_events_after(
        self,
        db: AsyncSession,
        *,
        record_id: int,
        after_sequence: int = 0,
        limit: int = 100,
    ) -> list[GenerationStreamEventModel]:
        stmt = (
            select(GenerationStreamEventModel)
            .where(
                GenerationStreamEventModel.record_id == record_id,
                GenerationStreamEventModel.sequence_no > after_sequence,
            )
            .order_by(GenerationStreamEventModel.sequence_no.asc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def max_stream_sequence(self, db: AsyncSession, *, record_id: int) -> int:
        result = await db.execute(
            select(func.max(GenerationStreamEventModel.sequence_no)).where(
                GenerationStreamEventModel.record_id == record_id
            )
        )
        return int(result.scalar() or 0)

    async def mark_record_streaming(
        self,
        db: AsyncSession,
        *,
        record_id: int,
        stage: str,
        user_id: int | None = None,
    ) -> GenerationRecord | None:
        record = await self.get_record(db, record_id=record_id, user_id=user_id)
        if record is None:
            return None
        if record.status != "canceled":
            record.status = "streaming"
            record.current_stage = stage
            if record.started_at is None:
                record.started_at = utc_now()
        await db.flush()
        return record

    async def mark_record_canceled(
        self,
        db: AsyncSession,
        *,
        record_id: int,
        user_id: int | None = None,
    ) -> GenerationRecord | None:
        record = await self.get_record(db, record_id=record_id, user_id=user_id)
        if record is None:
            return None
        record.status = "canceled"
        record.canceled_at = utc_now()
        await db.flush()
        return record

    async def mark_record_completed(
        self,
        db: AsyncSession,
        *,
        record_id: int,
        duration_ms: int,
        summary_title: str | None,
        summary_text: str | None,
    ) -> GenerationRecord | None:
        record = await self.get_record(db, record_id=record_id)
        if record is None:
            return None
        if record.status != "canceled":
            record.status = "completed"
            record.current_stage = "summary"
            record.duration_ms = duration_ms
            record.completed_at = utc_now()
            record.summary_title = summary_title
            record.summary_text = summary_text
        await db.flush()
        return record

    async def mark_record_failed(
        self,
        db: AsyncSession,
        *,
        record_id: int,
        stage: str | None,
        error_code: str,
        error_message: str,
        error_detail: dict[str, Any] | None = None,
    ) -> GenerationRecord | None:
        record = await self.get_record(db, record_id=record_id)
        if record is None:
            return None
        record.status = "failed"
        record.current_stage = stage
        record.failed_at = utc_now()
        record.error_code = error_code
        record.error_message = error_message[:500]
        db.add(
            GenerationError(
                record_id=record_id,
                stage=stage,
                error_source="generation",
                error_code=error_code,
                error_message=error_message,
                error_detail=error_detail or {},
                retryable=True,
            )
        )
        await db.flush()
        return record

    async def save_generation_output(
        self,
        db: AsyncSession,
        *,
        record_id: int,
        output_payload: dict[str, Any],
    ) -> GenerationOutput:
        output = await self._scalar_by_record(db, GenerationOutput, record_id)
        if output is None:
            output = GenerationOutput(record_id=record_id)
            db.add(output)

        output.final_markdown = output_payload.get("final_markdown")
        output.result_json = output_payload.get("result_json") or {}
        output.weather_summary = output_payload.get("weather_summary")
        output.route_summary = output_payload.get("route_summary")
        output.attractions_summary = output_payload.get("attractions_summary")
        output.realtime_info_summary = output_payload.get("realtime_info_summary")
        output.risk_summary = output_payload.get("risk_summary")
        output.amap_route_url = output_payload.get("amap_route_url")
        await db.flush()
        return output

    async def save_generation_snapshot(
        self,
        db: AsyncSession,
        *,
        record_id: int,
        snapshot_type: str,
        data: dict[str, Any],
        input_payload: dict[str, Any],
    ) -> int | None:
        if snapshot_type == "weather":
            snapshot = WeatherSnapshot(
                record_id=record_id,
                provider=data.get("provider") or "mock",
                city_name=data.get("city_name") or input_payload["destination_text"],
                location=data.get("location"),
                weather_date=input_payload.get("travel_date"),
                weather_summary=data.get("weather_summary") or data.get("summary"),
                alert_level=data.get("alert_level"),
                alerts=data.get("alerts") or [],
                request_params={"city": input_payload["destination_text"]},
                response_data=data,
                source_updated_at=self._coerce_datetime(data.get("source_updated_at")),
            )
            db.add(snapshot)
            await db.flush()
            return snapshot.id
        elif snapshot_type == "route":
            snapshot = RouteSnapshot(
                record_id=record_id,
                provider=data.get("provider") or "mock",
                route_type=data.get("transport_mode") or input_payload["transport_mode"],
                origin_location=data.get("origin_location"),
                destination_location=data.get("destination_location"),
                waypoints=data.get("waypoints") or [],
                distance_m=data.get("distance_m"),
                duration_s=data.get("duration_s"),
                request_params={
                    "origin": input_payload["origin_text"],
                    "destination": input_payload["destination_text"],
                },
                response_data=data,
                source_updated_at=self._coerce_datetime(data.get("source_updated_at")),
            )
            db.add(snapshot)
            await db.flush()
            return snapshot.id
        elif snapshot_type == "map_export":
            export = RouteMapExport(
                record_id=record_id,
                route_snapshot_id=data.get("route_snapshot_id"),
                export_type=data.get("export_type") or "mock",
                status=data.get("status") or "completed",
                amap_route_url=data.get("amap_route_url"),
                image_url=data.get("image_url") or data.get("route_map_image"),
                storage_path=data.get("storage_path"),
                width=data.get("width"),
                height=data.get("height"),
                error_message=data.get("error_message"),
            )
            db.add(export)
            await db.flush()
            return export.id
        elif snapshot_type == "realtime":
            snapshot_id: int | None = None
            for category, items in (
                ("traffic", data.get("news_traffic") or []),
                ("pitfall", data.get("guide_pitfall") or []),
            ):
                snapshot = NewsSnapshot(
                    record_id=record_id,
                    provider=data.get("provider") or "mock",
                    query_text=f"{input_payload['destination_text']} {category}",
                    category=category,
                    item_count=len(items),
                    top_titles=[item.get("title", "") for item in items if item.get("title")],
                    source_sites=[
                        item.get("source", "") for item in items if item.get("source")
                    ],
                    credibility_score=self._average_credibility_score(items),
                    response_data={"items": items, "summary": data},
                    source_updated_at=self._coerce_datetime(data.get("source_updated_at")),
                )
                db.add(snapshot)
                await db.flush()
                snapshot_id = snapshot_id or snapshot.id
            return snapshot_id
        await db.flush()
        return None

    async def list_user_records(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        page: int,
        page_size: int,
        status: str | None = None,
        keyword: str | None = None,
    ) -> tuple[int, list[GenerationRecord]]:
        filters = self._record_filters(user_id=user_id, status=status, keyword=keyword)
        total = await self._count(db, select(GenerationRecord).where(*filters))
        stmt = (
            select(GenerationRecord)
            .where(*filters)
            .order_by(GenerationRecord.created_at.desc(), GenerationRecord.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        return total, list(result.scalars().all())

    async def list_admin_records(
        self,
        db: AsyncSession,
        *,
        page: int,
        page_size: int,
        status: str | None = None,
        transport_mode: str | None = None,
        user_keyword: str | None = None,
    ) -> tuple[int, list[tuple[GenerationRecord, str | None, str | None]]]:
        filters = self._record_filters(status=status, transport_mode=transport_mode)
        if user_keyword:
            keyword = f"%{user_keyword.strip()}%"
            filters.append(
                or_(
                    User.username.like(keyword),
                    User.nickname.like(keyword),
                    User.email.like(keyword),
                )
            )

        base_stmt = (
            select(GenerationRecord)
            .outerjoin(User, User.id == GenerationRecord.user_id)
            .where(*filters)
        )
        total = await self._count(db, base_stmt)
        stmt = (
            select(GenerationRecord, User.username, User.nickname)
            .outerjoin(User, User.id == GenerationRecord.user_id)
            .where(*filters)
            .order_by(GenerationRecord.created_at.desc(), GenerationRecord.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        return total, [(row[0], row[1], row[2]) for row in result.all()]

    async def get_record(
        self,
        db: AsyncSession,
        *,
        record_id: int,
        user_id: int | None = None,
    ) -> GenerationRecord | None:
        filters = self._record_filters(user_id=user_id)
        filters.append(GenerationRecord.id == record_id)
        result = await db.execute(select(GenerationRecord).where(*filters))
        return result.scalar_one_or_none()

    async def get_record_input(
        self,
        db: AsyncSession,
        *,
        record_id: int,
    ) -> GenerationInput | None:
        result = await db.execute(
            select(GenerationInput).where(GenerationInput.record_id == record_id)
        )
        return result.scalar_one_or_none()

    async def get_record_detail_components(
        self,
        db: AsyncSession,
        *,
        record_id: int,
        include_llm_logs: bool = False,
    ) -> dict[str, Any]:
        components: dict[str, Any] = {
            "input": await self.get_record_input(db, record_id=record_id),
            "output": await self._scalar_by_record(db, GenerationOutput, record_id),
            "route_snapshots": await self._list_by_record(db, RouteSnapshot, record_id),
            "map_exports": await self._list_by_record(db, RouteMapExport, record_id),
            "weather_snapshots": await self._list_by_record(db, WeatherSnapshot, record_id),
            "news_snapshots": await self._list_by_record(db, NewsSnapshot, record_id),
            "errors": await self._list_by_record(db, GenerationError, record_id),
        }
        if include_llm_logs:
            components["llm_call_logs"] = await self._list_by_record(
                db,
                LlmCallLog,
                record_id,
            )
        return components

    async def create_regeneration_record(
        self,
        db: AsyncSession,
        *,
        parent_record: GenerationRecord,
        record_no: str,
        input_payload: dict[str, Any],
        raw_input: dict[str, Any],
    ) -> GenerationRecord:
        new_record = GenerationRecord(
            record_no=record_no,
            user_id=parent_record.user_id,
            source_client=parent_record.source_client,
            origin_text=input_payload["origin_text"],
            destination_text=input_payload["destination_text"],
            range_text=input_payload["range_text"],
            transport_mode=input_payload["transport_mode"],
            status="pending",
            parent_record_id=parent_record.id,
        )
        db.add(new_record)
        await db.flush()

        db.add(
            GenerationInput(
                record_id=new_record.id,
                origin_text=input_payload["origin_text"],
                destination_text=input_payload["destination_text"],
                range_text=input_payload["range_text"],
                transport_mode=input_payload["transport_mode"],
                travel_date=input_payload.get("travel_date"),
                date_text=input_payload.get("date_text"),
                people_count=input_payload.get("people_count"),
                preferences=input_payload.get("preferences") or [],
                avoidances=input_payload.get("avoidances") or [],
                raw_input=raw_input,
            )
        )
        await db.flush()
        return new_record

    async def soft_delete_record(self, db: AsyncSession, *, record: GenerationRecord) -> None:
        record.deleted_at = utc_now()
        await db.flush()

    async def _count(self, db: AsyncSession, stmt: Select[tuple[Any, ...]]) -> int:
        count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
        result = await db.execute(count_stmt)
        return int(result.scalar_one())

    async def _scalar_by_record(
        self,
        db: AsyncSession,
        model: type[Any],
        record_id: int,
    ) -> Any | None:
        result = await db.execute(select(model).where(model.record_id == record_id))
        return result.scalar_one_or_none()

    async def _list_by_record(
        self,
        db: AsyncSession,
        model: type[Any],
        record_id: int,
    ) -> list[Any]:
        stmt = (
            select(model)
            .where(model.record_id == record_id)
            .order_by(model.created_at.asc(), model.id.asc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    def _record_filters(
        self,
        *,
        user_id: int | None = None,
        status: str | None = None,
        transport_mode: str | None = None,
        keyword: str | None = None,
    ) -> list[Any]:
        filters: list[Any] = [GenerationRecord.deleted_at.is_(None)]
        if user_id is not None:
            filters.append(GenerationRecord.user_id == user_id)
        if status:
            filters.append(GenerationRecord.status == status)
        if transport_mode:
            filters.append(GenerationRecord.transport_mode == transport_mode)
        if keyword:
            keyword_like = f"%{keyword.strip()}%"
            filters.append(
                or_(
                    GenerationRecord.record_no.like(keyword_like),
                    GenerationRecord.origin_text.like(keyword_like),
                    GenerationRecord.destination_text.like(keyword_like),
                    GenerationRecord.summary_title.like(keyword_like),
                    GenerationRecord.summary_text.like(keyword_like),
                )
            )
        return filters

    def _coerce_datetime(self, value: Any) -> datetime | None:
        if isinstance(value, datetime):
            return value.replace(tzinfo=None) if value.tzinfo else value
        if isinstance(value, str) and value:
            normalized = value.replace("Z", "+00:00")
            try:
                parsed = datetime.fromisoformat(normalized)
            except ValueError:
                return None
            return parsed.replace(tzinfo=None) if parsed.tzinfo else parsed
        return None

    def _average_credibility_score(self, items: list[dict[str, Any]]) -> float | None:
        scores = []
        for item in items:
            score = item.get("credibility_score")
            if isinstance(score, int | float):
                scores.append(float(score))
        if not scores:
            return None
        return round(sum(scores) / len(scores), 2)
