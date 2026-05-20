#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 11:05
# @File     : render_tasks.py
# @Desc     : Celery tasks for video rendering.

from app.core.celery_app import celery_app
from app.core.constants import CONTENT_RENDER_FAILED, TASK_FAILED
from app.db.session import SessionLocal
from app.models.entities import RenderTask, Script
from app.services.asset_service import execute_render_task


@celery_app.task(name="render.run_render_task")
def run_render_task(render_task_id: str) -> dict:
    with SessionLocal() as db:
        render = db.get(RenderTask, render_task_id)
        if render is None:
            return {"render_task_id": render_task_id, "status": "not_found"}
        try:
            execute_render_task(db, render.id)
            return {"render_task_id": render.id, "status": render.status}
        except Exception as exc:
            render.status = TASK_FAILED
            render.error_message = str(exc)[:1000]
            script = db.get(Script, render.script_id)
            if script is not None:
                script.status = CONTENT_RENDER_FAILED
            db.commit()
            return {"render_task_id": render.id, "status": render.status, "error": render.error_message}
