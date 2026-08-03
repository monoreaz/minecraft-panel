import os
import sqlite3
import time

from dotenv import load_dotenv
from typing import Annotated

load_dotenv()

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
    delete_email_verification_code,
    delete_user,
    get_email_verification_code,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    increment_verification_attempts,
    mark_user_email_verified,
    save_email_verification_code,
    update_user_email,
    update_user_password_hash,
    update_user_username
)

from schemas import (
    EmailUpdate,
    EmailVerificationRequest,
    EmailVerificationResend,
    MessageResponse,
    PasswordUpdate,
    TokenResponse,
    UserPublic,
    UserRegister,
    UsernameUpdate
)

from email_service import (
    send_verification_email
)

from security import (
    create_access_token,
    decode_access_token,
    generate_email_verification_code,
    hash_email_verification_code,
    hash_password,
    verify_email_verification_code,
    verify_password
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login"
)

EMAIL_VERIFICATION_EXPIRE_MINUTES = int(
    os.getenv(
        "EMAIL_VERIFICATION_EXPIRE_MINUTES",
        "10"
    )
)

EMAIL_VERIFICATION_RESEND_SECONDS = int(
    os.getenv(
        "EMAIL_VERIFICATION_RESEND_SECONDS",
        "60"
    )
)

EMAIL_VERIFICATION_MAX_ATTEMPTS = int(
    os.getenv(
        "EMAIL_VERIFICATION_MAX_ATTEMPTS",
        "5"
    )
)

def create_verification_code_for_user(
    user: dict
):
    code = (
        generate_email_verification_code()
    )

    current_time = int(
        time.time()
    )

    expires_at = (
        current_time
        + EMAIL_VERIFICATION_EXPIRE_MINUTES
        * 60
    )

    code_hash = (
        hash_email_verification_code(
            user["email"],
            code
        )
    )

    save_email_verification_code(
        user_id=user["id"],
        code_hash=code_hash,
        expires_at=expires_at,
        last_sent_at=current_time
    )

    try:
        send_verification_email(
            user["email"],
            code
        )

    except Exception:
        delete_email_verification_code(
            user["id"]
        )

        raise

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

    if not user["is_active"]:
        raise HTTPException(
            tatus_code=status.HTTP_403_FORBIDDEN,
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
            password_hash=password_hash,
            email_verified=False
        )

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists"
        )

    user = get_user_by_id(
        user_id
    )

    try:
        create_verification_code_for_user(
            user
        )

    except Exception as error:
        print(
            "Could not send verification email:",
            error
        )

        delete_user(
            user_id
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Could not send verification email. "
                "Please try again later."
            )
        )

    return user


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

    if not user["email_verified"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email is not verified"
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

    updated_user = get_user_by_id(
        current_user["id"]
    )

    try:
        create_verification_code_for_user(
            updated_user
        )

    except Exception as error:
        print(
            "Could not send verification email:",
            error
        )

        update_user_email(
            current_user["id"],
            current_user["email"],
            email_verified=True
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Could not send verification email. "
                "Your previous email was restored."
            )
        )

    return updated_user


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

@router.post(
    "/verify-email",
    response_model=MessageResponse
)
def verify_email(
    data: EmailVerificationRequest
):
    email = str(data.email).lower()

    user = get_user_by_email(
        email
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid email or "
                "verification code"
            )
        )

    if user["email_verified"]:
        return {
            "success": True,
            "message": "Email is already verified"
        }

    verification = (
        get_email_verification_code(
            user["id"]
        )
    )

    if verification is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Verification code not found. "
                "Request a new code."
            )
        )

    current_time = int(
        time.time()
    )

    if (
        verification["expires_at"]
        <= current_time
    ):
        delete_email_verification_code(
            user["id"]
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Verification code has expired. "
                "Request a new code."
            )
        )

    code_is_valid = (
        verify_email_verification_code(
            email,
            data.code,
            verification["code_hash"]
        )
    )

    if not code_is_valid:
        next_attempt_count = (
            verification["failed_attempts"]
            + 1
        )

        increment_verification_attempts(
            user["id"]
        )

        if (
            next_attempt_count
            >= EMAIL_VERIFICATION_MAX_ATTEMPTS
        ):
            delete_email_verification_code(
                user["id"]
            )

            raise HTTPException(
                status_code=(
                    status.HTTP_429_TOO_MANY_REQUESTS
                ),
                detail=(
                    "Too many incorrect attempts. "
                    "Request a new code."
                )
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )

    mark_user_email_verified(
        user["id"]
    )

    delete_email_verification_code(
        user["id"]
    )

    return {
        "success": True,
        "message": "Email successfully verified"
    }


@router.post(
    "/resend-verification",
    response_model=MessageResponse
)
def resend_verification(
    data: EmailVerificationResend
):
    email = str(data.email).lower()

    user = get_user_by_email(
        email
    )

    generic_message = (
        "If an unverified account exists, "
        "a new code has been sent."
    )

    if user is None:
        return {
            "success": True,
            "message": generic_message
        }

    if user["email_verified"]:
        return {
            "success": True,
            "message": "Email is already verified"
        }

    existing_code = (
        get_email_verification_code(
            user["id"]
        )
    )

    current_time = int(
        time.time()
    )

    if existing_code is not None:
        elapsed_seconds = (
            current_time
            - existing_code["last_sent_at"]
        )

        if (
            elapsed_seconds
            < EMAIL_VERIFICATION_RESEND_SECONDS
        ):
            remaining_seconds = (
                EMAIL_VERIFICATION_RESEND_SECONDS
                - elapsed_seconds
            )

            raise HTTPException(
                status_code=(
                    status.HTTP_429_TOO_MANY_REQUESTS
                ),
                detail=(
                    "Please wait "
                    f"{remaining_seconds} seconds "
                    "before requesting another code"
                )
            )

    try:
        create_verification_code_for_user(
            user
        )

    except Exception as error:
        print(
            "Could not resend verification email:",
            error
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Could not send verification email. "
                "Please try again later."
            )
        )

    return {
        "success": True,
        "message": generic_message
    }