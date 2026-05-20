"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-20 10:20:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    ]


def _id() -> sa.Column:
    return sa.Column("id", sa.String(length=32), nullable=False)


def upgrade() -> None:
    op.create_table(
        "role",
        _id(),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("description", sa.String(length=255)),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uk_role_code"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )

    op.create_table(
        "permission",
        _id(),
        sa.Column("code", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("module", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("description", sa.String(length=255)),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uk_permission_code"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("idx_permission_module_type", "permission", ["module", "type"])

    op.create_table(
        "role_permission",
        _id(),
        sa.Column("role_id", sa.String(length=32), nullable=False),
        sa.Column("permission_id", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("role_id", "permission_id", name="uk_role_permission_role_permission"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("idx_role_permission_permission_id", "role_permission", ["permission_id"])
    op.create_index("ix_role_permission_role_id", "role_permission", ["role_id"])

    op.create_table(
        "user",
        _id(),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=64), nullable=False),
        sa.Column("avatar_url", sa.String(length=512)),
        sa.Column("phone", sa.String(length=32)),
        sa.Column("email", sa.String(length=128)),
        sa.Column("role_id", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("last_login_at", sa.DateTime()),
        sa.Column("last_login_ip", sa.String(length=64)),
        sa.Column("deleted_at", sa.DateTime()),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username", name="uk_user_username"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("idx_user_role_id", "user", ["role_id"])
    op.create_index("idx_user_status", "user", ["status"])

    op.create_table(
        "audit_log",
        _id(),
        sa.Column("user_id", sa.String(length=32)),
        sa.Column("username", sa.String(length=64)),
        sa.Column("module", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("resource_type", sa.String(length=64)),
        sa.Column("resource_id", sa.String(length=32)),
        sa.Column("request_method", sa.String(length=16)),
        sa.Column("request_path", sa.String(length=255)),
        sa.Column("request_params_json", sa.JSON()),
        sa.Column("response_status", sa.Integer()),
        sa.Column("ip", sa.String(length=64)),
        sa.Column("user_agent", sa.String(length=512)),
        sa.Column("result", sa.String(length=32)),
        sa.Column("message", sa.String(length=512)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("idx_audit_log_user_id_created_at", "audit_log", ["user_id", "created_at"])
    op.create_index("idx_audit_log_resource", "audit_log", ["resource_type", "resource_id"])
    op.create_index("idx_audit_log_created_at", "audit_log", ["created_at"])

    op.create_table(
        "generation_task",
        _id(),
        sa.Column("direction", sa.String(length=255), nullable=False),
        sa.Column("topic", sa.String(length=255)),
        sa.Column("audience", sa.String(length=255)),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("column_code", sa.String(length=64), nullable=False),
        sa.Column("generation_type", sa.String(length=64), nullable=False),
        sa.Column("start_mode", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("current_stage", sa.String(length=64), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("parent_task_id", sa.String(length=32)),
        sa.Column("source_summary_id", sa.String(length=32)),
        sa.Column("selected_topic_id", sa.String(length=32)),
        sa.Column("final_script_id", sa.String(length=32)),
        sa.Column("final_render_task_id", sa.String(length=32)),
        sa.Column("input_payload_json", sa.JSON()),
        sa.Column("result_payload_json", sa.JSON()),
        sa.Column("error_message", sa.Text()),
        sa.Column("error_code", sa.String(length=64)),
        sa.Column("started_at", sa.DateTime()),
        sa.Column("finished_at", sa.DateTime()),
        sa.Column("created_by", sa.String(length=32)),
        sa.Column("updated_by", sa.String(length=32)),
        sa.Column("deleted_at", sa.DateTime()),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("idx_generation_task_status_created_at", "generation_task", ["status", "created_at"])
    op.create_index("idx_generation_task_created_by", "generation_task", ["created_by"])
    op.create_index("idx_generation_task_current_stage", "generation_task", ["current_stage"])
    op.create_index("idx_generation_task_source_summary_id", "generation_task", ["source_summary_id"])

    op.create_table(
        "render_task",
        _id(),
        sa.Column("generation_task_id", sa.String(length=32)),
        sa.Column("script_id", sa.String(length=32), nullable=False),
        sa.Column("template_code", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("start_mode", sa.String(length=32), nullable=False),
        sa.Column("input_payload_json", sa.JSON()),
        sa.Column("output_video_asset_id", sa.String(length=32)),
        sa.Column("error_message", sa.Text()),
        sa.Column("started_at", sa.DateTime()),
        sa.Column("finished_at", sa.DateTime()),
        sa.Column("created_by", sa.String(length=32)),
        sa.Column("updated_by", sa.String(length=32)),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("idx_render_task_script_id", "render_task", ["script_id"])
    op.create_index("idx_render_task_status_created_at", "render_task", ["status", "created_at"])
    op.create_index("idx_render_task_generation_task_id", "render_task", ["generation_task_id"])

    op.create_table(
        "monitor_task",
        _id(),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("audience", sa.String(length=255)),
        sa.Column("schedule_time", sa.String(length=16), nullable=False),
        sa.Column("fetch_limit", sa.Integer(), nullable=False),
        sa.Column("auto_generate_topics", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("cron_expression", sa.String(length=64)),
        sa.Column("last_run_at", sa.DateTime()),
        sa.Column("next_run_at", sa.DateTime()),
        sa.Column("last_summary_id", sa.String(length=32)),
        sa.Column("created_by", sa.String(length=32)),
        sa.Column("updated_by", sa.String(length=32)),
        sa.Column("deleted_at", sa.DateTime()),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("idx_monitor_task_status", "monitor_task", ["status"])
    op.create_index("idx_monitor_task_next_run_at", "monitor_task", ["next_run_at"])
    op.create_index("idx_monitor_task_created_by", "monitor_task", ["created_by"])

    op.create_table(
        "source_summary",
        _id(),
        sa.Column("summary_type", sa.String(length=32), nullable=False),
        sa.Column("generation_task_id", sa.String(length=32)),
        sa.Column("monitor_task_id", sa.String(length=32)),
        sa.Column("summary_date", sa.Date()),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary_text", mysql.LONGTEXT(), nullable=False),
        sa.Column("key_points_json", sa.JSON()),
        sa.Column("risk_notes_json", sa.JSON()),
        sa.Column("source_count", sa.Integer(), nullable=False),
        sa.Column("usable_source_count", sa.Integer(), nullable=False),
        sa.Column("need_human_confirm", sa.Boolean(), nullable=False),
        sa.Column("llm_model_name", sa.String(length=128)),
        sa.Column("llm_raw_output", mysql.LONGTEXT()),
        sa.Column("created_by", sa.String(length=32)),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("idx_source_summary_generation_task_id", "source_summary", ["generation_task_id"])
    op.create_index("idx_source_summary_monitor_task_id_summary_date", "source_summary", ["monitor_task_id", "summary_date"])
    op.create_index("idx_source_summary_type_created_at", "source_summary", ["summary_type", "created_at"])

    op.create_table(
        "source_item",
        _id(),
        sa.Column("source_summary_id", sa.String(length=32)),
        sa.Column("generation_task_id", sa.String(length=32)),
        sa.Column("monitor_task_id", sa.String(length=32)),
        sa.Column("source_hash", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("site_name", sa.String(length=128)),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column("author", sa.String(length=128)),
        sa.Column("published_at", sa.DateTime()),
        sa.Column("summary_text", sa.Text()),
        sa.Column("relevance_reason", sa.Text()),
        sa.Column("key_points_json", sa.JSON()),
        sa.Column("raw_content_text", mysql.LONGTEXT()),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("need_human_confirm", sa.Boolean(), nullable=False),
        sa.Column("fetch_status", sa.String(length=32), nullable=False),
        sa.Column("fetch_error_message", sa.Text()),
        sa.Column("source_order", sa.Integer(), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("idx_source_item_source_summary_id", "source_item", ["source_summary_id"])
    op.create_index("idx_source_item_generation_task_id", "source_item", ["generation_task_id"])
    op.create_index("idx_source_item_monitor_task_id", "source_item", ["monitor_task_id"])
    op.create_index("idx_source_item_status", "source_item", ["status"])
    op.create_index("idx_source_item_source_hash", "source_item", ["source_hash"])
    op.create_index("idx_source_item_url", "source_item", ["url"], mysql_length=255)

    op.create_table(
        "topic",
        _id(),
        sa.Column("generation_task_id", sa.String(length=32), nullable=False),
        sa.Column("source_summary_id", sa.String(length=32)),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("audience", sa.String(length=255)),
        sa.Column("angle", sa.Text()),
        sa.Column("recommended_column", sa.String(length=64)),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("keywords_json", sa.JSON()),
        sa.Column("reason", sa.Text()),
        sa.Column("score", sa.Float()),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("need_human_confirm", sa.Boolean(), nullable=False),
        sa.Column("lock_user_id", sa.String(length=32)),
        sa.Column("lock_at", sa.DateTime()),
        sa.Column("reject_reason", sa.Text()),
        sa.Column("approved_by", sa.String(length=32)),
        sa.Column("approved_at", sa.DateTime()),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("idx_topic_generation_task_id", "topic", ["generation_task_id"])
    op.create_index("idx_topic_source_summary_id", "topic", ["source_summary_id"])
    op.create_index("idx_topic_status", "topic", ["status"])
    op.create_index("idx_topic_lock_user_id", "topic", ["lock_user_id"])

    op.create_table(
        "script",
        _id(),
        sa.Column("topic_id", sa.String(length=32)),
        sa.Column("generation_task_id", sa.String(length=32), nullable=False),
        sa.Column("source_summary_id", sa.String(length=32)),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("hook", sa.Text()),
        sa.Column("pain_point", sa.Text()),
        sa.Column("method", sa.Text()),
        sa.Column("steps_json", sa.JSON()),
        sa.Column("example_text", sa.Text()),
        sa.Column("summary_text", sa.Text()),
        sa.Column("cta_text", sa.Text()),
        sa.Column("platform_title", sa.String(length=255)),
        sa.Column("description", sa.Text()),
        sa.Column("tags_json", sa.JSON()),
        sa.Column("cover_text", sa.String(length=255)),
        sa.Column("pinned_comment", sa.Text()),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("current_version_no", sa.Integer(), nullable=False),
        sa.Column("need_human_confirm", sa.Boolean(), nullable=False),
        sa.Column("risk_notes_json", sa.JSON()),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("idx_script_topic_id", "script", ["topic_id"])
    op.create_index("idx_script_generation_task_id", "script", ["generation_task_id"])
    op.create_index("idx_script_status", "script", ["status"])

    op.create_table(
        "storyboard",
        _id(),
        sa.Column("script_id", sa.String(length=32), nullable=False),
        sa.Column("shot_no", sa.Integer(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("voiceover", sa.Text(), nullable=False),
        sa.Column("subtitle", sa.Text(), nullable=False),
        sa.Column("visual_type", sa.String(length=64), nullable=False),
        sa.Column("material_suggestion", sa.Text()),
        sa.Column("motion_suggestion", sa.Text()),
        sa.Column("scene_note", sa.Text()),
        sa.Column("status", sa.String(length=32), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("script_id", "shot_no", name="uk_storyboard_script_shot_no"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("idx_storyboard_script_id", "storyboard", ["script_id"])

    op.create_table(
        "subtitle",
        _id(),
        sa.Column("script_id", sa.String(length=32), nullable=False),
        sa.Column("line_no", sa.Integer(), nullable=False),
        sa.Column("start_time_ms", sa.Integer(), nullable=False),
        sa.Column("end_time_ms", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("speaker", sa.String(length=64)),
        sa.Column("style_name", sa.String(length=64)),
        sa.Column("status", sa.String(length=32), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("script_id", "line_no", name="uk_subtitle_script_line_no"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("idx_subtitle_script_id", "subtitle", ["script_id"])

    op.create_table(
        "content_version",
        _id(),
        sa.Column("content_type", sa.String(length=32), nullable=False),
        sa.Column("content_id", sa.String(length=32), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("change_note", sa.String(length=255)),
        sa.Column("operator_id", sa.String(length=32)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("content_type", "content_id", "version_no", name="uk_content_version_type_id_no"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("idx_content_version_content_id", "content_version", ["content_id"])

    op.create_table(
        "review_record",
        _id(),
        sa.Column("content_type", sa.String(length=32), nullable=False),
        sa.Column("content_id", sa.String(length=32), nullable=False),
        sa.Column("generation_task_id", sa.String(length=32)),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("before_status", sa.String(length=32)),
        sa.Column("after_status", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text()),
        sa.Column("comment", sa.Text()),
        sa.Column("edited_payload_json", sa.JSON()),
        sa.Column("reviewer_id", sa.String(length=32)),
        sa.Column("reviewer_name", sa.String(length=64)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("idx_review_record_content", "review_record", ["content_type", "content_id"])
    op.create_index("idx_review_record_generation_task_id", "review_record", ["generation_task_id"])
    op.create_index("idx_review_record_reviewer_id", "review_record", ["reviewer_id"])

    op.create_table(
        "video_asset",
        _id(),
        sa.Column("script_id", sa.String(length=32), nullable=False),
        sa.Column("render_task_id", sa.String(length=32)),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("storage_provider", sa.String(length=32), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(length=128), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(length=128)),
        sa.Column("status", sa.String(length=32), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("idx_video_asset_script_id", "video_asset", ["script_id"])
    op.create_index("idx_video_asset_render_task_id", "video_asset", ["render_task_id"])

    for table_name, default_mime, extra_cols in [
        ("cover_asset", "image/jpeg", [sa.Column("width", sa.Integer()), sa.Column("height", sa.Integer())]),
        ("card_asset", "image/png", []),
    ]:
        op.create_table(
            table_name,
            _id(),
            sa.Column("script_id", sa.String(length=32), nullable=False),
            sa.Column("package_id", sa.String(length=32)),
            sa.Column("file_name", sa.String(length=255), nullable=False),
            sa.Column("file_path", sa.String(length=1024), nullable=False),
            sa.Column("storage_provider", sa.String(length=32), nullable=False),
            sa.Column("file_size", sa.Integer(), nullable=False),
            sa.Column("mime_type", sa.String(length=128), nullable=False, server_default=default_mime),
            *extra_cols,
            sa.Column("checksum", sa.String(length=128)),
            sa.Column("status", sa.String(length=32), nullable=False),
            *_timestamps(),
            sa.PrimaryKeyConstraint("id"),
            mysql_charset="utf8mb4",
            mysql_collate="utf8mb4_unicode_ci",
        )
        op.create_index(f"idx_{table_name}_script_id", table_name, ["script_id"])
        op.create_index(f"idx_{table_name}_package_id", table_name, ["package_id"])

    op.create_table(
        "download_asset",
        _id(),
        sa.Column("script_id", sa.String(length=32), nullable=False),
        sa.Column("package_id", sa.String(length=32)),
        sa.Column("draft_name", sa.String(length=255), nullable=False),
        sa.Column("draft_text", mysql.LONGTEXT()),
        sa.Column("file_name", sa.String(length=255)),
        sa.Column("file_path", sa.String(length=1024)),
        sa.Column("storage_provider", sa.String(length=32), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(length=128)),
        sa.Column("checksum", sa.String(length=128)),
        sa.Column("status", sa.String(length=32), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("idx_download_asset_script_id", "download_asset", ["script_id"])
    op.create_index("idx_download_asset_package_id", "download_asset", ["package_id"])

    op.create_table(
        "publish_package",
        _id(),
        sa.Column("script_id", sa.String(length=32), nullable=False),
        sa.Column("render_task_id", sa.String(length=32)),
        sa.Column("video_asset_id", sa.String(length=32)),
        sa.Column("cover_asset_id", sa.String(length=32)),
        sa.Column("card_asset_id", sa.String(length=32)),
        sa.Column("download_asset_id", sa.String(length=32)),
        sa.Column("package_name", sa.String(length=255), nullable=False),
        sa.Column("platform_title", sa.String(length=255)),
        sa.Column("description", sa.Text()),
        sa.Column("tags_json", sa.JSON()),
        sa.Column("pinned_comment", sa.Text()),
        sa.Column("platforms_json", sa.JSON()),
        sa.Column("package_status", sa.String(length=32), nullable=False),
        sa.Column("file_name", sa.String(length=255)),
        sa.Column("file_path", sa.String(length=1024)),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(length=128)),
        sa.Column("exported_by", sa.String(length=32)),
        sa.Column("exported_at", sa.DateTime()),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("idx_publish_package_script_id", "publish_package", ["script_id"])
    op.create_index("idx_publish_package_render_task_id", "publish_package", ["render_task_id"])
    op.create_index("idx_publish_package_status", "publish_package", ["package_status"])

    op.create_table(
        "publish_record",
        _id(),
        sa.Column("package_id", sa.String(length=32), nullable=False),
        sa.Column("script_id", sa.String(length=32)),
        sa.Column("platform", sa.String(length=64), nullable=False),
        sa.Column("platform_url", sa.String(length=1024)),
        sa.Column("published_at", sa.DateTime()),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("remark", sa.Text()),
        sa.Column("created_by", sa.String(length=32)),
        sa.Column("updated_by", sa.String(length=32)),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("idx_publish_record_package_id", "publish_record", ["package_id"])
    op.create_index("idx_publish_record_platform", "publish_record", ["platform"])
    op.create_index("idx_publish_record_status", "publish_record", ["status"])

    op.create_table(
        "task_log",
        _id(),
        sa.Column("task_type", sa.String(length=32), nullable=False),
        sa.Column("task_id", sa.String(length=32), nullable=False),
        sa.Column("generation_task_id", sa.String(length=32)),
        sa.Column("monitor_task_id", sa.String(length=32)),
        sa.Column("related_content_type", sa.String(length=32)),
        sa.Column("related_content_id", sa.String(length=32)),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("stage", sa.String(length=64)),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("detail_json", sa.JSON()),
        sa.Column("error_code", sa.String(length=64)),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("idx_task_log_task_type_task_id", "task_log", ["task_type", "task_id"])
    op.create_index("idx_task_log_related_content", "task_log", ["related_content_type", "related_content_id"])
    op.create_index("idx_task_log_level_created_at", "task_log", ["level", "created_at"])
    op.create_index("idx_task_log_created_at", "task_log", ["created_at"])

    op.create_table(
        "daily_report",
        _id(),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("generation_task_count", sa.Integer(), nullable=False),
        sa.Column("source_item_count", sa.Integer(), nullable=False),
        sa.Column("topic_count", sa.Integer(), nullable=False),
        sa.Column("script_count", sa.Integer(), nullable=False),
        sa.Column("storyboard_count", sa.Integer(), nullable=False),
        sa.Column("subtitle_count", sa.Integer(), nullable=False),
        sa.Column("render_count", sa.Integer(), nullable=False),
        sa.Column("package_count", sa.Integer(), nullable=False),
        sa.Column("failed_task_count", sa.Integer(), nullable=False),
        sa.Column("success_rate", sa.Float(), nullable=False),
        sa.Column("overview_json", sa.JSON()),
        sa.Column("content_json", sa.JSON()),
        sa.Column("markdown_path", sa.String(length=1024)),
        sa.Column("pdf_path", sa.String(length=1024)),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("report_date", name="uk_daily_report_report_date"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )

    op.create_table(
        "system_setting",
        _id(),
        sa.Column("setting_key", sa.String(length=128), nullable=False),
        sa.Column("setting_name", sa.String(length=128), nullable=False),
        sa.Column("setting_group", sa.String(length=64), nullable=False),
        sa.Column("setting_value_json", sa.JSON()),
        sa.Column("value_type", sa.String(length=32), nullable=False),
        sa.Column("is_secret", sa.Boolean(), nullable=False),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("description", sa.String(length=255)),
        sa.Column("updated_by", sa.String(length=32)),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("setting_key", name="uk_system_setting_key"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("idx_system_setting_group", "system_setting", ["setting_group"])


def downgrade() -> None:
    for table_name in [
        "system_setting",
        "daily_report",
        "task_log",
        "publish_record",
        "publish_package",
        "download_asset",
        "card_asset",
        "cover_asset",
        "video_asset",
        "review_record",
        "content_version",
        "subtitle",
        "storyboard",
        "script",
        "topic",
        "source_item",
        "source_summary",
        "monitor_task",
        "render_task",
        "generation_task",
        "audit_log",
        "user",
        "role_permission",
        "permission",
        "role",
    ]:
        op.drop_table(table_name)
