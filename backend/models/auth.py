from datetime import datetime

from pydantic import BaseModel, computed_field, model_validator

from backend.enums import UserRole


class LoginRequest(BaseModel):
    username: str
    password: str


class UserInfo(BaseModel):
    id: int
    username: str
    display_name: str | None
    email: str | None
    avatar_path: str | None
    role: UserRole
    created_at: datetime
    require_password_change: bool

    @computed_field
    @property
    def avatar_url(self) -> str | None:
        """Generate full URL for avatar if avatar_path exists."""
        if self.avatar_path:
            return f"/avatars/{self.avatar_path}"
        return None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


class CreateUserRequest(BaseModel):
    username: str
    password: str
    display_name: str | None = None
    email: str | None = None
    role: UserRole
    require_password_change: bool = True

    @model_validator(mode="after")
    def sanitize_fields(self) -> "CreateUserRequest":
        """Sanitize fields after model initialization."""
        self.username = self.username.strip()
        self.password = self.password.strip()
        if self.display_name is not None and self.display_name.strip() == "":
            self.display_name = None
        if self.email is not None and self.email.strip() == "":
            self.email = None
        return self


class ChangeProfileInfoRequest(BaseModel):
    display_name: str | None = None
    email: str | None = None

    @model_validator(mode="after")
    def sanitize_fields(self) -> "ChangeProfileInfoRequest":
        if self.display_name is not None:
            self.display_name = self.display_name.strip() or None
        if self.email is not None:
            self.email = self.email.strip() or None
        return self


class ChangePasswordRequest(BaseModel):
    old_password: str | None = None
    new_password: str

    @model_validator(mode="after")
    def sanitize_fields(self) -> "ChangePasswordRequest":
        if self.old_password is not None:
            self.old_password = self.old_password.strip() or None
        self.new_password = self.new_password.strip()
        return self


# class LinkJellyfinRequest(BaseModel):
#     username: str
#     password: str
