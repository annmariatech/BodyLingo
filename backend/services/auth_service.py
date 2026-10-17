"""Password hashing and signed access-token helpers."""

import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from fastapi import HTTPException, status
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, encoded_hash: str) -> bool:
    return password_hash.verify(password, encoded_hash)


def token_lifetime_seconds() -> int:
    try:
        minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    except ValueError as exc:
        raise HTTPException(status_code=500, detail="Invalid token lifetime configuration") from exc
    if not 1 <= minutes <= 1440:
        raise HTTPException(status_code=500, detail="Invalid token lifetime configuration")
    return minutes * 60


def jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET_KEY", "")
    if len(secret) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured",
        )
    return secret


def create_access_token(user_id: str) -> tuple[str, str, datetime]:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=token_lifetime_seconds())
    token_id = str(uuid4())
    token = jwt.encode(
        {"sub": user_id, "jti": token_id, "iat": now, "exp": expires_at, "iss": "bodylingo"},
        jwt_secret(),
        algorithm="HS256",
    )
    return token, token_id, expires_at


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, jwt_secret(), algorithms=["HS256"], issuer="bodylingo")
