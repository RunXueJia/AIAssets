from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, Index, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, MEDIUMTEXT
from sqlalchemy.dialects.mysql import JSON as MySQLJSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, BigIntPrimaryKeyMixin, TimestampMixin


class GenerationRecord(BigIntPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "generation_records"
    __table_args__ = (
        Index("idx_generation_records_user_created", "user_id", "created_at"),
        Index("idx_generation_records_status_created", "status", "created_at"),
        Index("idx_generation_records_transport_created", "transport_mode", "created_at"),
        Index("idx_generation_records_parent", "parent_record_id"),
        {"comment": "生成记录主表"},
    )

    record_no: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    source_client: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'web'")
    )
    origin_text: Mapped[str] = mapped_column(String(255), nullable=False)
    destination_text: Mapped[str] = mapped_column(String(255), nullable=False)
    range_text: Mapped[str] = mapped_column(String(120), nullable=False)
    transport_mode: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'pending'")
    )
    current_stage: Mapped[str | None] = mapped_column(String(40), nullable=True)
    summary_title: Mapped[str | None] = mapped_column(String(160), nullable=True)
    summary_text: Mapped[str | None] = mapped_column(String(500), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(INTEGER(unsigned=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(
        INTEGER(unsigned=True), nullable=False, server_default=text("0")
    )
    parent_record_id: Mapped[int | None] = mapped_column(BIGINT(unsigned=True), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class GenerationInput(BigIntPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "generation_inputs"
    __table_args__ = (
        UniqueConstraint("record_id", name="uk_generation_inputs_record"),
        Index("idx_generation_inputs_transport", "transport_mode"),
        Index("idx_generation_inputs_travel_date", "travel_date"),
        {"comment": "生成输入快照"},
    )

    record_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    origin_text: Mapped[str] = mapped_column(String(255), nullable=False)
    destination_text: Mapped[str] = mapped_column(String(255), nullable=False)
    range_text: Mapped[str] = mapped_column(String(120), nullable=False)
    transport_mode: Mapped[str] = mapped_column(String(30), nullable=False)
    travel_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_text: Mapped[str | None] = mapped_column(String(120), nullable=True)
    people_count: Mapped[int | None] = mapped_column(INTEGER(unsigned=True), nullable=True)
    preferences: Mapped[list[str] | None] = mapped_column(MySQLJSON, nullable=True)
    avoidances: Mapped[list[str] | None] = mapped_column(MySQLJSON, nullable=True)
    raw_input: Mapped[dict[str, Any]] = mapped_column(MySQLJSON, nullable=False)


class GenerationOutput(BigIntPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "generation_outputs"
    __table_args__ = (
        UniqueConstraint("record_id", name="uk_generation_outputs_record"),
        Index("idx_generation_outputs_map_export", "map_export_id"),
        {"comment": "生成输出结果"},
    )

    record_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    final_markdown: Mapped[str | None] = mapped_column(MEDIUMTEXT, nullable=True)
    result_json: Mapped[dict[str, Any] | None] = mapped_column(MySQLJSON, nullable=True)
    weather_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    route_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    attractions_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    realtime_info_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    amap_route_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    map_export_id: Mapped[int | None] = mapped_column(BIGINT(unsigned=True), nullable=True)
    output_version: Mapped[int] = mapped_column(
        INTEGER(unsigned=True), nullable=False, server_default=text("1")
    )


class GenerationStreamEvent(BigIntPrimaryKeyMixin, Base):
    __tablename__ = "generation_stream_events"
    __table_args__ = (
        UniqueConstraint("record_id", "sequence_no", name="uk_stream_events_record_seq"),
        Index("idx_stream_events_record_created", "record_id", "created_at"),
        Index("idx_stream_events_type", "event_type"),
        {"comment": "流式输出事件"},
    )

    record_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    sequence_no: Mapped[int] = mapped_column(INTEGER(unsigned=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    stage: Mapped[str | None] = mapped_column(String(40), nullable=True)
    content: Mapped[str | None] = mapped_column(MEDIUMTEXT, nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(MySQLJSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class GenerationError(BigIntPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "generation_errors"
    __table_args__ = (
        Index("idx_generation_errors_record", "record_id"),
        Index("idx_generation_errors_source_created", "error_source", "created_at"),
        Index("idx_generation_errors_retryable", "retryable"),
        {"comment": "生成错误记录"},
    )

    record_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    stage: Mapped[str | None] = mapped_column(String(40), nullable=True)
    error_source: Mapped[str] = mapped_column(String(40), nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    error_message: Mapped[str] = mapped_column(String(1000), nullable=False)
    error_detail: Mapped[dict[str, Any] | None] = mapped_column(MySQLJSON, nullable=True)
    retryable: Mapped[bool] = mapped_column(nullable=False, server_default=text("0"))
    handled_by: Mapped[int | None] = mapped_column(BIGINT(unsigned=True), nullable=True)
    handled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
