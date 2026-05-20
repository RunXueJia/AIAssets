#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 09:56
# @File     : generation_service.py
# @Desc     : Generation task orchestration service.

import hashlib
from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.constants import (
    CONTENT_PENDING_REVIEW,
    SOURCE_UNCERTAIN,
    SOURCE_USABLE,
    STAGE_COMPLETED,
    STAGE_FETCH_SOURCES,
    STAGE_GENERATE_SCRIPT,
    STAGE_GENERATE_STORYBOARD,
    STAGE_GENERATE_SUBTITLE,
    STAGE_GENERATE_TOPICS,
    STAGE_NAMES,
    STAGE_SUMMARIZE_SOURCES,
    TASK_CANCELLED,
    TASK_PENDING,
    TASK_RETRYING,
    TASK_RUNNING,
    TASK_SUCCESS,
)
from app.core.config import settings
from app.core.exceptions import AppError
from app.models.entities import (
    ContentVersion,
    GenerationTask,
    Script,
    SourceItem,
    SourceSummary,
    Storyboard,
    Subtitle,
    TaskLog,
    Topic,
)
from app.schemas.generation import (
    CreateGenerationTaskRequest,
    StoryboardItemRequest,
    SubtitleItemRequest,
    UpdateScriptRequest,
)
from app.services.fetch_service import FetchedSource, fetch_public_sources
from app.services.llm_service import build_generation_prompt, chat_json
from app.services.log_service import create_task_log
from app.services.serializers import (
    script_to_dict,
    source_item_to_dict,
    source_summary_to_dict,
    storyboard_to_dict,
    subtitle_to_dict,
    task_to_dict,
    topic_to_dict,
)
from app.utils.id import new_id
from app.utils.time import format_dt


def create_generation_task(db: Session, payload: CreateGenerationTaskRequest, user_id: str | None) -> GenerationTask:
    task = GenerationTask(
        id=new_id("task"),
        direction=payload.direction,
        topic=payload.topic,
        audience=payload.audience,
        count=payload.count,
        column_code=payload.column,
        generation_type=payload.generation_type,
        start_mode=payload.start_mode,
        status=TASK_PENDING if payload.start_mode == "draft" else TASK_RUNNING,
        current_stage="create_task",
        progress=0,
        input_payload_json=payload.model_dump(),
        created_by=user_id,
        updated_by=user_id,
        started_at=datetime.now() if payload.start_mode != "draft" else None,
    )
    db.add(task)
    create_task_log(
        db,
        task_type="generation",
        task_id=task.id,
        generation_task_id=task.id,
        event_type="start",
        stage="create_task",
        message="生成任务已创建",
        detail={"task_id": task.id, "status": task.status},
    )
    db.flush()
    if payload.start_mode != "draft":
        if settings.enable_celery_tasks:
            from app.tasks.generation_tasks import run_generation_task

            db.commit()
            run_generation_task.delay(task.id)
            db.refresh(task)
            return task
        else:
            run_generation_pipeline(db, task)
    db.commit()
    db.refresh(task)
    return task


def run_generation_pipeline(db: Session, task: GenerationTask) -> None:
    summary = _build_sources_and_summary(db, task)
    topics = _generate_topics(db, task, summary)
    if task.generation_type == "topics_only":
        _finish_task(db, task, summary, topics[0] if topics else None, None)
        return
    script = _generate_script(db, task, topics[0], summary)
    if task.generation_type == "topics_and_script":
        _finish_task(db, task, summary, topics[0], script)
        return
    _generate_storyboard_and_subtitles(db, task, script)
    _finish_task(db, task, summary, topics[0], script)


def _stage(db: Session, task: GenerationTask, stage: str, progress: int, message: str, detail: dict | None = None) -> None:
    task.current_stage = stage
    task.progress = progress
    create_task_log(
        db,
        task_type="generation",
        task_id=task.id,
        generation_task_id=task.id,
        event_type="stage",
        stage=stage,
        message=message,
        detail={"stage_name": STAGE_NAMES.get(stage, stage), "progress": progress, **(detail or {})},
    )


