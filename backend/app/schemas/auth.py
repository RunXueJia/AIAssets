from pydantic import BaseModel, Field

from app.schemas.common import TimestampMixin


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str | None = None


class TokenUser(BaseModel):
    id: str
    username: str
    display_name: str
    roles: list[str]
    permissions: list[str]


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    user: TokenUser


class UserCreate(BaseModel):
    username: str
    password: str = Field(min_length=6)
    display_name: str = ""
    email: str | None = None
    role_ids: list[str] = Field(default_factory=list)


class UserUpdate(BaseModel):
    id: str
    display_name: str | None = None
    email: str | None = None
    role_ids: list[str] | None = None


class ResetPasswordRequest(BaseModel):
    id: str
    password: str = Field(min_length=6)


class UserOut(TimestampMixin):
    username: str
    display_name: str
    email: str | None
    status: str
    is_superuser: bool
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)


class RoleCreate(BaseModel):
    name: str
    display_name: str
    description: str = ""
    permission_ids: list[str] = Field(default_factory=list)


class RolePermissionUpdate(BaseModel):
    role_id: str
    permission_ids: list[str]


class RoleOut(TimestampMixin):
    name: str
    display_name: str
    description: str
    status: str
    permissions: list[str] = Field(default_factory=list)
