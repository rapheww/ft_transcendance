from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.exceptions.friend import (FriendConflict,
                                       FriendRequestNotFound,
                                       FriendshipNotFound,
                                       InvalidFriendRequest,
                                       SelfFriendRequest)
from backend.exceptions.user import UserNotFound
from backend.models.friend_request import FriendRequest
from backend.models.friendship import Friendship
from backend.models.user import User
from backend.repositories.friend_repository import FriendRepository
from backend.repositories import user_repository


def _ordered_pair(user_a: int, user_b: int) -> tuple[int, int]:
    low_id, high_id = sorted((user_a, user_b))
    return low_id, high_id


def search_users(db: Session, user_id: int, query: str,
                 limit: int = 20) -> list[User]:
    normalized_query = query.strip()
    if not normalized_query:
        return []
    return FriendRepository(db).search_users(user_id, normalized_query, limit)


def list_friends(db: Session, user_id: int) -> list[User]:
    return FriendRepository(db).list_friends(user_id)


def list_incoming_requests(db: Session, user_id: int) -> list[
        tuple[FriendRequest, User]]:
    return FriendRepository(db).list_requests(user_id, incoming=True)


def list_outgoing_requests(db: Session, user_id: int) -> list[
        tuple[FriendRequest, User]]:
    return FriendRepository(db).list_requests(user_id, incoming=False)


def send_friend_request(db: Session, sender_id: int,
                        recipient_id: int) -> tuple[User, str]:
    try:
        if sender_id == recipient_id:
            raise SelfFriendRequest()

        recipient = user_repository.get_by_id(db, recipient_id)
        if recipient is None:
            raise UserNotFound()

        repository = FriendRepository(db)
        if repository.get_friendship(sender_id, recipient_id) is not None:
            raise FriendConflict("You are already friends")

        request = repository.get_friend_request_for_update(
            sender_id, recipient_id)
        if request is not None and request.status == "pending":
            if request.requested_by_id == sender_id:
                raise FriendConflict("Friend request already sent")

            low_id, high_id = _ordered_pair(sender_id, recipient_id)
            repository.create_friendship(
                Friendship(user_low_id=low_id, user_high_id=high_id))
            repository.delete_friend_request(request)
            db.commit()
            return recipient, "accepted"

        if request is None:
            low_id, high_id = _ordered_pair(sender_id, recipient_id)
            request = FriendRequest(user_low_id=low_id,
                                    user_high_id=high_id,
                                    requested_by_id=sender_id)
            repository.create_friend_request(request)
        else:
            request.requested_by_id = sender_id
            request.status = "pending"
            request.requested_at = datetime.now(timezone.utc)
            request.responded_at = None

        db.commit()
        return recipient, "pending"

    except IntegrityError as error:
        db.rollback()
        raise FriendConflict() from error
    except Exception:
        db.rollback()
        raise


def _respond_to_request(db: Session, recipient_id: int, requester_id: int,
                         *, accept: bool) -> User:
    try:
        if recipient_id == requester_id:
            raise SelfFriendRequest(
                "You cannot respond to your own friend request")

        requester = user_repository.get_by_id(db, requester_id)
        if requester is None:
            raise UserNotFound()

        repository = FriendRepository(db)
        request = repository.get_friend_request_for_update(
            recipient_id, requester_id)
        if request is None or request.status != "pending":
            raise FriendRequestNotFound()
        if request.requested_by_id != requester_id:
            raise InvalidFriendRequest()

        if accept:
            low_id, high_id = _ordered_pair(recipient_id, requester_id)
            repository.create_friendship(
                Friendship(user_low_id=low_id, user_high_id=high_id))
            repository.delete_friend_request(request)
        else:
            request.status = "rejected"
            request.responded_at = datetime.now(timezone.utc)

        db.commit()
        return requester

    except IntegrityError as error:
        db.rollback()
        raise FriendConflict() from error
    except Exception:
        db.rollback()
        raise


def accept_friend_request(db: Session, recipient_id: int,
                          requester_id: int) -> User:
    return _respond_to_request(db, recipient_id, requester_id, accept=True)


def reject_friend_request(db: Session, recipient_id: int,
                          requester_id: int) -> User:
    return _respond_to_request(db, recipient_id, requester_id, accept=False)


def remove_friend(db: Session, user_id: int, friend_id: int) -> None:
    try:
        if user_id == friend_id:
            raise FriendConflict("You cannot remove yourself as a friend")

        repository = FriendRepository(db)
        friendship = repository.get_friendship(user_id, friend_id)
        if friendship is None:
            raise FriendshipNotFound()

        repository.delete_friendship(friendship)
        db.commit()
    except Exception:
        db.rollback()
        raise