def _build_sources_and_summary(db: Session, task: GenerationTask) -> SourceSummary:
    _stage(db, task, STAGE_FETCH_SOURCES, 20, "正在抓取相关内容")
    base_topic = task.topic or task.direction
    fetched_sources = fetch_public_sources(task.direction, task.topic, task.audience)
    if not fetched_sources:
        fetched_sources = _fallback_sources(task)
    sources: list[SourceItem] = []
    for index, fetched in enumerate(fetched_sources, start=1):
        item = SourceItem(
            id=new_id("src"),
            generation_task_id=task.id,
            source_hash=fetched.source_hash,
            title=fetched.title,
            site_name=fetched.site_name,
            url=fetched.url,
            author="公开资料",
            published_at=fetched.published_at,
            summary_text=fetched.summary_text,
            relevance_reason=fetched.relevance_reason,
            key_points_json=fetched.key_points,
            raw_content_text=fetched.raw_content,
            status=fetched.status,
            need_human_confirm=fetched.need_human_confirm,
            fetch_status=fetched.fetch_status,
            fetch_error_message=fetched.fetch_error_message,
            source_order=index,
        )
        db.add(item)
        sources.append(item)
        create_task_log(
            db,
            task_type="generation",
            task_id=task.id,
            generation_task_id=task.id,
            event_type="source",
            stage=STAGE_FETCH_SOURCES,
            message=f"发现来源：{fetched.title}",
            detail=source_item_to_dict(item),
        )
    db.flush()

    _stage(db, task, STAGE_SUMMARIZE_SOURCES, 35, "正在整理素材汇总")
    usable_count = sum(1 for item in sources if item.fetch_status == "success" and item.status == SOURCE_USABLE)
    fallback_summary = _fallback_generation_payload(task, base_topic, sources)
    llm_payload, model_name, raw_output = chat_json(
        db,
        build_generation_prompt(task.input_payload_json or {}, fallback_summary["summary"], [item.title for item in sources]),
        fallback_summary,
    )
    summary = SourceSummary(
        id=new_id("sum"),
        summary_type="generation",
        generation_task_id=task.id,
        title=f"{base_topic}素材汇总",
        summary_text=str(llm_payload.get("summary") or fallback_summary["summary"]),
        key_points_json=llm_payload.get("key_points") or fallback_summary["key_points"],
        risk_notes_json=llm_payload.get("risk_notes") or fallback_summary["risk_notes"],
        source_count=len(sources),
        usable_source_count=usable_count,
        need_human_confirm=any(item.need_human_confirm for item in sources),
        llm_model_name=model_name,
        llm_raw_output=raw_output,
        created_by=task.created_by,
    )
    summary._llm_payload = llm_payload
    db.add(summary)
    db.flush()
    for item in sources:
        item.source_summary_id = summary.id
    task.source_summary_id = summary.id
    create_task_log(
        db,
        task_type="generation",
        task_id=task.id,
        generation_task_id=task.id,
        event_type="result",
        stage=STAGE_SUMMARIZE_SOURCES,
        message="素材汇总已生成",
        detail={"type": "source_summary", "content_id": summary.id},
    )
    return summary


def _generate_topics(db: Session, task: GenerationTask, summary: SourceSummary) -> list[Topic]:
    _stage(db, task, STAGE_GENERATE_TOPICS, 55, "正在生成选题")
    base_topic = task.topic or task.direction
    audience = task.audience or "普通职场人"
    llm_payload = getattr(summary, "_llm_payload", None) or _fallback_generation_payload(task, base_topic, [])
    topic_payloads = llm_payload.get("topics") or []
    if len(topic_payloads) < 10:
        topic_payloads = _fallback_generation_payload(task, base_topic, [])["topics"]
    topics = []
    for index, topic_payload in enumerate(topic_payloads[: max(10, task.count)], start=1):
        title = str(topic_payload.get("title") or f"{base_topic}候选选题 {index}")
        topic = Topic(
            id=new_id("topic"),
            generation_task_id=task.id,
            source_summary_id=summary.id,
            title=title,
            audience=topic_payload.get("audience") or audience,
            angle=topic_payload.get("angle") or "把公开素材整理成适合 60 秒短视频表达的具体方法。",
            recommended_column=topic_payload.get("recommended_column") or ("一分钟 AI 办公" if index % 2 else "今天少加班一小时"),
            duration_seconds=int(topic_payload.get("duration_seconds") or 60),
            keywords_json=topic_payload.get("keywords") or ["AI办公", "职场效率", base_topic],
            reason=topic_payload.get("reason") or "主题具体，适合以步骤演示形式制作短视频。",
            score=float(topic_payload.get("score") or round(9.5 - index * 0.2, 2)),
            status="draft",
            need_human_confirm=bool(topic_payload.get("need_human_confirm", index in {5, 8})),
        )
        db.add(topic)
        topics.append(topic)
    db.flush()
    create_task_log(
        db,
        task_type="generation",
        task_id=task.id,
        generation_task_id=task.id,
        event_type="result",
        stage=STAGE_GENERATE_TOPICS,
        message="候选选题已生成",
        detail={"type": "topics", "count": len(topics), "first_topic_id": topics[0].id},
    )
    return topics


