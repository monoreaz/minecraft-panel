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
    get_user_by_username,
    update_user_email,
    update_user_password_hash,
    update_user_username
)

from schemas import (
    EmailUpdate,
    MessageResponse,
    PasswordUpdate,
    TokenResponse,
    UserPublic,
    UserRegister,
    UsernameUpdate
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

def require_current_password(
    current_password: str,
    current_user: dict
):
    if not verify_password(
        current_password,
        current_user["password_hash"]
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

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

@router.patch(
    "/me/username",
    response_model=UserPublic
)
def update_current_username(
    data: UsernameUpdate,
    current_user: Annotated[
        dict,
        Depends(get_current_user)
    ]
):
    require_current_password(
        data.current_password,
        current_user
    )

    username = data.username.strip()

    existing_user = get_user_by_username(
        username
    )

    if (
        existing_user is not None
        and existing_user["id"]
        != current_user["id"]
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already taken"
        )

    try:
        updated = update_user_username(
            current_user["id"],
            username
        )

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already taken"
        )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return get_user_by_id(
        current_user["id"]
    )


@router.patch(
    "/me/email",
    response_model=UserPublic
)
def update_current_email(
    data: EmailUpdate,
    current_user: Annotated[
        dict,
        Depends(get_current_user)
    ]
):
    require_current_password(
        data.current_password,
        current_user
    )

    email = str(data.email).lower()

    existing_user = get_user_by_email(
        email
    )

    if (
        existing_user is not None
        and existing_user["id"]
        != current_user["id"]
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered"
        )

    try:
        updated = update_user_email(
            current_user["id"],
            email
        )

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered"
        )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return get_user_by_id(
        current_user["id"]
    )


@router.patch(
    "/me/password",
    response_model=MessageResponse
)
def update_current_password(
    data: PasswordUpdate,
    current_user: Annotated[
        dict,
        Depends(get_current_user)
    ]
):
    require_current_password(
        data.current_password,
        current_user
    )

    if (
        data.new_password
        != data.confirm_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match"
        )

    if verify_password(
        data.new_password,
        current_user["password_hash"]
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "New password must be different "
                "from the current password"
            )
        )

    password_hash = hash_password(
        data.new_password
    )

    updated = update_user_password_hash(
        current_user["id"],
        password_hash
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "success": True,
        "message": "Password successfully changed"
    }