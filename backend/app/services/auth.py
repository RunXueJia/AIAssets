from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from app.core.security import create_token, hash_password, verify_password
from app.models.auth import Permission, Role, RolePermission, User, UserRole
from app.schemas.auth import TokenUser

ROLE_DEFINITIONS = [
    ("admin", "管理员", "全量权限"),
    ("operation_lead", "运营负责人", "内容、发布和数据管理"),
    ("content_editor", "内容编辑", "内容生产和审核"),
    ("video_operator", "视频运营", "视频与发布管理"),
    ("viewer", "只读查看者", "只读权限"),
]

PERMISSIONS = [
    "system:user:read",
    "system:user:create",
    "system:user:update",
    "system:role:read",
    "system:role:create",
    "system:role:update",
    "llm:provider:read",
    "llm:provider:create",
    "llm:provider:update",
    "llm:provider:test",
    "llm:model:read",
    "llm:model:create",
    "llm:model:update",
    "llm:prompt:read",
    "llm:prompt:create",
    "llm:prompt:update",
    "llm:prompt:publish",
    "llm:prompt:test",
    "llm:log:read",
    "llm:call:retry",
    "content:channel:read",
    "content:channel:create",
    "content:channel:update",
    "content:column:read",
    "content:column:create",
    "content:column:update",
    "template:video:read",
    "template:video:create",
    "template:video:update",
    "template:article:read",
    "template:article:create",
    "template:article:update",
    "publish:platform:read",
    "publish:platform:update",
    "content:topic:read",
    "content:topic:create",
    "content:topic:update",
    "content:topic:generate",
    "content:script:read",
    "content:script:update",
    "content:script:generate",
    "content:storyboard:read",
    "content:storyboard:update",
    "content:storyboard:generate",
    "review:content:read",
    "review:content:approve",
    "review:content:reject",
    "review:content:update",
    "asset:video:read",
    "asset:video:render",
    "asset:video:update",
    "asset:video:download",
    "asset:card:read",
    "asset:card:generate",
    "asset:download:read",
    "asset:download:generate",
    "content:article:read",
    "content:article:generate",
    "content:article:update",
    "content:article:publish",
    "publish:queue:read",
    "publish:queue:update",
    "publish:package:create",
    "publish:package:download",
    "lead:lead:read",
    "lead:lead:export",
    "dashboard:overview:read",
    "dashboard:task:read",
    "report:daily:read",
    "report:daily:generate",
    "report:daily:export",
    "system:task:read",
    "system:task:run",
    "system:task:update",
]


def permission_module(code: str) -> str:
    return code.split(":")[0]


def user_permissions(user: User) -> list[str]:
    if user.is_superuser:
        return PERMISSIONS
    codes: set[str] = set()
    for role in user.roles:
        for permission in role.permissions:
            codes.add(permission.code)
    return sorted(codes)


def token_user(user: User) -> TokenUser:
    return TokenUser(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        roles=[role.name for role in user.roles],
        permissions=user_permissions(user),
    )


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    stmt = (
        select(User)
        .options(selectinload(User.roles).selectinload(Role.permissions))
        .where(User.username == username)
    )
    return (await db.execute(stmt)).scalars().first()


async def get_user_with_permissions(db: AsyncSession, user_id: str) -> User:
    stmt = (
        select(User)
        .options(selectinload(User.roles).selectinload(Role.permissions))
        .where(User.id == user_id)
    )
    user = (await db.execute(stmt)).scalars().first()
    if not user:
        raise UnauthorizedError()
    if user.status != "enabled":
        raise ForbiddenError("用户已禁用")
    return user


async def authenticate(db: AsyncSession, username: str, password: str) -> User:
    user = await get_user_by_username(db, username)
    if not user or not verify_password(password, user.password_hash):
        raise UnauthorizedError("用户名或密码错误")
    if user.status != "enabled":
        raise ForbiddenError("用户已禁用")
    return user


def issue_tokens(user: User) -> dict:
    return {
        "access_token": create_token(user.id, "access"),
        "refresh_token": create_token(user.id, "refresh"),
        "expires_in": 7200,
        "user": token_user(user).model_dump(),
    }


async def seed_rbac(db: AsyncSession) -> None:
    permission_map: dict[str, Permission] = {}
    for code in PERMISSIONS:
        stmt = select(Permission).where(Permission.code == code)
        permission = (await db.execute(stmt)).scalars().first()
        if not permission:
            permission = Permission(code=code, name=code, module=permission_module(code))
            db.add(permission)
        permission_map[code] = permission

    role_map: dict[str, Role] = {}
    for name, display_name, description in ROLE_DEFINITIONS:
        stmt = select(Role).where(Role.name == name)
        role = (await db.execute(stmt)).scalars().first()
        if not role:
            role = Role(name=name, display_name=display_name, description=description)
            db.add(role)
        role_map[name] = role

    await db.flush()
    role_permissions = {
        "admin": list(permission_map.values()),
        "viewer": [p for code, p in permission_map.items() if code.endswith(":read")],
        "content_editor": [
            p
            for code, p in permission_map.items()
            if code.startswith("content:") or code.startswith("review:")
        ],
        "video_operator": [
            p
            for code, p in permission_map.items()
            if code.startswith("asset:") or code.startswith("publish:")
        ],
        "operation_lead": [
            p
            for code, p in permission_map.items()
            if code.startswith(("content:", "review:", "asset:", "publish:", "dashboard:", "lead:"))
        ],
    }
    for role_name, permissions in role_permissions.items():
        role = role_map[role_name]
        await db.execute(delete(RolePermission).where(RolePermission.role_id == role.id))
        for permission in permissions:
            db.add(RolePermission(role_id=role.id, permission_id=permission.id))

    stmt = select(User).where(User.username == "admin")
    user = (await db.execute(stmt)).scalars().first()
    if not user:
        user = User(
            username="admin",
            password_hash=hash_password("admin123456"),
            display_name="管理员",
            is_superuser=True,
        )
        db.add(user)
        await db.flush()
        db.add(UserRole(user_id=user.id, role_id=role_map["admin"].id))
    await db.commit()


async def require_user_exists(db: AsyncSession, user_id: str) -> User:
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundError("用户不存在")
    return user
