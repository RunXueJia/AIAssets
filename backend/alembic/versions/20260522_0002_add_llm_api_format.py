"""add llm api format

Revision ID: 20260522_0002
Revises: 20260521_0001
Create Date: 2026-05-22 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260522_0002"
down_revision: str | None = "20260521_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "llm_configs",
        sa.Column(
            "api_format",
            sa.String(length=50),
            server_default=sa.text("'openai_chat_completions'"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("llm_configs", "api_format")
