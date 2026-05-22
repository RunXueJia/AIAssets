"""add record detail order indexes

Revision ID: 20260522_0003
Revises: 20260522_0002
Create Date: 2026-05-22 00:10:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260522_0003"
down_revision: str | None = "20260522_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "idx_route_snapshots_record_created",
        "route_snapshots",
        ["record_id", "created_at", "id"],
    )
    op.create_index(
        "idx_route_map_exports_record_created",
        "route_map_exports",
        ["record_id", "created_at", "id"],
    )
    op.create_index(
        "idx_weather_snapshots_record_created",
        "weather_snapshots",
        ["record_id", "created_at", "id"],
    )
    op.create_index(
        "idx_news_snapshots_record_created",
        "news_snapshots",
        ["record_id", "created_at", "id"],
    )
    op.create_index(
        "idx_generation_errors_record_created",
        "generation_errors",
        ["record_id", "created_at", "id"],
    )
    op.create_index(
        "idx_llm_call_logs_record_created",
        "llm_call_logs",
        ["record_id", "created_at", "id"],
    )


def downgrade() -> None:
    op.drop_index("idx_llm_call_logs_record_created", table_name="llm_call_logs")
    op.drop_index("idx_generation_errors_record_created", table_name="generation_errors")
    op.drop_index("idx_news_snapshots_record_created", table_name="news_snapshots")
    op.drop_index("idx_weather_snapshots_record_created", table_name="weather_snapshots")
    op.drop_index("idx_route_map_exports_record_created", table_name="route_map_exports")
    op.drop_index("idx_route_snapshots_record_created", table_name="route_snapshots")
