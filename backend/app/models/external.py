from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Date, DateTime, Index, Numeric, String, Text, text
from sqlalchemy.dialects.mysql import BIGINT, INTEGER
from sqlalchemy.dialects.mysql import JSON as MySQLJSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, BigIntPrimaryKeyMixin, TimestampMixin


class RouteSnapshot(BigIntPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "route_snapshots"
    __table_args__ = (
        Index("idx_route_snapshots_record", "record_id"),
        Index("idx_route_snapshots_record_created", "record_id", "created_at", "id"),
        Index("idx_route_snapshots_type_created", "route_type", "created_at"),
        Index("idx_route_snapshots_provider", "provider"),
        {"comment": "地图路线快照"},
    )

    record_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    provider: Mapped[str] = mapped_column(String(30), nullable=False, server_default=text("'amap'"))
    route_type: Mapped[str] = mapped_column(String(30), nullable=False)
    origin_location: Mapped[str | None] = mapped_column(String(64), nullable=True)
    destination_location: Mapped[str | None] = mapped_column(String(64), nullable=True)
    waypoints: Mapped[list[dict[str, Any]] | None] = mapped_column(MySQLJSON, nullable=True)
    distance_m: Mapped[int | None] = mapped_column(INTEGER(unsigned=True), nullable=True)
    duration_s: Mapped[int | None] = mapped_column(INTEGER(unsigned=True), nullable=True)
    request_params: Mapped[dict[str, Any]] = mapped_column(MySQLJSON, nullable=False)
    response_data: Mapped[dict[str, Any]] = mapped_column(MySQLJSON, nullable=False)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class RouteMapExport(BigIntPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "route_map_exports"
    __table_args__ = (
        Index("idx_route_map_exports_record", "record_id"),
        Index("idx_route_map_exports_record_created", "record_id", "created_at", "id"),
        Index("idx_route_map_exports_snapshot", "route_snapshot_id"),
        Index("idx_route_map_exports_status", "status"),
        {"comment": "路径图导出"},
    )

    record_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    route_snapshot_id: Mapped[int | None] = mapped_column(BIGINT(unsigned=True), nullable=True)
    export_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'pending'")
    )
    amap_route_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    storage_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    width: Mapped[int | None] = mapped_column(INTEGER(unsigned=True), nullable=True)
    height: Mapped[int | None] = mapped_column(INTEGER(unsigned=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)


class WeatherSnapshot(BigIntPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "weather_snapshots"
    __table_args__ = (
        Index("idx_weather_snapshots_record", "record_id"),
        Index("idx_weather_snapshots_record_created", "record_id", "created_at", "id"),
        Index("idx_weather_snapshots_city_date", "city_name", "weather_date"),
        Index("idx_weather_snapshots_alert", "alert_level"),
        {"comment": "天气快照"},
    )

    record_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    city_name: Mapped[str] = mapped_column(String(80), nullable=False)
    location: Mapped[str | None] = mapped_column(String(64), nullable=True)
    weather_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    weather_summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    alert_level: Mapped[str | None] = mapped_column(String(30), nullable=True)
    alerts: Mapped[list[dict[str, Any]] | None] = mapped_column(MySQLJSON, nullable=True)
    request_params: Mapped[dict[str, Any]] = mapped_column(MySQLJSON, nullable=False)
    response_data: Mapped[dict[str, Any]] = mapped_column(MySQLJSON, nullable=False)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class NewsSnapshot(BigIntPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "news_snapshots"
    __table_args__ = (
        Index("idx_news_snapshots_record", "record_id"),
        Index("idx_news_snapshots_record_created", "record_id", "created_at", "id"),
        Index("idx_news_snapshots_query_created", "query_text", "created_at"),
        Index("idx_news_snapshots_category", "category"),
        Index("idx_news_snapshots_provider_category", "provider", "category"),
        {"comment": "实时信息检索快照"},
    )

    record_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), nullable=False)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    query_text: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False, server_default=text("'news'"))
    item_count: Mapped[int] = mapped_column(
        INTEGER(unsigned=True), nullable=False, server_default=text("0")
    )
    top_titles: Mapped[list[str] | None] = mapped_column(MySQLJSON, nullable=True)
    source_sites: Mapped[list[str] | None] = mapped_column(MySQLJSON, nullable=True)
    credibility_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    response_data: Mapped[dict[str, Any]] = mapped_column(MySQLJSON, nullable=False)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
