from sqlalchemy import and_, case, or_, select
from sqlalchemy.orm import Session

from backend.models.friend_request import FriendRequest
from backend.models.friendship import Friendship
from backend.models.user import User


class FriendRepository:

    def __init__(self, db: Session):
        self.db = db

    def search_users(self, user_id: int, query: str,
                     limit: int) -> list[User]:
        statement = (select(User).where(
            User.id != user_id,
            User.username.ilike(f"%{query}%"),
        ).order_by(User.username).limit(limit))
        return list(self.db.scalars(statement))

    def get_friend_request_for_update(self, user_a: int,
                                     user_b: int) -> FriendRequest | None:
        low_id, high_id = sorted((user_a, user_b))
        statement = (select(FriendRequest).where(
            FriendRequest.user_low_id == low_id,
            FriendRequest.user_high_id == high_id).with_for_update())
        return self.db.scalar(statement)

    def create_friend_request(self,
                              request: FriendRequest) -> FriendRequest:
        self.db.add(request)
        self.db.flush()
        return request

    def get_friendship(self, user_a: int,
                       user_b: int) -> Friendship | None:
        low_id, high_id = sorted((user_a, user_b))
        return self.db.get(Friendship, (low_id, high_id))

    def list_friends(self, user_id: int) -> list[User]:
        statement = (select(User).join(
            Friendship,
            or_(
                and_(Friendship.user_low_id == user_id,
                     Friendship.user_high_id == User.id),
                and_(Friendship.user_high_id == user_id,
                     Friendship.user_low_id == User.id),
            )).order_by(User.username))
        return list(self.db.scalars(statement))

    def list_requests(self, user_id: int, *, incoming: bool) -> list[tuple[
            FriendRequest, User]]:
        other_id = (FriendRequest.requested_by_id if incoming else case(
            (FriendRequest.user_low_id == user_id,
             FriendRequest.user_high_id),
            else_=FriendRequest.user_low_id))
        statement = (select(FriendRequest, User).join(User, User.id == other_id)
                     .where(FriendRequest.status == "pending"))
        if incoming:
            statement = statement.where(
                FriendRequest.requested_by_id != user_id,
                or_(FriendRequest.user_low_id == user_id,
                    FriendRequest.user_high_id == user_id))
        else:
            statement = statement.where(
                FriendRequest.requested_by_id == user_id,
                or_(FriendRequest.user_low_id == user_id,
                    FriendRequest.user_high_id == user_id))
        return list(self.db.execute(statement.order_by(
            FriendRequest.requested_at.desc())))

    def delete_friend_request(self, request: FriendRequest) -> None:
        self.db.delete(request)
        self.db.flush()

    def create_friendship(self, friendship: Friendship) -> Friendship:
        self.db.add(friendship)
        self.db.flush()
        return friendship

    def delete_friendship(self, friendship: Friendship) -> None:
        self.db.delete(friendship)
        self.db.flush()
