from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class VideoAsset(Base):
    script_id: Mapped[str] = mapped_column(String(64), index=True)
    template_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    file_url: Mapped[str] = mapped_column(String(500), default="")
    cover_url: Mapped[str] = mapped_column(String(500), default="")
    resolution: Mapped[str] = mapped_column(String(32), default="")
    duration_seconds: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(32), default="waiting", index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)


class KnowledgeCard(Base):
    script_id: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255), default="")
    content: Mapped[dict] = mapped_column(JSON, default=dict)
    image_url: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)


class DownloadAsset(Base):
    title: Mapped[str] = mapped_column(String(255), index=True)
    asset_type: Mapped[str] = mapped_column(String(64), default="markdown")
    source_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    file_url: Mapped[str] = mapped_column(String(500), default="")
    content: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)


class ArticlePage(Base):
    topic_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    video_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    body: Mapped[str] = mapped_column(Text, default="")
    seo_title: Mapped[str] = mapped_column(String(255), default="")
    seo_description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    published_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PublishRecord(Base):
    content_id: Mapped[str] = mapped_column(String(64), index=True)
    platform: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending_publish", index=True)
    platform_url: Mapped[str] = mapped_column(String(500), default="")
    package_url: Mapped[str] = mapped_column(String(500), default="")
    operator_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    published_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Lead(Base):
    name: Mapped[str] = mapped_column(String(128))
    contact: Mapped[str] = mapped_column(String(255), index=True)
    company: Mapped[str] = mapped_column(String(255), default="")
    role: Mapped[str] = mapped_column(String(128), default="")
    need_type: Mapped[str] = mapped_column(String(64), default="")
    source_page: Mapped[str] = mapped_column(String(500), default="")
    source_asset_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    consent: Mapped[bool] = mapped_column(Boolean, default=False)


class PublicEvent(Base):
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    source_page: Mapped[str] = mapped_column(String(500), default="")
    target_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    referrer: Mapped[str] = mapped_column(String(500), default="")
    utm_source: Mapped[str] = mapped_column(String(128), default="")
