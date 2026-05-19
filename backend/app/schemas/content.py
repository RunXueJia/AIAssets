from pydantic import BaseModel, Field


class TopicCreate(BaseModel):
    channel_id: str
    column_id: str
    title: str
    subtitle: str = ""
    keywords: list[str] = Field(default_factory=list)
    audience: str = ""
    angle: str = ""
    difficulty: str = "beginner"
    expected_duration: int = 60
    recommended_platforms: list[str] = Field(default_factory=list)
    generated_reason: str = ""
    status: str = "generated"


class TopicUpdate(TopicCreate):
    id: str


class GenerateTopicsRequest(BaseModel):
    channel_id: str
    column_id: str
    count: int = 10
    keyword_seeds: list[str] = Field(default_factory=list)
    model_id: str
    prompt_template_id: str


class TopicActionRequest(BaseModel):
    id: str
    reason: str | None = None


class GenerateScriptRequest(BaseModel):
    topic_id: str
    model_id: str
    prompt_template_id: str
    duration_type: str = "60s"


class ScriptUpdate(BaseModel):
    id: str
    duration_type: str | None = None
    hook: str | None = None
    body: list[dict] | None = None
    ending: str | None = None
    platform_title: str | None = None
    platform_description: str | None = None
    tags: list[str] | None = None
    risk_flags: list[str] | None = None
    status: str | None = None
    change_reason: str = "manual_update"


class RegenerateScriptRequest(GenerateScriptRequest):
    script_id: str | None = None


class GenerateStoryboardRequest(BaseModel):
    script_id: str
    model_id: str
    prompt_template_id: str


class StoryboardUpdate(BaseModel):
    id: str
    scene_index: int | None = None
    duration_seconds: float | None = None
    voiceover: str | None = None
    subtitle: str | None = None
    visual_type: str | None = None
    visual_prompt: str | None = None
    motion_hint: str | None = None
    music_hint: str | None = None
    status: str | None = None


class ReviewRequest(BaseModel):
    target_type: str
    target_id: str
    comment: str | None = None
    reason: str | None = None
    changes: dict | None = None
