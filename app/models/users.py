from pydantic import Field, BaseModel, EmailStr, field_validator, ValidationError
from pydantic_settings import SettingsConfigDict
from app.utils import helpers
from app.config.settings import get_settings
from .enums import UserType, OperationTypes


settings = get_settings()


USER_EXCLUDE_FIELDS = {
    "password_hash", "password_reset_at", "password_updated_at"
}


class UserBase(BaseModel):

    email:  EmailStr | None
    full_name: str = Field(
        alias="fullName",  min_length=2, max_length=32)

    @field_validator("full_name")
    @classmethod
    def check_fullname(cls, v):

        if not v:
            raise ValueError("Fullname is required.")

        names_arr = v.split(" ")

        if len(names_arr) < 2:
            raise ValueError("Fullname must contain at least two names.")

        # for name in names_arr:
        #     if len(name) < 2:
        #         raise ValueError(
        #             "Each name must contain at least two characters.")

        return f"{names_arr[0].title()} {names_arr[1].title()}"


class UserInput(UserBase):
    password: str = Field(min_length=8, max_length=20)

    model_config = SettingsConfigDict(populate_by_name=True)


class User(UserBase):
    uid:  str = Field(default_factory=helpers.get_uuid4)

    created_at: float = Field(
        default_factory=helpers.get_utc_timestamp, alias="createdAt")
    password_reset_at: float | None = Field(
        default=None, alias="passwordResetAt")
    password_hash: str | None = Field(None, alias="passwordHash")
    password_updated_at: float | None = Field(
        default=None, alias="passwordUpdatedAt")
    is_active: bool = Field(default=False, alias="isActive")
    email_verified: bool = Field(default=False, alias="emailVerified")

    model_config = SettingsConfigDict(populate_by_name=True)


class AccessCode(BaseModel):
    uid: str = Field(alias="uid", default_factory=helpers.get_uuid4)
    key: str = Field(min_length=32)
    operation_type: OperationTypes
    resource_id:  str = Field(min_length=8, max_length=64)
    created_at: float = Field(
        default_factory=helpers.get_utc_timestamp, alias="createdAt")
    interval: int = Field(default=settings.code_duration)
    revoked:  bool = False


class AuthSession(BaseModel):
    uid: str = Field(alias="uid")
    user_id: str = Field(alias="userId")
    revoked: bool = Field(alias="revoked", default=False)
    created_at: float = Field(
        default_factory=helpers.get_utc_timestamp, alias="createdAt")
    duration_in_hours: float = Field(alias="durationInHours")
    last_used: float | None = Field(alias="lastUsed", default=None)
    usage_count: int = Field(alias="usageCount", default=0)
    meta: str | None = Field(None)

    model_config = SettingsConfigDict(populate_by_name=True)


class AccessToken(BaseModel):
    access_token:  str = Field()
    bearer:  str = Field(default="Bearer")


class PasswordResetCompleteInput(BaseModel):
    uid: str = Field(min_length=32)
    token: str = Field(min_length=16)


class PasswordResetInput(BaseModel):
    email: EmailStr
    new_password: str = Field(min_length=8, max_length=25, alias="newPassword")
    user_type:  UserType = Field(alias="userType")


class PasswordResetStore(BaseModel):
    uid: str = Field(min_length=32, default_factory=helpers.get_uuid4)
    user_id: str = Field(min_length=32, alias="userId")
    new_password_hash: str = Field(min_length=32, alias="newPasswordHash")
    valid: bool = Field(default=True)
    token: str = Field(
        min_length=16, default_factory=helpers.get_random_string)
    created_at: float = Field(
        default_factory=helpers.get_utc_timestamp, alias="createdAt")

    model_config = SettingsConfigDict(populate_by_name=True)


class SessionInfo(BaseModel):
    user: User | None = None
    session: AuthSession | None = None
    is_authenticated:  bool = Field(default=False, alias="isAuthenticated")
    error: str | None = None

    model_config = SettingsConfigDict(populate_by_name=True)


class EmailVerifyOutput(BaseModel):
    acuid:  str
    rid:  str
