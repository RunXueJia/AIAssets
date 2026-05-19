from fastapi import APIRouter, Depends
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, require_permission
from app.core.exceptions import NotFoundError, UnauthorizedError
from app.core.response import ok, page_response
from app.core.security import decode_token, hash_password
from app.db.session import get_db
from app.models.auth import Role, User
from app.repositories.base import BaseRepository
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    RoleCreate,
    RoleOut,
    RolePermissionUpdate,
    UserCreate,
    UserOut,
    UserUpdate,
)
from app.services.auth import (
    authenticate,
    get_user_with_permissions,
    issue_tokens,
    token_user,
    user_permissions,
)

router = APIRouter()
user_repo = BaseRepository(User)
role_repo = BaseRepository(Role)


def serialize_user(user: User) -> dict:
    return UserOut(
        id=user.id,
        created_at=user.created_at,
        updated_at=user.updated_at,
        username=user.username,
        display_name=user.display_name,
        email=user.email,
        status=user.status,
        is_superuser=user.is_superuser,
        roles=[role.name for role in user.roles],
        permissions=user_permissions(user),
    ).model_dump()


def serialize_role(role: Role) -> dict:
    return RoleOut(
        id=role.id,
        created_at=role.created_at,
        updated_at=role.updated_at,
        name=role.name,
        display_name=role.display_name,
        description=role.description,
        status=role.status,
        permissions=[permission.code for permission in role.permissions],
    ).model_dump()


@router.post("/auth/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate(db, payload.username, payload.password)
    return ok(issue_tokens(user))


@router.post("/auth/logout")
async def logout(_: User = Depends(get_current_user)):
    return ok()


@router.get("/auth/get_current_user")
async def current_user(user: User = Depends(get_current_user)):
    return ok(token_user(user).model_dump())


@router.post("/auth/refresh_token")
async def refresh_token(payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    if not payload.refresh_token:
        raise UnauthorizedError()
    try:
        decoded = decode_token(payload.refresh_token)
    except InvalidTokenError as exc:
        raise UnauthorizedError() from exc
    if decoded.get("type") != "refresh":
        raise UnauthorizedError("Token 类型错误")
    user = await get_user_with_permissions(db, decoded["sub"])
    return ok(issue_tokens(user))


@router.get("/users/get_user_list")
async def get_user_list(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("system:user:read")),
):
    items, total = await user_repo.list(
        db, page=page, page_size=page_size, keyword=keyword, keyword_fields=["username", "display_name"]
    )
    return page_response([serialize_user(item) for item in items], total, page, page_size)


@router.get("/users/get_user_detail/{id}")
async def get_user_detail(
    id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("system:user:read")),
):
    item = await user_repo.get(db, id)
    if not item:
        raise NotFoundError("用户不存在")
    return ok(serialize_user(item))


@router.post("/users/create_user")
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("system:user:create")),
):
    item = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
        email=payload.email,
    )
    if payload.role_ids:
        roles = (await db.execute(select(Role).where(Role.id.in_(payload.role_ids)))).scalars().all()
        item.roles = list(roles)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return ok(serialize_user(item))


@router.post("/users/update_user")
async def update_user(
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("system:user:update")),
):
    item = await user_repo.get(db, payload.id)
    if not item:
        raise NotFoundError("用户不存在")
    item.display_name = payload.display_name if payload.display_name is not None else item.display_name
    item.email = payload.email if payload.email is not None else item.email
    if payload.role_ids is not None:
        roles = (await db.execute(select(Role).where(Role.id.in_(payload.role_ids)))).scalars().all()
        item.roles = list(roles)
    await db.commit()
    await db.refresh(item)
    return ok(serialize_user(item))


@router.post("/users/change_user_status")
async def change_user_status(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("system:user:update")),
):
    item = await user_repo.get(db, payload["id"])
    if not item:
        raise NotFoundError("用户不存在")
    item.status = payload["status"]
    await db.commit()
    return ok()


@router.post("/users/reset_user_password")
async def reset_user_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("system:user:update")),
):
    item = await user_repo.get(db, payload.id)
    if not item:
        raise NotFoundError("用户不存在")
    item.password_hash = hash_password(payload.password)
    await db.commit()
    return ok()


@router.get("/roles/get_role_list")
async def get_role_list(
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("system:role:read")),
):
    stmt = select(Role).options(selectinload(Role.permissions))
    if keyword:
        stmt = stmt.where(Role.name.ilike(f"%{keyword}%") | Role.display_name.ilike(f"%{keyword}%"))
    roles = (await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    total_items, total = await role_repo.list(
        db, page=1, page_size=1, keyword=keyword, keyword_fields=["name", "display_name"]
    )
    del total_items
    return page_response([serialize_role(item) for item in roles], total, page, page_size)


@router.post("/roles/create_role")
async def create_role(
    payload: RoleCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("system:role:create")),
):
    role = Role(name=payload.name, display_name=payload.display_name, description=payload.description)
    db.add(role)
    await db.flush()
    if payload.permission_ids:
        from app.models.auth import Permission

        permissions = (
            await db.execute(select(Permission).where(Permission.id.in_(payload.permission_ids)))
        ).scalars().all()
        role.permissions = list(permissions)
    await db.commit()
    await db.refresh(role)
    return ok(serialize_role(role))


@router.post("/roles/update_role_permissions")
async def update_role_permissions(
    payload: RolePermissionUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("system:role:update")),
):
    from app.models.auth import Permission

    role = await role_repo.get(db, payload.role_id)
    if not role:
        raise NotFoundError("角色不存在")
    permissions = (
        await db.execute(select(Permission).where(Permission.id.in_(payload.permission_ids)))
    ).scalars().all()
    role.permissions = list(permissions)
    await db.commit()
    await db.refresh(role)
    return ok(serialize_role(role))
