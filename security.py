import os

from datetime import (
    datetime,
    timedelta,
    timezone
)

import jwt

from dotenv import load_dotenv
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash


load_dotenv()


JWT_SECRET = os.getenv("JWT_SECRET")

JWT_ALGORITHM = os.getenv(
    "JWT_ALGORITHM",
    "HS256"
)

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "30"
    )
)


if not JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET is missing from the .env file"
    )


password_hasher = PasswordHash.recommended()


def hash_password(password: str):
    return password_hasher.hash(password)


def verify_password(
    plain_password: str,
    password_hash: str
):
    return password_hasher.verify(
        plain_password,
        password_hash
    )


def create_access_token(user_id: int):
    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    payload = {
        "sub": str(user_id),
        "exp": expires_at
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )


def decode_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )

        subject = payload.get("sub")

        if subject is None:
            return None

        return int(subject)

    except (
        InvalidTokenError,
        ValueError,
        TypeError
    ):
        return None