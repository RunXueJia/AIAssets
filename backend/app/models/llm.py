from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LLMProvider(Base):
    __tablename__ = "llm_provider"

    name: Mapped[str] = mapped_column(String(128), index=True)
    provider_type: Mapped[str] = mapped_column(String(64), default="openai_compatible")
    base_url: Mapped[str] = mapped_column(String(500))
    api_key_encrypted: Mapped[str] = mapped_column(Text, default="")
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=60)
    status: Mapped[str] = mapped_column(String(32), default="enabled", index=True)

    models: Mapped[list["LLMModel"]] = relationship(back_populates="provider", lazy="selectin")


class LLMModel(Base):
    __tablename__ = "llm_model"

    provider_id: Mapped[str] = mapped_column(ForeignKey("llm_provider.id"), index=True)
    model_name: Mapped[str] = mapped_column(String(128), index=True)
    display_name: Mapped[str] = mapped_column(String(128))
    usage_type: Mapped[str] = mapped_column(String(64), index=True)
    context_window: Mapped[int] = mapped_column(Integer, default=128000)
    max_output_tokens: Mapped[int] = mapped_column(Integer, default=4096)
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    input_token_price: Mapped[float] = mapped_column(Float, default=0.0)
    output_token_price: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="enabled", index=True)

    provider: Mapped[LLMProvider] = relationship(back_populates="models", lazy="selectin")


class PromptTemplate(Base):
    scene: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    name: Mapped[str] = mapped_column(String(128), index=True)
    system_prompt: Mapped[str] = mapped_column(Text)
    user_prompt: Mapped[str] = mapped_column(Text)
    variables: Mapped[list] = mapped_column(JSON, default=list)
    output_schema: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)


class LLMCallLog(Base):
    __tablename__ = "llm_call_log"

    task_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    target_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    target_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    scene: Mapped[str] = mapped_column(String(64), index=True)
    provider_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    model_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    prompt_template_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    prompt_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    request_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    stream_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    first_token_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_output: Mapped[str] = mapped_column(Text, default="")
    parsed_output: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    chunks: Mapped[list["LLMStreamChunk"]] = relationship(
        back_populates="call_log", cascade="all, delete-orphan", lazy="selectin"
    )


class LLMStreamChunk(Base):
    __tablename__ = "llm_stream_chunk"

    call_log_id: Mapped[str] = mapped_column(ForeignKey("llm_call_log.id"), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    chunk_json: Mapped[dict] = mapped_column(JSON, default=dict)
    delta_content: Mapped[str] = mapped_column(Text, default="")
    finish_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)

    call_log: Mapped[LLMCallLog] = relationship(back_populates="chunks", lazy="selectin")
