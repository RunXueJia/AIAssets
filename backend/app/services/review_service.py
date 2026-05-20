#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 10:03
# @File     : review_service.py
# @Desc     : Content review workflows.

from sqlalchemy.orm import Session

from app.core.constants import CONTENT_APPROVED, CONTENT_APPROVED_WITH_EDIT, CONTENT_PENDING_RENDER, CONTENT_REJECTED
from app.core.exceptions import AppError
from app.models.entities import ReviewRecord, Script
from app.schemas.auth import CurrentUser
from app.services.generation_service import update_script
from app.services.serializers import review_record_to_dict
from app.utils.id import new_id


def list_reviews(db: Session, status: str | None, keyword: str | None, page: int, page_size: int) -> tuple[list[dict], int]:
    query = db.query(Script)
    if status:
        query = query.filter(Script.status == status)
    if keyword:
        query = query.filter(Script.title.like(f"%{keyword}%"))
    total = query.count()
    scripts = query.order_by(Script.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return [
        {
            "content_id": item.id,
            "content_type": "script",
            "title": item.title,
            "status": item.status,
            "need_human_confirm": item.need_human_confirm,
            "risk_notes": item.risk_notes_json or [],
            "created_by_name": "系统生成",
            "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for item in scripts
    ], total


def _get_script(content_type: str, content_id: str, db: Session) -> Script:
    if content_type != "script":
        raise AppError(40001, "MVP 阶段仅支持脚本审核", 400)
    script = db.get(Script, content_id)
    if script is None:
        raise AppError(40400, "审核内容不存在", 404)
    return script


def _record(
    db: Session,
    script: Script,
    action: str,
    before_status: str,
    after_status: str,
    current_user: CurrentUser,
    reason: str | None = None,
    comment: str | None = None,
    edited_payload: dict | None = None,
) -> ReviewRecord:
    record = ReviewRecord(
        id=new_id("rev"),
        content_type="script",
        content_id=script.id,
        generation_task_id=script.generation_task_id,
        action=action,
        before_status=before_status,
        after_status=after_status,
        reason=reason,
        comment=comment,
        edited_payload_json=edited_payload,
        reviewer_id=current_user.id,
        reviewer_name=current_user.display_name,
    )
    db.add(record)
    return record


def approve(db: Session, content_id: str, content_type: str, comment: str | None, current_user: CurrentUser) -> dict:
    script = _get_script(content_type, content_id, db)
    before = script.status
    script.status = CONTENT_APPROVED
    _record(db, script, "approve", before, CONTENT_APPROVED, current_user, comment=comment)
    db.commit()
    return {"content_id": script.id, "status": script.status, "next_status": CONTENT_PENDING_RENDER}


def approve_with_edit(
    db: Session,
    content_id: str,
    content_type: str,
    edited_payload: dict,
    comment: str | None,
    current_user: CurrentUser,
) -> dict:
    script = _get_script(content_type, content_id, db)
    before = script.status
    if edited_payload:
        from app.schemas.generation import UpdateScriptRequest

        update_payload = UpdateScriptRequest(script_id=script.id, **edited_payload)
        update_script(db, update_payload, current_user.id)
        db.refresh(script)
    script.status = CONTENT_APPROVED_WITH_EDIT
    _record(
        db,
        script,
        "approve_with_edit",
        before,
        CONTENT_APPROVED_WITH_EDIT,
        current_user,
        comment=comment,
        edited_payload=edited_payload,
    )
    db.commit()
    return {
        "content_id": script.id,
        "status": script.status,
        "version": script.current_version_no,
        "next_status": CONTENT_PENDING_RENDER,
    }


def reject(db: Session, content_id: str, content_type: str, reason: str, current_user: CurrentUser) -> dict:
    script = _get_script(content_type, content_id, db)
    before = script.status
    script.status = CONTENT_REJECTED
    _record(db, script, "reject", before, CONTENT_REJECTED, current_user, reason=reason)
    db.commit()
    return {"content_id": script.id, "status": script.status}


def regenerate(db: Session, content_id: str, content_type: str, reason: str | None, current_user: CurrentUser) -> dict:
    script = _get_script(content_type, content_id, db)
    from app.schemas.generation import CreateGenerationTaskRequest
    from app.services.generation_service import create_generation_task

    payload = CreateGenerationTaskRequest(
        direction=script.title,
        topic=script.title,
        audience=None,
        count=5,
        column="auto",
        generation_type="full_script_storyboard",
        start_mode="now",
    )
    task = create_generation_task(db, payload, current_user.id)
    _record(db, script, "regenerate", script.status, script.status, current_user, reason=reason)
    db.commit()
    return {"task_id": task.id, "status": task.status, "stream_url": f"/api/v1/generation/stream/{task.id}"}


def review_history(db: Session, content_id: str) -> list[dict]:
    records = db.query(ReviewRecord).filter(ReviewRecord.content_id == content_id).order_by(ReviewRecord.created_at.desc()).all()
    script = db.get(Script, content_id)
    return [review_record_to_dict(item, script) for item in records]