def _generate_script(db: Session, task: GenerationTask, topic: Topic, summary: SourceSummary) -> Script:
    _stage(db, task, STAGE_GENERATE_SCRIPT, 75, "正在生成脚本")
    base_topic = task.topic or task.direction
    llm_payload = getattr(summary, "_llm_payload", None) or _fallback_generation_payload(task, base_topic, [])
    script_payload = llm_payload.get("script") or _fallback_generation_payload(task, base_topic, [])["script"]
    delta_texts = script_payload.get("deltas") or ["开头用职场痛点快速进入主题。", "中段给出可执行步骤并强调人工校对。", "结尾提示风险边界和下一步动作。"]
    for text in delta_texts:
        create_task_log(
            db,
            task_type="generation",
            task_id=task.id,
            generation_task_id=task.id,
            event_type="delta",
            stage=STAGE_GENERATE_SCRIPT,
            message=text,
            detail={"text": text},
        )
    script = Script(
        id=new_id("script"),
        topic_id=topic.id,
        generation_task_id=task.id,
        source_summary_id=summary.id,
        title=str(script_payload.get("title") or topic.title),
        hook=script_payload.get("hook") or "周五最痛苦的事，是发现内容还没整理成能交付的版本。",
        pain_point=script_payload.get("pain_point") or "很多人不是不会用 AI，而是直接丢一句话就等结果，最后还要返工。",
        method=script_payload.get("method") or "先用 AI 整理素材，再让它按固定结构生成脚本，最后由人工确认事实。",
        steps_json=script_payload.get("steps") or ["粘贴素材和目标受众", "要求 AI 输出痛点、步骤和示例", "检查事实、数字和夸张表达"],
        example_text=script_payload.get("example") or "把会议纪要、待办记录和公开资料放在一起，让 AI 输出一版 60 秒讲解脚本。",
        summary_text=script_payload.get("summary") or "AI 负责整理和起草，人负责判断和把关。",
        cta_text=script_payload.get("cta") or "下次生成内容前，先让 AI 整理素材清单。",
        platform_title=script_payload.get("platform_title") or topic.title[:80],
        description=script_payload.get("description") or "一个适合职场效率内容的 AI 素材整理和脚本生成方法。",
        tags_json=script_payload.get("tags") or ["AI办公", "职场效率", "内容生产"],
        cover_text=script_payload.get("cover_text") or "AI 提效流程",
        pinned_comment=script_payload.get("pinned_comment") or "先整理素材，再生成脚本，最后人工确认事实。",
        status=CONTENT_PENDING_REVIEW,
        current_version_no=1,
        need_human_confirm=bool(script_payload.get("need_human_confirm", True)),
        risk_notes_json=script_payload.get("risk_notes") or ["效率提升需结合实际工作量，不应承诺固定节省时间。"],
    )
    db.add(script)
    db.flush()
    create_task_log(
        db,
        task_type="generation",
        task_id=task.id,
        generation_task_id=task.id,
        event_type="result",
        stage=STAGE_GENERATE_SCRIPT,
        message="脚本已生成",
        related_content_type="script",
        related_content_id=script.id,
        detail={"type": "script", "content_id": script.id},
    )
    return script


