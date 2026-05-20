#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author   : Codex
# @Time     : 2026/05/20 09:50
# @File     : bootstrap.py
# @Desc     : Seed default roles, permissions, settings and admin account.

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import DEFAULT_COLUMNS, ROLE_PERMISSIONS
from app.core.security import hash_password
from app.models.entities import Permission, Role, RolePermission, SystemSetting, User
from app.utils.id import new_id


PERMISSION_NAMES = {
    "*": "全部权限",
    "dashboard:view": "查看数据看板",
    "generation:create": "创建生成任务",
    "generation:view": "查看生成任务",
    "source:view": "查看素材来源",
    "topic:view": "查看选题",
    "topic:manage": "管理选题",
    "script:view": "查看脚本",
    "script:manage": "管理脚本",
    "review:manage": "审核内容",
    "monitor:manage": "管理话题监控",
    "render:manage": "管理视频合成",
    "package:view": "查看发布包",
    "package:manage": "管理发布包",
    "publish:manage": "管理发布记录",
    "report:view": "查看每日报告",
    "file:download": "下载文件",
}


ROLE_NAMES = {
    "admin": "管理员",
    "operation_manager": "运营负责人",
    "content_editor": "内容编辑",
    "video_operator": "视频运营",
    "viewer": "只读查看者",
}


def ensure_bootstrap_data(db: Session) -> None:
    permission_map: dict[str, Permission] = {}
    for code, name in PERMISSION_NAMES.items():
        permission = db.query(Permission).filter(Permission.code == code).one_or_none()
        if permission is None:
            module = "all" if code == "*" else code.split(":", 1)[0]
            action = "all" if code == "*" else code.rsplit(":", 1)[-1]
            permission = Permission(
                id=new_id("perm"),
                code=code,
                name=name,
                type="api",
                module=module,
                action=action,
                status="enabled",
            )
            db.add(permission)
        permission_map[code] = permission

    role_map: dict[str, Role] = {}
    for index, (code, permissions) in enumerate(ROLE_PERMISSIONS.items()):
        role = db.query(Role).filter(Role.code == code).one_or_none()
        if role is None:
            role = Role(
                id=new_id("role"),
                code=code,
                name=ROLE_NAMES.get(code, code),
                status="enabled",
                sort_order=index,
            )
            db.add(role)
        role_map[code] = role
        db.flush()
        for permission_code in permissions:
            permission = permission_map[permission_code]
            exists = (
                db.query(RolePermission)
                .filter(RolePermission.role_id == role.id, RolePermission.permission_id == permission.id)
                .one_or_none()
            )
            if exists is None:
                db.add(RolePermission(id=new_id("rp"), role_id=role.id, permission_id=permission.id))

    admin_role = role_map["admin"]
    admin = db.query(User).filter(User.username == settings.default_admin_username).one_or_none()
    if admin is None:
        db.add(
            User(
                id=new_id("user"),
                username=settings.default_admin_username,
                password_hash=hash_password(settings.default_admin_password),
                display_name=settings.default_admin_display_name,
                role_id=admin_role.id,
                status="enabled",
            )
        )

    default_settings = {
        "default_count": ("默认生成数量", "generation", 5, False, False),
        "default_fetch_limit": ("默认抓取数量", "fetch", 20, False, False),
        "enabled_columns": ("默认启用栏目", "content", DEFAULT_COLUMNS, False, False),
        "storage_type": ("文件存储类型", "storage", "local", False, False),
        "model_provider": ("模型服务商", "llm", settings.llm_model_provider, False, True),
        "model_base_url": ("模型接口地址", "llm", settings.llm_model_base_url, True, True),
        "model_api_key": ("模型 API Key", "llm", settings.llm_model_api_key, True, True),
        "model_name": ("模型名称", "llm", settings.llm_model_name, False, True),
        "model_timeout_seconds": (
            "模型请求超时时间",
            "llm",
            settings.llm_request_timeout_seconds,
            False,
            True,
        ),
    }
    for key, (name, group, value, is_secret, env_override) in default_settings.items():
        exists = db.query(SystemSetting).filter(SystemSetting.setting_key == key).one_or_none()
        if exists is None:
            db.add(
                SystemSetting(
                    id=new_id("set"),
                    setting_key=key,
                    setting_name=name,
                    setting_group=group,
                    setting_value_json=value,
                    value_type="json",
                    is_secret=is_secret,
                    scope="global",
                )
            )
        elif env_override and value not in ("", None):
            exists.setting_value_json = value
            exists.is_secret = is_secret
    db.commit()
