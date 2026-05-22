"""initial schema

Revision ID: 20260521_0001
Revises:
Create Date: 2026-05-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

revision: str = "20260521_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            server_onupdate=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    ]


def pk() -> sa.Column:
    return sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False)


def upgrade() -> None:
    op.create_table(
        "users",
        pk(),
        sa.Column("username", sa.String(length=64), nullable=True),
        sa.Column("nickname", sa.String(length=64), nullable=True),
        sa.Column("email", sa.String(length=128), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("role", sa.String(length=20), server_default=sa.text("'user'"), nullable=False),
        sa.Column(
            "status", sa.String(length=20), server_default=sa.text("'active'"), nullable=False
        ),
        sa.Column("guest_token_hash", sa.String(length=128), nullable=True),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        *timestamps(),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("phone"),
        sa.UniqueConstraint("username"),
        comment="用户账号",
    )
    op.create_index("idx_users_created_at", "users", ["created_at"])
    op.create_index("idx_users_role_status", "users", ["role", "status"])

    op.create_table(
        "login_sessions",
        pk(),
        sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("session_token_hash", sa.String(length=128), nullable=False),
        sa.Column("refresh_token_hash", sa.String(length=128), nullable=True),
        sa.Column(
            "client_type", sa.String(length=20), server_default=sa.text("'web'"), nullable=False
        ),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_token_hash"),
        comment="登录会话",
    )
    op.create_index("idx_login_sessions_expires_at", "login_sessions", ["expires_at"])
    op.create_index("idx_login_sessions_revoked_at", "login_sessions", ["revoked_at"])
    op.create_index("idx_login_sessions_user_id", "login_sessions", ["user_id"])

    op.create_table(
        "generation_records",
        pk(),
        sa.Column("record_no", sa.String(length=40), nullable=False),
        sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column(
            "source_client", sa.String(length=20), server_default=sa.text("'web'"), nullable=False
        ),
        sa.Column("origin_text", sa.String(length=255), nullable=False),
        sa.Column("destination_text", sa.String(length=255), nullable=False),
        sa.Column("range_text", sa.String(length=120), nullable=False),
        sa.Column("transport_mode", sa.String(length=30), nullable=False),
        sa.Column(
            "status", sa.String(length=20), server_default=sa.text("'pending'"), nullable=False
        ),
        sa.Column("current_stage", sa.String(length=40), nullable=True),
        sa.Column("summary_title", sa.String(length=160), nullable=True),
        sa.Column("summary_text", sa.String(length=500), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("canceled_at", sa.DateTime(), nullable=True),
        sa.Column("failed_at", sa.DateTime(), nullable=True),
        sa.Column("duration_ms", mysql.INTEGER(unsigned=True), nullable=True),
        sa.Column(
            "retry_count", mysql.INTEGER(unsigned=True), server_default=sa.text("0"), nullable=False
        ),
        sa.Column("parent_record_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        *timestamps(),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("record_no"),
        comment="生成记录主表",
    )
    op.create_index("idx_generation_records_parent", "generation_records", ["parent_record_id"])
    op.create_index(
        "idx_generation_records_status_created", "generation_records", ["status", "created_at"]
    )
    op.create_index(
        "idx_generation_records_transport_created",
        "generation_records",
        ["transport_mode", "created_at"],
    )
    op.create_index(
        "idx_generation_records_user_created", "generation_records", ["user_id", "created_at"]
    )

    op.create_table(
        "generation_inputs",
        pk(),
        sa.Column("record_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("origin_text", sa.String(length=255), nullable=False),
        sa.Column("destination_text", sa.String(length=255), nullable=False),
        sa.Column("range_text", sa.String(length=120), nullable=False),
        sa.Column("transport_mode", sa.String(length=30), nullable=False),
        sa.Column("travel_date", sa.Date(), nullable=True),
        sa.Column("date_text", sa.String(length=120), nullable=True),
        sa.Column("people_count", mysql.INTEGER(unsigned=True), nullable=True),
        sa.Column("preferences", mysql.JSON(), nullable=True),
        sa.Column("avoidances", mysql.JSON(), nullable=True),
        sa.Column("raw_input", mysql.JSON(), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("record_id", name="uk_generation_inputs_record"),
        comment="生成输入快照",
    )
    op.create_index("idx_generation_inputs_transport", "generation_inputs", ["transport_mode"])
    op.create_index("idx_generation_inputs_travel_date", "generation_inputs", ["travel_date"])

    op.create_table(
        "generation_outputs",
        pk(),
        sa.Column("record_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("final_markdown", mysql.MEDIUMTEXT(), nullable=True),
        sa.Column("result_json", mysql.JSON(), nullable=True),
        sa.Column("weather_summary", sa.Text(), nullable=True),
        sa.Column("route_summary", sa.Text(), nullable=True),
        sa.Column("attractions_summary", sa.Text(), nullable=True),
        sa.Column("realtime_info_summary", sa.Text(), nullable=True),
        sa.Column("risk_summary", sa.Text(), nullable=True),
        sa.Column("amap_route_url", sa.String(length=1000), nullable=True),
        sa.Column("map_export_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column(
            "output_version",
            mysql.INTEGER(unsigned=True),
            server_default=sa.text("1"),
            nullable=False,
        ),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("record_id", name="uk_generation_outputs_record"),
        comment="生成输出结果",
    )
    op.create_index("idx_generation_outputs_map_export", "generation_outputs", ["map_export_id"])

    op.create_table(
        "generation_stream_events",
        pk(),
        sa.Column("record_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("sequence_no", mysql.INTEGER(unsigned=True), nullable=False),
        sa.Column("event_type", sa.String(length=30), nullable=False),
        sa.Column("stage", sa.String(length=40), nullable=True),
        sa.Column("content", mysql.MEDIUMTEXT(), nullable=True),
        sa.Column("payload", mysql.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("record_id", "sequence_no", name="uk_stream_events_record_seq"),
        comment="流式输出事件",
    )
    op.create_index(
        "idx_stream_events_record_created", "generation_stream_events", ["record_id", "created_at"]
    )
    op.create_index("idx_stream_events_type", "generation_stream_events", ["event_type"])

    op.create_table(
        "generation_errors",
        pk(),
        sa.Column("record_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("stage", sa.String(length=40), nullable=True),
        sa.Column("error_source", sa.String(length=40), nullable=False),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("error_message", sa.String(length=1000), nullable=False),
        sa.Column("error_detail", mysql.JSON(), nullable=True),
        sa.Column("retryable", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("handled_by", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("handled_at", sa.DateTime(), nullable=True),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        comment="生成错误记录",
    )
    op.create_index("idx_generation_errors_record", "generation_errors", ["record_id"])
    op.create_index("idx_generation_errors_retryable", "generation_errors", ["retryable"])
    op.create_index(
        "idx_generation_errors_source_created", "generation_errors", ["error_source", "created_at"]
    )

    op.create_table(
        "route_snapshots",
        pk(),
        sa.Column("record_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column(
            "provider", sa.String(length=30), server_default=sa.text("'amap'"), nullable=False
        ),
        sa.Column("route_type", sa.String(length=30), nullable=False),
        sa.Column("origin_location", sa.String(length=64), nullable=True),
        sa.Column("destination_location", sa.String(length=64), nullable=True),
        sa.Column("waypoints", mysql.JSON(), nullable=True),
        sa.Column("distance_m", mysql.INTEGER(unsigned=True), nullable=True),
        sa.Column("duration_s", mysql.INTEGER(unsigned=True), nullable=True),
        sa.Column("request_params", mysql.JSON(), nullable=False),
        sa.Column("response_data", mysql.JSON(), nullable=False),
        sa.Column("source_updated_at", sa.DateTime(), nullable=True),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        comment="地图路线快照",
    )
    op.create_index("idx_route_snapshots_provider", "route_snapshots", ["provider"])
    op.create_index("idx_route_snapshots_record", "route_snapshots", ["record_id"])
    op.create_index(
        "idx_route_snapshots_type_created", "route_snapshots", ["route_type", "created_at"]
    )

    op.create_table(
        "route_map_exports",
        pk(),
        sa.Column("record_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("route_snapshot_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("export_type", sa.String(length=30), nullable=False),
        sa.Column(
            "status", sa.String(length=20), server_default=sa.text("'pending'"), nullable=False
        ),
        sa.Column("amap_route_url", sa.String(length=1000), nullable=True),
        sa.Column("image_url", sa.String(length=1000), nullable=True),
        sa.Column("storage_path", sa.String(length=500), nullable=True),
        sa.Column("width", mysql.INTEGER(unsigned=True), nullable=True),
        sa.Column("height", mysql.INTEGER(unsigned=True), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        comment="路径图导出",
    )
    op.create_index("idx_route_map_exports_record", "route_map_exports", ["record_id"])
    op.create_index("idx_route_map_exports_snapshot", "route_map_exports", ["route_snapshot_id"])
    op.create_index("idx_route_map_exports_status", "route_map_exports", ["status"])

    op.create_table(
        "weather_snapshots",
        pk(),
        sa.Column("record_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("city_name", sa.String(length=80), nullable=False),
        sa.Column("location", sa.String(length=64), nullable=True),
        sa.Column("weather_date", sa.Date(), nullable=True),
        sa.Column("weather_summary", sa.String(length=500), nullable=True),
        sa.Column("alert_level", sa.String(length=30), nullable=True),
        sa.Column("alerts", mysql.JSON(), nullable=True),
        sa.Column("request_params", mysql.JSON(), nullable=False),
        sa.Column("response_data", mysql.JSON(), nullable=False),
        sa.Column("source_updated_at", sa.DateTime(), nullable=True),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        comment="天气快照",
    )
    op.create_index("idx_weather_snapshots_alert", "weather_snapshots", ["alert_level"])
    op.create_index(
        "idx_weather_snapshots_city_date", "weather_snapshots", ["city_name", "weather_date"]
    )
    op.create_index("idx_weather_snapshots_record", "weather_snapshots", ["record_id"])

    op.create_table(
        "news_snapshots",
        pk(),
        sa.Column("record_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("query_text", sa.String(length=255), nullable=False),
        sa.Column(
            "category", sa.String(length=30), server_default=sa.text("'news'"), nullable=False
        ),
        sa.Column(
            "item_count", mysql.INTEGER(unsigned=True), server_default=sa.text("0"), nullable=False
        ),
        sa.Column("top_titles", mysql.JSON(), nullable=True),
        sa.Column("source_sites", mysql.JSON(), nullable=True),
        sa.Column("credibility_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("response_data", mysql.JSON(), nullable=False),
        sa.Column("source_updated_at", sa.DateTime(), nullable=True),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        comment="实时信息检索快照",
    )
    op.create_index("idx_news_snapshots_category", "news_snapshots", ["category"])
    op.create_index(
        "idx_news_snapshots_provider_category", "news_snapshots", ["provider", "category"]
    )
    op.create_index(
        "idx_news_snapshots_query_created", "news_snapshots", ["query_text", "created_at"]
    )
    op.create_index("idx_news_snapshots_record", "news_snapshots", ["record_id"])

    op.create_table(
        "llm_configs",
        pk(),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("base_url", sa.String(length=500), nullable=False),
        sa.Column("model_name", sa.String(length=120), nullable=False),
        sa.Column("api_key_encrypted", sa.Text(), nullable=False),
        sa.Column("api_key_masked", sa.String(length=80), nullable=False),
        sa.Column(
            "status", sa.String(length=20), server_default=sa.text("'disabled'"), nullable=False
        ),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "timeout_s", mysql.INTEGER(unsigned=True), server_default=sa.text("60"), nullable=False
        ),
        sa.Column("max_tokens", mysql.INTEGER(unsigned=True), nullable=True),
        sa.Column("temperature", sa.Numeric(4, 3), nullable=True),
        sa.Column("last_test_status", sa.String(length=20), nullable=True),
        sa.Column("last_test_message", sa.String(length=500), nullable=True),
        sa.Column("last_test_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("updated_by", mysql.BIGINT(unsigned=True), nullable=True),
        *timestamps(),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        comment="LLM配置",
    )
    op.create_index("idx_llm_configs_created_by", "llm_configs", ["created_by"])
    op.create_index("idx_llm_configs_provider_model", "llm_configs", ["provider", "model_name"])
    op.create_index("idx_llm_configs_status_default", "llm_configs", ["status", "is_default"])

    op.create_table(
        "llm_call_logs",
        pk(),
        sa.Column("record_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("llm_config_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model_name", sa.String(length=120), nullable=False),
        sa.Column("call_type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("prompt_tokens", mysql.INTEGER(unsigned=True), nullable=True),
        sa.Column("completion_tokens", mysql.INTEGER(unsigned=True), nullable=True),
        sa.Column("total_tokens", mysql.INTEGER(unsigned=True), nullable=True),
        sa.Column("duration_ms", mysql.INTEGER(unsigned=True), nullable=True),
        sa.Column("request_id", sa.String(length=120), nullable=True),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("error_message", sa.String(length=1000), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        comment="LLM调用日志",
    )
    op.create_index(
        "idx_llm_call_logs_config_created", "llm_call_logs", ["llm_config_id", "created_at"]
    )
    op.create_index("idx_llm_call_logs_provider_model", "llm_call_logs", ["provider", "model_name"])
    op.create_index("idx_llm_call_logs_record", "llm_call_logs", ["record_id"])
    op.create_index("idx_llm_call_logs_status_created", "llm_call_logs", ["status", "created_at"])

    op.create_table(
        "config_audit_logs",
        pk(),
        sa.Column("config_type", sa.String(length=40), nullable=False),
        sa.Column("config_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("action", sa.String(length=40), nullable=False),
        sa.Column("operator_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("before_data", mysql.JSON(), nullable=True),
        sa.Column("after_data", mysql.JSON(), nullable=True),
        sa.Column("change_summary", sa.String(length=500), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        comment="配置审计日志",
    )
    op.create_index(
        "idx_config_audit_logs_action_created", "config_audit_logs", ["action", "created_at"]
    )
    op.create_index(
        "idx_config_audit_logs_config", "config_audit_logs", ["config_type", "config_id"]
    )
    op.create_index(
        "idx_config_audit_logs_operator_created", "config_audit_logs", ["operator_id", "created_at"]
    )


def downgrade() -> None:
    for table_name in (
        "config_audit_logs",
        "llm_call_logs",
        "llm_configs",
        "news_snapshots",
        "weather_snapshots",
        "route_map_exports",
        "route_snapshots",
        "generation_errors",
        "generation_stream_events",
        "generation_outputs",
        "generation_inputs",
        "generation_records",
        "login_sessions",
        "users",
    ):
        op.drop_table(table_name)
