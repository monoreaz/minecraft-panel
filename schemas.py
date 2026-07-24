from pydantic import (
    BaseModel,
    EmailStr,
    Field
)


class UserRegister(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=32,
        pattern=r"^[A-Za-z0-9_]+$"
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128
    )


class UserPublic(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str