def _generate_storyboard_and_subtitles(db: Session, task: GenerationTask, script: Script) -> None:
    _stage(db, task, STAGE_GENERATE_STORYBOARD, 88, "正在生成分镜")
    task_summary = db.get(SourceSummary, script.source_summary_id) if script.source_summary_id else None
    base_topic = task.topic or task.direction
    llm_payload = getattr(task_summary, "_llm_payload", None) or _fallback_generation_payload(task, base_topic, [])
    shots = llm_payload.get("storyboards") or _fallback_generation_payload(task, base_topic, [])["storyboards"]
    start_ms = 0
    for index, shot in enumerate(shots[:10], start=1):
        duration = int(shot.get("duration_seconds") or 10)
        voiceover = str(shot.get("voiceover") or "AI 负责起草，人负责判断。")
        storyboard = Storyboard(
            id=new_id("shot"),
            script_id=script.id,
            shot_no=index,
            duration_seconds=duration,
            voiceover=voiceover,
            subtitle=str(shot.get("subtitle") or voiceover[:28]),
            visual_type=str(shot.get("visual_type") or "screen_recording"),
            material_suggestion=shot.get("material_suggestion") or "展示素材列表变成结构化大纲",
            motion_suggestion=shot.get("motion_suggestion") or "使用轻量滑入和重点标注动效",
            scene_note=shot.get("scene_note") or "默认竖屏 9:16",
            status="draft",
        )
        db.add(storyboard)
        subtitle = Subtitle(
            id=new_id("sub"),
            script_id=script.id,
            line_no=index,
            start_time_ms=start_ms,
            end_time_ms=start_ms + duration * 1000,
            text=str(shot.get("subtitle") or voiceover),
            speaker="旁白",
            style_name="default",
            status="draft",
        )
        db.add(subtitle)
        start_ms += duration * 1000
    _stage(db, task, STAGE_GENERATE_SUBTITLE, 95, "正在生成字幕")
    create_task_log(
        db,
        task_type="generation",
        task_id=task.id,
        generation_task_id=task.id,
        event_type="result",
        stage=STAGE_GENERATE_STORYBOARD,
        message="分镜和字幕已生成",
        related_content_type="script",
        related_content_id=script.id,
        detail={"type": "storyboard_subtitle", "content_id": script.id, "storyboard_count": len(shots)},
    )


def _fallback_sources(task: GenerationTask) -> list[FetchedSource]:
    base_topic = task.topic or task.direction
    source_titles = [
        f"{base_topic}的实操方法与常见误区",
        f"{task.direction}在职场效率场景中的应用案例",
        f"{base_topic}如何整理资料并输出可执行步骤",
        "用 AI 处理重复办公任务的流程建议",
        "AI 工具辅助内容生产时的人工校对要点",
    ]
    sources = []
    for index, title in enumerate(source_titles, start=1):
        url = f"https://example.com/ai-growth/{hashlib.sha1(title.encode('utf-8')).hexdigest()[:10]}"
        sources.append(
            FetchedSource(
                title=title,
                site_name="示例公开来源",
                url=url,
                published_at=None,
                summary_text=f"围绕“{base_topic}”整理出适合短视频脚本使用的公开信息和操作建议。",
                relevance_reason=f"与“{base_topic}”主题相关，可支撑选题和脚本生成。",
                key_points=["先整理素材", "再生成结构", "最后人工确认事实"],
                raw_content=f"{title}\n本地回退素材，可替换为真实抓取正文。",
                status=SOURCE_USABLE if index < 5 else SOURCE_UNCERTAIN,
                need_human_confirm=index == 5,
            )
        )
    return sources


