import hashlib
import hmac
import os
import secrets

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

EMAIL_VERIFICATION_SECRET = os.getenv(
    "EMAIL_VERIFICATION_SECRET"
)

PASSWORD_RESET_SECRET = os.getenv(
    "PASSWORD_RESET_SECRET"
)

if not JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET is missing from the .env file"
    )

if not EMAIL_VERIFICATION_SECRET:
    raise RuntimeError(
        "EMAIL_VERIFICATION_SECRET is missing "
        "from the .env file"
    )
if not PASSWORD_RESET_SECRET:
    raise RuntimeError(
        "PASSWORD_RESET_SECRET is missing "
        "from the .env file"
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

def generate_email_verification_code():
    code = (
        secrets.randbelow(900000)
        + 100000
    )

    return str(code)


def hash_email_verification_code(
    email: str,
    code: str
):
    message = (
        f"{email.lower()}:{code}"
    ).encode("utf-8")

    return hmac.new(
        EMAIL_VERIFICATION_SECRET.encode(
            "utf-8"
        ),
        message,
        hashlib.sha256
    ).hexdigest()


def verify_email_verification_code(
    email: str,
    code: str,
    expected_hash: str
):
    provided_hash = (
        hash_email_verification_code(
            email,
            code
        )
    )

    return hmac.compare_digest(
        provided_hash,
        expected_hash
    )
def generate_password_reset_code():
    code = (
        secrets.randbelow(900000)
        + 100000
    )

    return str(code)


def hash_password_reset_code(
    email: str,
    code: str
):
    message = (
        f"{email.lower()}:{code}"
    ).encode("utf-8")

    return hmac.new(
        PASSWORD_RESET_SECRET.encode(
            "utf-8"
        ),
        message,
        hashlib.sha256
    ).hexdigest()


def verify_password_reset_code(
    email: str,
    code: str,
    expected_hash: str
):
    provided_hash = (
        hash_password_reset_code(
            email,
            code
        )
    )

    return hmac.compare_digest(
        provided_hash,
        expected_hash
    )