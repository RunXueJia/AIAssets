#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 10:45
# @File     : redis_service.py
# @Desc     : Redis connection helpers.

import redis

from app.core.config import settings


def get_redis_client() -> redis.Redis:
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


def ping_redis() -> bool:
    client = get_redis_client()
    try:
        return bool(client.ping())
    except redis.RedisError:
        return False