def _fallback_generation_payload(task: GenerationTask, base_topic: str, sources: list[SourceItem]) -> dict:
    audience = task.audience or "普通职场人"
    source_titles = [item.title for item in sources] or [base_topic]
    topic_titles = [
        f"用 AI 10 分钟完成{base_topic}",
        f"{base_topic}前先让 AI 帮你整理思路",
        f"一个适合{audience}的 AI 办公流程",
        "别直接让 AI 代写，先做这 3 步",
        "把零散资料变成清晰输出的 AI 方法",
        "AI 写作结果不稳定？先给它这份素材",
        f"{base_topic}的 60 秒实操演示",
        "普通人用 AI 提效时最该避开的坑",
        "让 AI 帮你拆任务，而不是替你做判断",
        "从素材到脚本：AI 内容生成的安全流程",
    ]
    return {
        "summary": f"本次素材围绕“{base_topic}”，来源包括：{'、'.join(source_titles[:3])}。生成内容需要避免夸大承诺，并标记不确定事实供编辑审核。",
        "key_points": ["AI 适合整理资料和生成结构", "事实和数据仍需人工确认", "短视频应给出明确可执行步骤"],
        "risk_notes": ["不要承诺完全替代人工判断", "涉及效率提升时避免夸张收益表达"],
        "topics": [
            {
                "title": title,
                "audience": audience,
                "angle": "把公开素材整理成适合 60 秒短视频表达的具体方法。",
                "recommended_column": "一分钟 AI 办公" if index % 2 else "今天少加班一小时",
                "duration_seconds": 60,
                "keywords": ["AI办公", "职场效率", base_topic],
                "reason": "主题具体，适合以步骤演示形式制作短视频。",
                "score": round(9.5 - index * 0.2, 2),
                "need_human_confirm": index in {5, 8},
            }
            for index, title in enumerate(topic_titles, start=1)
        ],
        "script": {
            "title": f"{base_topic}的 AI 提效流程",
            "hook": "周五最痛苦的事，是发现内容还没整理成能交付的版本。",
            "pain_point": "很多人不是不会用 AI，而是直接丢一句话就等结果，最后还要返工。",
            "method": "先用 AI 整理素材，再让它按固定结构生成脚本，最后由人工确认事实。",
            "steps": ["粘贴素材和目标受众", "要求 AI 输出痛点、步骤和示例", "检查事实、数字和夸张表达"],
            "example": "把会议纪要、待办记录和公开资料放在一起，让 AI 输出一版 60 秒讲解脚本。",
            "summary": "AI 负责整理和起草，人负责判断和把关。",
            "cta": "下次生成内容前，先让 AI 整理素材清单。",
            "platform_title": f"{base_topic}AI提效方法",
            "description": "一个适合职场效率内容的 AI 素材整理和脚本生成方法。",
            "tags": ["AI办公", "职场效率", "内容生产"],
            "cover_text": "AI 提效流程",
            "pinned_comment": "先整理素材，再生成脚本，最后人工确认事实。",
            "risk_notes": ["效率提升需结合实际工作量，不应承诺固定节省时间。"],
            "deltas": ["开头用职场痛点快速进入主题。", "中段给出可执行步骤并强调人工校对。", "结尾提示风险边界和下一步动作。"],
        },
        "storyboards": [
            {
                "duration_seconds": 10,
                "voiceover": voiceover,
                "subtitle": voiceover[:28],
                "visual_type": visual_type,
                "material_suggestion": material,
                "motion_suggestion": "使用轻量滑入和重点标注动效",
            }
            for visual_type, voiceover, material in [
                ("痛点开场", "周五最痛苦的事，是发现内容还没整理好。", "空白文档与零散资料快速切换"),
                ("方法总览", "别直接让 AI 代写，先让它整理素材。", "展示素材列表变成结构化大纲"),
                ("步骤一", "第一步，贴入素材和目标受众。", "屏幕录制输入素材"),
                ("步骤二", "第二步，让 AI 输出痛点、步骤和示例。", "大纲逐条出现"),
                ("步骤三", "第三步，人工检查事实和夸张表达。", "风险提示标记"),
                ("总结", "AI 负责起草，人负责判断。", "脚本、分镜、字幕合并为发布包"),
            ]
        ],
    }


