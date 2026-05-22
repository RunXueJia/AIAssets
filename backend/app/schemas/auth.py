from pydantic import BaseModel, ConfigDict, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)
    nickname: str | None = Field(default=None, max_length=64)
    email: str | None = Field(default=None, max_length=128, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class LoginRequest(BaseModel):
    account: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=128)
    client_type: str = Field(default="web", max_length=20)


class GuestSessionRequest(BaseModel):
    client_id: str = Field(min_length=8, max_length=128)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class UserPublic(BaseModel):
    id: int
    username: str | None = None
    nickname: str | None = None
    role: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class AuthTokens(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int


class AuthData(AuthTokens):
    user: UserPublic


class RefreshTokenData(AuthTokens):
    pass
