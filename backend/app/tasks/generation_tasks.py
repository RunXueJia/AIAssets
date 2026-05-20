#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 11:05
# @File     : generation_tasks.py
# @Desc     : Celery tasks for generation pipeline.

from app.core.celery_app import celery_app
from app.core.constants import TASK_FAILED
from app.db.session import SessionLocal
from app.models.entities import GenerationTask
from app.services.generation_service import run_generation_pipeline
from app.services.log_service import create_task_log


@celery_app.task(name="generation.run_generation_task")
def run_generation_task(task_id: str) -> dict:
    with SessionLocal() as db:
        task = db.get(GenerationTask, task_id)
        if task is None:
            return {"task_id": task_id, "status": "not_found"}
        try:
            run_generation_pipeline(db, task)
            db.commit()
            return {"task_id": task.id, "status": task.status}
        except Exception as exc:
            task.status = TASK_FAILED
            task.error_message = str(exc)[:1000]
            create_task_log(
                db,
                task_type="generation",
                task_id=task.id,
                generation_task_id=task.id,
                event_type="error",
                stage=task.current_stage,
                level="error",
                message="生成任务执行失败",
                error_message=task.error_message,
            )
            db.commit()
            return {"task_id": task.id, "status": task.status, "error": task.error_message}
