from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.configuration import Column, ContentChannel
from app.models.content import Script, Topic
from app.models.llm import LLMModel, PromptTemplate
from app.repositories.base import BaseRepository


async def topic_variables(
    db: AsyncSession, channel_id: str, column_id: str, count: int, keyword_seeds: list[str]
) -> dict:
    channel = await BaseRepository(ContentChannel).get(db, channel_id)
    column = await BaseRepository(Column).get(db, column_id)
    if not channel or not column:
        raise NotFoundError("内容方向或栏目不存在")
    return {
        "channel_name": channel.name,
        "column_name": column.name,
        "count": count,
        "target_audience": column.target_audience or channel.target_audience,
        "forbidden_topics": channel.forbidden_topics,
        "keyword_seeds": keyword_seeds,
    }


async def script_variables(db: AsyncSession, topic_id: str, duration_type: str) -> dict:
    topic = await BaseRepository(Topic).get(db, topic_id)
    if not topic:
        raise NotFoundError("选题不存在")
    return {
        "topic_title": topic.title,
        "topic_subtitle": topic.subtitle,
        "keywords": topic.keywords,
        "audience": topic.audience,
        "angle": topic.angle,
        "duration_type": duration_type,
    }


async def storyboard_variables(db: AsyncSession, script_id: str) -> dict:
    script = await BaseRepository(Script).get(db, script_id)
    if not script:
        raise NotFoundError("脚本不存在")
    return {
        "hook": script.hook,
        "body": script.body,
        "ending": script.ending,
        "duration_type": script.duration_type,
    }


async def require_model_template(
    db: AsyncSession, model_id: str, prompt_template_id: str
) -> tuple[LLMModel, PromptTemplate]:
    model = await BaseRepository(LLMModel).get(db, model_id)
    template = await BaseRepository(PromptTemplate).get(db, prompt_template_id)
    if not model or not template:
        raise NotFoundError("模型或 Prompt 模板不存在")
    return model, template
