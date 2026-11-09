from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.core.security import create_access_token
from backend.core.security import create_refresh_token, decode_refresh_token
from backend.schemas.auth import TokenWithRefresh, RefreshRequest
from backend.db.session import get_db
from backend.exceptions.user import InvalidCredentials
from backend.schemas.auth import Token
from backend.schemas.user import UserLogin
from backend.services import user_service

router = APIRouter()


@router.post("/login", response_model=TokenWithRefresh)
def login(
        user: UserLogin,
        db: Session = Depends(get_db),
):
    try:
        authenticated_user = user_service.authenticate_user(
            db, user.username, user.password)

        access_token = create_access_token(str(authenticated_user.id))
        refresh_token = create_refresh_token(str(authenticated_user.id))

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token,
        }

    except InvalidCredentials as error:
        raise HTTPException(status_code=401, detail=str(error))


@router.post("/refresh", response_model=TokenWithRefresh)
def refresh_token(payload: RefreshRequest):
    try:
        token = payload.refresh_token
        data = decode_refresh_token(token)
        if data.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="invalid token")
        user_id = str(data["sub"])
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)
        return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}
    except Exception:
        raise HTTPException(status_code=401, detail="invalid refresh token")
