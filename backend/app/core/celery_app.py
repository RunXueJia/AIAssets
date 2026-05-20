#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 10:45
# @File     : celery_app.py
# @Desc     : Celery application configured with Redis broker and result backend.

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "hours24_backend",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.generation_tasks", "app.tasks.render_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_track_started=True,
    worker_prefetch_multiplier=1,
)
