#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 10:12
# @File     : api.py
# @Desc     : API v1 router registry.

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    dashboard,
    file,
    generation,
    monitor,
    package,
    publish,
    render,
    report,
    review,
    script,
    setting,
    source,
    topic,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(generation.router, prefix="/generation", tags=["generation"])
api_router.include_router(source.router, prefix="/source", tags=["source"])
api_router.include_router(topic.router, prefix="/topic", tags=["topic"])
api_router.include_router(script.router, prefix="/script", tags=["script"])
api_router.include_router(script.storyboard_router, prefix="/storyboard", tags=["storyboard"])
api_router.include_router(script.subtitle_router, prefix="/subtitle", tags=["subtitle"])
api_router.include_router(review.router, prefix="/review", tags=["review"])
api_router.include_router(monitor.router, prefix="/monitor", tags=["monitor"])
api_router.include_router(render.router, prefix="/render", tags=["render"])
api_router.include_router(package.router, prefix="/package", tags=["package"])
api_router.include_router(publish.router, prefix="/publish", tags=["publish"])
api_router.include_router(report.router, prefix="/report", tags=["report"])
api_router.include_router(setting.router, prefix="/setting", tags=["setting"])
api_router.include_router(file.router, prefix="/file", tags=["file"])
