from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, Index, Numeric, String, Text, text
from sqlalchemy.dialects.mysql import BIGINT, INTEGER
from sqlalchemy.dialects.mysql import JSON as MySQLJSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, BigIntPrimaryKeyMixin, TimestampMixin


class LlmConfig(BigIntPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "llm_configs"
    __table_args__ = (
        Index("idx_llm_configs_status_default", "status", "is_default"),
        Index("idx_llm_configs_provider_model", "provider", "model_name"),
        Index("idx_llm_configs_created_by", "created_by"),
        {"comment": "LLM配置"},
    )

    name: Mapped[str] = mapped_column(String(80), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    api_key_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    api_key_masked: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'disabled'")
    )
    is_default: Mapped[bool] = mapped_column(nullable=False, server_default=text("0"))
    timeout_s: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
        server_default=text("60"),
    )
    max_tokens: Mapped[int | None] = mapped_column(INTEGER(unsigned=True), nullable=True)
    temperature: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)
    last_test_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    last_test_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_test_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    updated_by: Mapped[int | None] = mapped_column(BIGINT(unsigned=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class LlmCallLog(BigIntPrimaryKeyMixin, Base):
    __tablename__ = "llm_call_logs"
    __table_args__ = (
        Index("idx_llm_call_logs_record", "record_id"),
        Index("idx_llm_call_logs_config_created", "llm_config_id", "created_at"),
        Index("idx_llm_call_logs_status_created", "status", "created_at"),
        Index("idx_llm_call_logs_provider_model", "provider", "model_name"),
        {"comment": "LLM调用日志"},
    )

    record_id: Mapped[int | None] = mapped_column(BIGINT(unsigned=True), nullable=True)
    llm_config_id: Mapped[int | None] = mapped_column(BIGINT(unsigned=True), nullable=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    call_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    prompt_tokens: Mapped[int | None] = mapped_column(INTEGER(unsigned=True), nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(INTEGER(unsigned=True), nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(INTEGER(unsigned=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(INTEGER(unsigned=True), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class ConfigAuditLog(BigIntPrimaryKeyMixin, Base):
    __tablename__ = "config_audit_logs"
    __table_args__ = (
        Index("idx_config_audit_logs_config", "config_type", "config_id"),
        Index("idx_config_audit_logs_operator_created", "operator_id", "created_at"),
        Index("idx_config_audit_logs_action_created", "action", "created_at"),
        {"comment": "配置审计日志"},
    )

    config_type: Mapped[str] = mapped_column(String(40), nullable=False)
    config_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    operator_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    before_data: Mapped[dict[str, Any] | None] = mapped_column(MySQLJSON, nullable=True)
    after_data: Mapped[dict[str, Any] | None] = mapped_column(MySQLJSON, nullable=True)
    change_summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
