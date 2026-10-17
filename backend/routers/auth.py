"""Registration, sign-in, current profile, and logout endpoints."""

from datetime import datetime, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from dependencies.auth import CurrentUser
from models.user import RevokedToken, User
from schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserResponse
from services.auth_service import (
    create_access_token,
    hash_password,
    token_lifetime_seconds,
    verify_password,
)
from services.auth_service import decode_access_token, jwt_secret

router = APIRouter(prefix="/auth", tags=["authentication"])


def _auth_response(user: User) -> AuthResponse:
    token, _, _ = create_access_token(user.id)
    return AuthResponse(
        access_token=token,
        expires_in=token_lifetime_seconds(),
        user=UserResponse.model_validate(user),
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    jwt_secret()
    token_lifetime_seconds()
    normalized_email = str(payload.email).strip().lower()
    normalized_username = payload.username.strip()
    existing = db.scalar(
        select(User).where(
            (func.lower(User.email) == normalized_email)
            | (func.lower(User.username) == normalized_username.lower())
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="Username or email is already registered")

    user = User(
        username=normalized_username,
        email=normalized_email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username or email is already registered") from None
    return _auth_response(user)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    jwt_secret()
    token_lifetime_seconds()
    identifier = payload.identifier.strip()
    user = db.scalar(
        select(User).where(
            (func.lower(User.email) == identifier.lower())
            | (func.lower(User.username) == identifier.lower())
        )
    )
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username/email or password")
    return _auth_response(user)


@router.get("/me", response_model=UserResponse)
def current_profile(user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    user: CurrentUser,
    db: Session = Depends(get_db),
) -> Response:
    """Revoke the presented bearer token so it stops authorizing requests."""
    del user  # Its presence enforces verification and user lookup above.
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    try:
        claims = decode_access_token(token)
        token_id = claims["jti"]
        expires_at = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid authentication token") from None

    if db.get(RevokedToken, token_id) is None:
        db.add(
            RevokedToken(
                jti=token_id,
                user_id=claims["sub"],
                expires_at=expires_at,
            )
        )
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
