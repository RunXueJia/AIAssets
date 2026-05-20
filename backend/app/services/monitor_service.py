#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 10:03
# @File     : monitor_service.py
# @Desc     : Topic monitor service.

from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.constants import MONITOR_DELETED, MONITOR_ENABLED
from app.core.exceptions import AppError
from app.models.entities import MonitorTask, SourceSummary, Topic
from app.schemas.monitor import CreateMonitorRequest, UpdateMonitorRequest
from app.services.serializers import monitor_to_dict, source_summary_to_dict
from app.utils.id import new_id


def _next_run(schedule_time: str) -> datetime:
    hour, _, minute = schedule_time.partition(":")
    now = datetime.now()
    next_time = now.replace(hour=int(hour or 9), minute=int(minute or 0), second=0, microsecond=0)
    if next_time <= now:
        next_time += timedelta(days=1)
    return next_time


def create_monitor(db: Session, payload: CreateMonitorRequest, user_id: str | None) -> MonitorTask:
    monitor = MonitorTask(
        id=new_id("mon"),
        topic=payload.topic,
        audience=payload.audience,
        schedule_time=payload.schedule_time,
        fetch_limit=payload.fetch_limit,
        auto_generate_topics=payload.auto_generate_topics,
        status=MONITOR_ENABLED,
        cron_expression=f"0 {payload.schedule_time.split(':')[1]} {payload.schedule_time.split(':')[0]} * * *",
        next_run_at=_next_run(payload.schedule_time),
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(monitor)
    db.commit()
    db.refresh(monitor)
    return monitor


def list_monitors(db: Session, status: str | None, keyword: str | None, page: int, page_size: int) -> tuple[list[dict], int]:
    query = db.query(MonitorTask).filter(MonitorTask.deleted_at.is_(None))
    if status:
        query = query.filter(MonitorTask.status == status)
    if keyword:
        query = query.filter(MonitorTask.topic.like(f"%{keyword}%"))
    total = query.count()
    items = query.order_by(MonitorTask.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return [monitor_to_dict(item) for item in items], total


def get_monitor(db: Session, monitor_id: str) -> dict:
    monitor = db.get(MonitorTask, monitor_id)
    if monitor is None or monitor.deleted_at is not None:
        raise AppError(40400, "监控任务不存在", 404)
    return monitor_to_dict(monitor)


def update_monitor(db: Session, payload: UpdateMonitorRequest, user_id: str | None) -> dict:
    monitor = db.get(MonitorTask, payload.monitor_id)
    if monitor is None or monitor.deleted_at is not None:
        raise AppError(40400, "监控任务不存在", 404)
    monitor.topic = payload.topic
    monitor.audience = payload.audience
    monitor.schedule_time = payload.schedule_time
    monitor.fetch_limit = payload.fetch_limit
    monitor.auto_generate_topics = payload.auto_generate_topics
    monitor.next_run_at = _next_run(payload.schedule_time)
    monitor.updated_by = user_id
    db.commit()
    return {"monitor_id": monitor.id, "status": monitor.status}


def change_status(db: Session, monitor_id: str, status: str, user_id: str | None) -> dict:
    monitor = db.get(MonitorTask, monitor_id)
    if monitor is None or monitor.deleted_at is not None:
        raise AppError(40400, "监控任务不存在", 404)
    monitor.status = status
    monitor.updated_by = user_id
    if status == MONITOR_DELETED:
        monitor.deleted_at = datetime.now()
    db.commit()
    return {"monitor_id": monitor.id, "status": monitor.status}


def create_daily_summary_for_monitor(db: Session, monitor: MonitorTask) -> SourceSummary:
    summary = SourceSummary(
        id=new_id("sum"),
        summary_type="monitor_daily",
        monitor_task_id=monitor.id,
        summary_date=date.today(),
        title=f"{monitor.topic}每日素材汇总",
        summary_text=f"自动监控围绕“{monitor.topic}”形成每日素材汇总，等待运营选择后继续生成内容。",
        key_points_json=["每日自动抓取", "默认只生成选题", "发布前仍需人工审核"],
        risk_notes_json=[],
        source_count=0,
        usable_source_count=0,
        need_human_confirm=False,
        created_by=monitor.created_by,
    )
    db.add(summary)
    db.flush()
    monitor.last_run_at = datetime.now()
    monitor.next_run_at = _next_run(monitor.schedule_time)
    monitor.last_summary_id = summary.id
    if monitor.auto_generate_topics:
        for index in range(1, 4):
            db.add(
                Topic(
                    id=new_id("topic"),
                    generation_task_id="",
                    source_summary_id=summary.id,
                    title=f"{monitor.topic}自动候选选题 {index}",
                    audience=monitor.audience,
                    angle="基于每日汇总生成的候选方向",
                    recommended_column="一分钟 AI 办公",
                    duration_seconds=60,
                    keywords_json=[monitor.topic, "AI工具"],
                    reason="监控任务自动生成，进入审核前需人工确认。",
                    score=8.0,
                    status="draft",
                    need_human_confirm=True,
                )
            )
    db.commit()
    return summary


def list_daily_summaries(
    db: Session,
    monitor_id: str | None,
    start_date: str | None,
    end_date: str | None,
    page: int,
    page_size: int,
) -> tuple[list[dict], int]:
    query = db.query(SourceSummary).filter(SourceSummary.summary_type == "monitor_daily")
    if monitor_id:
        query = query.filter(SourceSummary.monitor_task_id == monitor_id)
    if start_date:
        query = query.filter(SourceSummary.summary_date >= start_date)
    if end_date:
        query = query.filter(SourceSummary.summary_date <= end_date)
    total = query.count()
    items = query.order_by(SourceSummary.summary_date.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for item in items:
        data = source_summary_to_dict(item)
        data.update(
            {
                "summary_id": item.id,
                "monitor_id": item.monitor_task_id,
                "date": data["date"],
                "topic_count": db.query(Topic).filter(Topic.source_summary_id == item.id).count(),
                "status": "success",
            }
        )
        result.append(data)
    return result, total
