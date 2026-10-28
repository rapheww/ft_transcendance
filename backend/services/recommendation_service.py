from sqlalchemy.orm import Session

from backend.models.user import User
from backend.ml.recommender import recommend_with_rules

def user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()

def get_opponent_recommendations(db: Session, user_id: int, top_n: int=5) -> dict[str, list[dict]] | None:

    recommendations = recommend_with_rules(db, user_id, top_n)

    if recommendations is None:
        return None

    for category in ("humans", "bots"):

        formatted = []
        for candidate in recommendations[category]:
            user = user_by_id(db, candidate["user_id"])
            if user is None:
                continue
            candidate["username"] = user.username
            candidate["elo"] = user.elo
            candidate["is_bot"] = user.is_bot
            formatted.append(candidate)
        recommendations[category] = formatted
        
    return recommendations
