from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Topic(Base):
    channel_id: Mapped[str] = mapped_column(String(64), index=True)
    column_id: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    subtitle: Mapped[str] = mapped_column(String(255), default="")
    keywords: Mapped[list] = mapped_column(JSON, default=list)
    audience: Mapped[str] = mapped_column(String(255), default="")
    angle: Mapped[str] = mapped_column(Text, default="")
    difficulty: Mapped[str] = mapped_column(String(32), default="beginner")
    expected_duration: Mapped[int] = mapped_column(Integer, default=60)
    recommended_platforms: Mapped[list] = mapped_column(JSON, default=list)
    generated_reason: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="generated", index=True)

    scripts: Mapped[list["Script"]] = relationship(back_populates="topic", lazy="selectin")


class Script(Base):
    topic_id: Mapped[str] = mapped_column(ForeignKey("topic.id"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    duration_type: Mapped[str] = mapped_column(String(32), default="60s")
    hook: Mapped[str] = mapped_column(Text, default="")
    body: Mapped[list] = mapped_column(JSON, default=list)
    ending: Mapped[str] = mapped_column(Text, default="")
    platform_title: Mapped[str] = mapped_column(String(255), default="")
    platform_description: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    risk_flags: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)

    topic: Mapped[Topic] = relationship(back_populates="scripts", lazy="selectin")
    versions: Mapped[list["ScriptVersion"]] = relationship(
        back_populates="script", cascade="all, delete-orphan", lazy="selectin"
    )
    storyboards: Mapped[list["Storyboard"]] = relationship(back_populates="script", lazy="selectin")


class ScriptVersion(Base):
    script_id: Mapped[str] = mapped_column(ForeignKey("script.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    change_reason: Mapped[str] = mapped_column(Text, default="")

    script: Mapped[Script] = relationship(back_populates="versions", lazy="selectin")


class Storyboard(Base):
    script_id: Mapped[str] = mapped_column(ForeignKey("script.id"), index=True)
    scene_index: Mapped[int] = mapped_column(Integer, index=True)
    duration_seconds: Mapped[float] = mapped_column(Float, default=6)
    voiceover: Mapped[str] = mapped_column(Text, default="")
    subtitle: Mapped[str] = mapped_column(Text, default="")
    visual_type: Mapped[str] = mapped_column(String(64), default="talking_head")
    visual_prompt: Mapped[str] = mapped_column(Text, default="")
    motion_hint: Mapped[str] = mapped_column(Text, default="")
    music_hint: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)

    script: Mapped[Script] = relationship(back_populates="storyboards", lazy="selectin")


class ReviewRecord(Base):
    target_type: Mapped[str] = mapped_column(String(64), index=True)
    target_id: Mapped[str] = mapped_column(String(64), index=True)
    action: Mapped[str] = mapped_column(String(64), index=True)
    reason: Mapped[str] = mapped_column(Text, default="")
    reviewer_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    before_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
