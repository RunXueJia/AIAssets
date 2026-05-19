from pydantic import BaseModel, Field

from app.schemas.common import TimestampMixin


class ContentChannelCreate(BaseModel):
    name: str
    description: str = ""
    target_audience: str = ""
    tone: str = ""
    forbidden_topics: list[str] = Field(default_factory=list)
    daily_topic_quota: int = 50
    reviewer_ids: list[str] = Field(default_factory=list)
    default_video_template_id: str | None = None
    default_article_template_id: str | None = None


class ContentChannelUpdate(ContentChannelCreate):
    id: str
    status: str | None = None


class ContentChannelOut(TimestampMixin, ContentChannelCreate):
    status: str


class ColumnCreate(BaseModel):
    channel_id: str
    name: str
    description: str = ""
    target_audience: str = ""
    topic_quota: int = 10
    default_video_template_id: str | None = None
    default_article_template_id: str | None = None


class ColumnUpdate(ColumnCreate):
    id: str
    status: str | None = None


class ColumnOut(TimestampMixin, ColumnCreate):
    status: str


class VideoTemplateCreate(BaseModel):
    name: str
    template_type: str = "html"
    ratio: str = "9:16"
    resolution: str = "1080x1920"
    template_path: str = ""
    status: str = "enabled"


class VideoTemplateUpdate(VideoTemplateCreate):
    id: str


class ArticleTemplateCreate(BaseModel):
    name: str
    layout: str = "default"
    seo_defaults: dict = Field(default_factory=dict)
    status: str = "enabled"


class ArticleTemplateUpdate(ArticleTemplateCreate):
    id: str


class PlatformUpdate(BaseModel):
    id: str | None = None
    platform_name: str
    title_limit: int = 60
    tag_limit: int = 10
    description_limit: int = 500
    status: str = "enabled"
