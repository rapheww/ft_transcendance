from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.core.security import create_access_token
from backend.db.session import get_db
from backend.exceptions.user import InvalidCredentials
from backend.schemas.auth import Token
from backend.schemas.user import UserLogin
from backend.services import user_service

router = APIRouter()


@router.post("/login", response_model=Token)
def login(
        user: UserLogin,
        db: Session = Depends(get_db),
):
    try:
        authenticated_user = user_service.authenticate_user(
            db, user.username, user.password)

        access_token = create_access_token(str(authenticated_user.id))

        return {"access_token": access_token, "token_type": "bearer"}

    except InvalidCredentials as error:
        raise HTTPException(status_code=401, detail=str(error))
