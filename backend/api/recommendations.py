from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Annotated

from backend.models.user import User
from backend.db.session import get_db
from backend.schemas.recommendation import ResponseRecommendation
from backend.services.recommendation_service import get_opponent_recommendations
from backend.core.dependencies import get_current_user

router = APIRouter()

@router.get("/opponents", response_model=ResponseRecommendation)

def recommend_opponents(current_user: Annotated[User, Depends(get_current_user)],
                        db: Annotated[Session, Depends(get_db)],
                        top_n: Annotated[int, Query(ge=1, le=20)] = 5,):
    
    recommendations = get_opponent_recommendations(
        db=db,
        user_id=current_user.id,
        top_n=top_n,
    )

    return recommendations
