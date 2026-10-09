import jwt
from datetime import datetime, timedelta, timezone
from backend.core.config import settings


def create_access_token(subject: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes)

    payload = {"sub": subject, "exp": expires_at, "type": "access"}

    return jwt.encode(payload,
                      settings.jwt_secret_key.get_secret_value(),
                      algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token,
                      settings.jwt_secret_key.get_secret_value(),
                      algorithms=[settings.jwt_algorithm],
                      options={"require": ["sub", "exp", "type"]})
