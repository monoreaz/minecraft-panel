import sqlite3

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm
)

from database import (
    add_user,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username
)

from schemas import (
    TokenResponse,
    UserPublic,
    UserRegister
)

from security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login"
)


def get_current_user(
    token: Annotated[
        str,
        Depends(oauth2_scheme)
    ]
):
    user_id = decode_access_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )

    user = get_user_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    return user


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED
)
def register_user(data: UserRegister):
    username = data.username.strip()
    email = str(data.email).lower()

    if get_user_by_username(username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already taken"
        )

    if get_user_by_email(email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered"
        )

    password_hash = hash_password(
        data.password
    )

    try:
        user_id = add_user(
            username=username,
            email=email,
            password_hash=password_hash
        )

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists"
        )

    return get_user_by_id(user_id)


@router.post(
    "/login",
    response_model=TokenResponse
)
def login_user(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends()
    ]
):
    user = get_user_by_username(
        form_data.username
    )

    if (
        user is None
        or not verify_password(
            form_data.password,
            user["password_hash"]
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    access_token = create_access_token(
        user["id"]
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get(
    "/me",
    response_model=UserPublic
)
def read_current_user(
    current_user: Annotated[
        dict,
        Depends(get_current_user)
    ]
):
    return current_user