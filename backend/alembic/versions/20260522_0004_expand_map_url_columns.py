"""expand map url columns

Revision ID: 20260522_0004
Revises: 20260522_0003
Create Date: 2026-05-22 17:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260522_0004"
down_revision: str | None = "20260522_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "generation_outputs",
        "amap_route_url",
        existing_type=sa.String(length=1000),
        type_=sa.Text(),
        existing_nullable=True,
        comment="高德路线链接",
    )
    op.alter_column(
        "route_map_exports",
        "amap_route_url",
        existing_type=sa.String(length=1000),
        type_=sa.Text(),
        existing_nullable=True,
        comment="高德路线链接",
    )
    op.alter_column(
        "route_map_exports",
        "image_url",
        existing_type=sa.String(length=1000),
        type_=sa.Text(),
        existing_nullable=True,
        comment="图片访问地址",
    )


def downgrade() -> None:
    op.alter_column(
        "route_map_exports",
        "image_url",
        existing_type=sa.Text(),
        type_=sa.String(length=1000),
        existing_nullable=True,
        comment="图片访问地址",
    )
    op.alter_column(
        "route_map_exports",
        "amap_route_url",
        existing_type=sa.Text(),
        type_=sa.String(length=1000),
        existing_nullable=True,
        comment="高德路线链接",
    )
    op.alter_column(
        "generation_outputs",
        "amap_route_url",
        existing_type=sa.Text(),
        type_=sa.String(length=1000),
        existing_nullable=True,
        comment="高德路线链接",
    )
