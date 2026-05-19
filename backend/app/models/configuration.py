from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ContentChannel(Base):
    name: Mapped[str] = mapped_column(String(128), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    target_audience: Mapped[str] = mapped_column(Text, default="")
    tone: Mapped[str] = mapped_column(String(255), default="")
    forbidden_topics: Mapped[list] = mapped_column(JSON, default=list)
    daily_topic_quota: Mapped[int] = mapped_column(Integer, default=50)
    reviewer_ids: Mapped[list] = mapped_column(JSON, default=list)
    default_video_template_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    default_article_template_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="enabled", index=True)

    columns: Mapped[list["Column"]] = relationship(back_populates="channel", lazy="selectin")


class Column(Base):
    __tablename__ = "content_column"

    channel_id: Mapped[str] = mapped_column(ForeignKey("content_channel.id"), index=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    target_audience: Mapped[str] = mapped_column(Text, default="")
    topic_quota: Mapped[int] = mapped_column(Integer, default=10)
    default_video_template_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    default_article_template_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="enabled", index=True)

    channel: Mapped[ContentChannel] = relationship(back_populates="columns", lazy="selectin")


class VideoTemplate(Base):
    name: Mapped[str] = mapped_column(String(128), index=True)
    template_type: Mapped[str] = mapped_column(String(64), default="html")
    ratio: Mapped[str] = mapped_column(String(32), default="9:16")
    resolution: Mapped[str] = mapped_column(String(32), default="1080x1920")
    template_path: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[str] = mapped_column(String(32), default="enabled", index=True)


class ArticleTemplate(Base):
    name: Mapped[str] = mapped_column(String(128), index=True)
    layout: Mapped[str] = mapped_column(String(64), default="default")
    seo_defaults: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="enabled", index=True)


class PlatformConfig(Base):
    platform_name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title_limit: Mapped[int] = mapped_column(Integer, default=60)
    tag_limit: Mapped[int] = mapped_column(Integer, default=10)
    description_limit: Mapped[int] = mapped_column(Integer, default=500)
    status: Mapped[str] = mapped_column(String(32), default="enabled", index=True)