def _finish_task(db: Session, task: GenerationTask, summary: SourceSummary, topic: Topic | None, script: Script | None) -> None:
    task.status = TASK_SUCCESS
    task.current_stage = STAGE_COMPLETED
    task.progress = 100
    task.source_summary_id = summary.id
    task.selected_topic_id = topic.id if topic else None
    task.final_script_id = script.id if script else None
    task.finished_at = datetime.now()
    task.result_payload_json = {
        "source_summary_id": summary.id,
        "selected_topic_id": topic.id if topic else None,
        "final_script_id": script.id if script else None,
    }
    create_task_log(
        db,
        task_type="generation",
        task_id=task.id,
        generation_task_id=task.id,
        event_type="done",
        stage=STAGE_COMPLETED,
        message="生成完成",
        detail={"task_id": task.id, "status": task.status, "content_id": script.id if script else None},
    )


def list_tasks(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    keyword: str | None = None,
) -> tuple[list[dict], int]:
    query = db.query(GenerationTask).filter(GenerationTask.deleted_at.is_(None))
    if status:
        query = query.filter(GenerationTask.status == status)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(or_(GenerationTask.direction.like(like), GenerationTask.topic.like(like)))
    total = query.count()
    items = query.order_by(GenerationTask.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return [task_to_dict(item) for item in items], total


def get_task_detail(db: Session, task_id: str) -> dict:
    task = db.get(GenerationTask, task_id)
    if task is None or task.deleted_at is not None:
        raise AppError(40400, "生成任务不存在", 404)
    logs = (
        db.query(TaskLog)
        .filter(TaskLog.generation_task_id == task.id)
        .order_by(TaskLog.created_at.asc())
        .limit(100)
        .all()
    )
    data = task_to_dict(task)
    data["logs"] = [
        {
            "stage": item.stage,
            "event_type": item.event_type,
            "message": item.message,
            "level": item.level,
            "created_at": format_dt(item.created_at),
        }
        for item in logs
    ]
    data["source_count"] = db.query(SourceItem).filter(SourceItem.generation_task_id == task.id).count()
    data["topic_count"] = db.query(Topic).filter(Topic.generation_task_id == task.id).count()
    data["script_count"] = db.query(Script).filter(Script.generation_task_id == task.id).count()
    return data


def cancel_task(db: Session, task_id: str, user_id: str | None) -> dict:
    task = db.get(GenerationTask, task_id)
    if task is None or task.deleted_at is not None:
        raise AppError(40400, "生成任务不存在", 404)
    if task.status == TASK_SUCCESS:
        raise AppError(40900, "任务已完成，不能取消", 409)
    task.status = TASK_CANCELLED
    task.updated_by = user_id
    create_task_log(
        db,
        task_type="generation",
        task_id=task.id,
        generation_task_id=task.id,
        event_type="done",
        stage=task.current_stage,
        message="任务已取消",
        detail={"task_id": task.id, "status": task.status},
    )
    db.commit()
    return {"task_id": task.id, "status": task.status}


def retry_task(db: Session, task_id: str, retry_from_stage: str | None, user_id: str | None) -> dict:
    task = db.get(GenerationTask, task_id)
    if task is None or task.deleted_at is not None:
        raise AppError(40400, "生成任务不存在", 404)
    task.status = TASK_RETRYING
    task.retry_count += 1
    task.updated_by = user_id
    task.current_stage = retry_from_stage or STAGE_FETCH_SOURCES
    create_task_log(
        db,
        task_type="generation",
        task_id=task.id,
        generation_task_id=task.id,
        event_type="stage",
        stage=task.current_stage,
        message="任务已进入重新生成",
        detail={"task_id": task.id, "status": task.status, "retry_from_stage": retry_from_stage},
    )
    task.status = TASK_RUNNING
    if settings.enable_celery_tasks:
        db.commit()
        from app.tasks.generation_tasks import run_generation_task

        run_generation_task.delay(task.id)
        return {"task_id": task.id, "status": task.status, "stream_url": f"/api/v1/generation/stream/{task.id}"}
    run_generation_pipeline(db, task)
    db.commit()
    return {"task_id": task.id, "status": task.status, "stream_url": f"/api/v1/generation/stream/{task.id}"}


def get_sse_logs(db: Session, task_id: str) -> list[TaskLog]:
    task = db.get(GenerationTask, task_id)
    if task is None or task.deleted_at is not None:
        raise AppError(40400, "生成任务不存在", 404)
    return (
        db.query(TaskLog)
        .filter(TaskLog.generation_task_id == task_id)
        .order_by(TaskLog.created_at.asc(), TaskLog.id.asc())
        .all()
    )


def list_sources(
    db: Session,
    task_id: str | None = None,
    summary_id: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[dict], int]:
    query = db.query(SourceItem)
    if task_id:
        query = query.filter(SourceItem.generation_task_id == task_id)
    if summary_id:
        query = query.filter(SourceItem.source_summary_id == summary_id)
    if status:
        query = query.filter(SourceItem.status == status)
    total = query.count()
    items = query.order_by(SourceItem.source_order.asc(), SourceItem.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return [source_item_to_dict(item) for item in items], total


def get_summary_detail(db: Session, summary_id: str) -> dict:
    item = db.get(SourceSummary, summary_id)
    if item is None:
        raise AppError(40400, "素材汇总不存在", 404)
    data = source_summary_to_dict(item)
    data["source_items"] = [
        source_item_to_dict(source)
        for source in db.query(SourceItem).filter(SourceItem.source_summary_id == summary_id).all()
    ]
    return data


def mark_source_status(db: Session, source_id: str, status: str, reason: str | None) -> dict:
    item = db.get(SourceItem, source_id)
    if item is None:
        raise AppError(40400, "来源素材不存在", 404)
    item.status = status
    if reason:
        item.fetch_error_message = reason
    db.commit()
    return {"source_id": item.id, "status": item.status}


def list_topics(
    db: Session,
    task_id: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[dict], int]:
    query = db.query(Topic)
    if task_id:
        query = query.filter(Topic.generation_task_id == task_id)
    if status:
        query = query.filter(Topic.status == status)
    if keyword:
        query = query.filter(Topic.title.like(f"%{keyword}%"))
    total = query.count()
    items = query.order_by(Topic.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return [topic_to_dict(item) for item in items], total


def get_topic_detail(db: Session, topic_id: str) -> dict:
    item = db.get(Topic, topic_id)
    if item is None:
        raise AppError(40400, "选题不存在", 404)
    data = topic_to_dict(item)
    if item.source_summary_id:
        data["source_items"] = [
            source_item_to_dict(source)
            for source in db.query(SourceItem).filter(SourceItem.source_summary_id == item.source_summary_id).limit(20).all()
        ]
    else:
        data["source_items"] = []
    return data


def change_topic_status(db: Session, topic_id: str, status: str, reason: str | None, user_id: str | None) -> dict:
    item = db.get(Topic, topic_id)
    if item is None:
        raise AppError(40400, "选题不存在", 404)
    item.status = status
    if status == "rejected":
        item.reject_reason = reason
    if status == "approved":
        item.approved_by = user_id
        item.approved_at = datetime.now()
    db.commit()
    return {"topic_id": item.id, "status": item.status}


def generate_script_from_topic(db: Session, topic_id: str, user_id: str | None) -> dict:
    topic = db.get(Topic, topic_id)
    if topic is None:
        raise AppError(40400, "选题不存在", 404)
    task = db.get(GenerationTask, topic.generation_task_id)
    if task is None:
        raise AppError(40400, "生成任务不存在", 404)
    summary = db.get(SourceSummary, topic.source_summary_id) if topic.source_summary_id else None
    if summary is None:
        raise AppError(40900, "缺少素材汇总，不能生成脚本", 409)
    task.status = TASK_RUNNING
    task.updated_by = user_id
    script = _generate_script(db, task, topic, summary)
    _generate_storyboard_and_subtitles(db, task, script)
    _finish_task(db, task, summary, topic, script)
    db.commit()
    return {"script_id": script.id, "status": script.status, "stream_url": f"/api/v1/generation/stream/{task.id}"}


def get_script_detail(db: Session, script_id: str) -> dict:
    script = db.get(Script, script_id)
    if script is None:
        raise AppError(40400, "脚本不存在", 404)
    data = script_to_dict(script)
    data["storyboards"] = [
        storyboard_to_dict(item)
        for item in db.query(Storyboard).filter(Storyboard.script_id == script.id).order_by(Storyboard.shot_no.asc()).all()
    ]
    data["subtitles"] = [
        subtitle_to_dict(item)
        for item in db.query(Subtitle).filter(Subtitle.script_id == script.id).order_by(Subtitle.line_no.asc()).all()
    ]
    return data


def _save_version(db: Session, content_type: str, content_id: str, version_no: int, payload: dict, operator_id: str | None) -> None:
    db.add(
        ContentVersion(
            id=new_id("ver"),
            content_type=content_type,
            content_id=content_id,
            version_no=version_no,
            payload_json=payload,
            change_note="接口编辑保存",
            operator_id=operator_id,
        )
    )


def update_script(db: Session, payload: UpdateScriptRequest, user_id: str | None) -> dict:
    script = db.get(Script, payload.script_id)
    if script is None:
        raise AppError(40400, "脚本不存在", 404)
    before = script_to_dict(script)
    fields = payload.model_dump(exclude_unset=True)
    fields.pop("script_id", None)
    mapping = {
        "steps": "steps_json",
        "example": "example_text",
        "summary": "summary_text",
        "cta": "cta_text",
        "tags": "tags_json",
    }
    for key, value in fields.items():
        setattr(script, mapping.get(key, key), value)
    script.current_version_no += 1
    _save_version(db, "script", script.id, script.current_version_no, {"before": before, "after": script_to_dict(script)}, user_id)
    db.commit()
    return {"script_id": script.id, "version": script.current_version_no, "updated_at": format_dt(script.updated_at)}


def update_storyboard(db: Session, script_id: str, items: list[StoryboardItemRequest], user_id: str | None) -> dict:
    script = db.get(Script, script_id)
    if script is None:
        raise AppError(40400, "脚本不存在", 404)
    db.query(Storyboard).filter(Storyboard.script_id == script_id).delete()
    for item in items:
        db.add(
            Storyboard(
                id=item.id or new_id("shot"),
                script_id=script_id,
                shot_no=item.shot_no,
                duration_seconds=item.duration_seconds,
                voiceover=item.voiceover,
                subtitle=item.subtitle,
                visual_type=item.visual_type,
                material_suggestion=item.material_suggestion,
                motion_suggestion=item.motion_suggestion,
                scene_note=item.scene_note,
                status="draft",
            )
        )
    script.current_version_no += 1
    _save_version(db, "storyboard", script_id, script.current_version_no, {"items": [item.model_dump() for item in items]}, user_id)
    db.commit()
    return {"script_id": script_id, "storyboard_count": len(items), "version": script.current_version_no}


def _time_to_ms(text: str | None, fallback: int) -> int:
    if not text:
        return fallback
    try:
        hours, minutes, seconds = text.split(":")
        sec, _, ms = seconds.partition(".")
        return (int(hours) * 3600 + int(minutes) * 60 + int(sec)) * 1000 + int((ms + "000")[:3])
    except ValueError:
        return fallback


def update_subtitle(db: Session, script_id: str, items: list[SubtitleItemRequest], user_id: str | None) -> dict:
    script = db.get(Script, script_id)
    if script is None:
        raise AppError(40400, "脚本不存在", 404)
    db.query(Subtitle).filter(Subtitle.script_id == script_id).delete()
    for index, item in enumerate(items, start=1):
        start_ms = item.start_time_ms if item.start_time_ms is not None else _time_to_ms(item.start_time, (index - 1) * 3000)
        end_ms = item.end_time_ms if item.end_time_ms is not None else _time_to_ms(item.end_time, index * 3000)
        db.add(
            Subtitle(
                id=item.id or new_id("sub"),
                script_id=script_id,
                line_no=item.line_no or index,
                start_time_ms=start_ms,
                end_time_ms=end_ms,
                text=item.text,
                speaker=item.speaker,
                style_name=item.style_name,
                status="draft",
            )
        )
    script.current_version_no += 1
    _save_version(db, "subtitle", script_id, script.current_version_no, {"items": [item.model_dump() for item in items]}, user_id)
    db.commit()
    return {"script_id": script_id, "subtitle_count": len(items), "version": script.current_version_no}
