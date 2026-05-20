#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 10:18
# @File     : main.py
# @Desc     : FastAPI application entrypoint.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.db.session import SessionLocal
from app.services.bootstrap import ensure_bootstrap_data


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.on_event("startup")
    def startup() -> None:
        try:
            with SessionLocal() as db:
                ensure_bootstrap_data(db)
        except Exception:
            # Database may not exist before running scripts/create_database.sql and Alembic.
            # The app still imports cleanly so Swagger and checks can run.
            pass

    @app.get("/health")
    def health() -> dict:
        return {"code": 0, "message": "success", "data": {"status": "ok", "database": settings.database_name}}

    return app


app = create_app()
