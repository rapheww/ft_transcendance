from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from jwt import InvalidTokenError
from backend.core.security import decode_access_token
from backend.db.session import get_db
from backend.exceptions.user import UserNotFound
from backend.models.user import User
from backend.services import user_service

bearer_scheme = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(
    bearer_scheme),
                     db: Session = Depends(get_db)) -> User:
    try:
        payload = decode_access_token(credentials.credentials)

        subject = payload.get("sub")
        token_type = payload.get("type")

        if subject is None or token_type != "access":
            raise ValueError

        user_id = int(subject)

    except (InvalidTokenError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid authentication credentials")

    try:
        return user_service.get_user_by_id(db, user_id)

    except UserNotFound:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid authentication credentials")
