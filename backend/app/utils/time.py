#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 09:35
# @File     : time.py
# @Desc     : Datetime formatting helpers.

from datetime import date, datetime


def format_dt(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.strftime("%Y-%m-%d %H:%M:%S")


def format_date(value: date | None) -> str | None:
    if value is None:
        return None
    return value.strftime("%Y-%m-%d")
