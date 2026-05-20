#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 09:35
# @File     : id.py
# @Desc     : Business ID generator.

from uuid import uuid4


def new_id(prefix: str) -> str:
    clean_prefix = prefix.strip("_")[:8]
    suffix = uuid4().hex[:22]
    return f"{clean_prefix}_{suffix}"[:32]
