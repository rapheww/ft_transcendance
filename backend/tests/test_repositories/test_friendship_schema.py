import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.models.friend_request import FriendRequest
from backend.models.friendship import Friendship
from backend.models.private_chat import PrivateConversation, PrivateMessage
from backend.models.user import User


def test_friend_request_constraints_and_chat_cascade(db: Session):
    first_user = User(username="alice",
                      email="alice@example.com",
                      password_hash="test-password-hash")
    second_user = User(username="bob",
                       email="bob@example.com",
                       password_hash="test-password-hash")
    db.add_all([first_user, second_user])
    db.flush()

    low_id, high_id = sorted([first_user.id, second_user.id])
    request = FriendRequest(user_low_id=low_id,
                            user_high_id=high_id,
                            requested_by_id=first_user.id)
    db.add(request)
    db.commit()

    db.expunge(request)
    db.add(FriendRequest(user_low_id=low_id,
                         user_high_id=high_id,
                         requested_by_id=second_user.id))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()

    db.add(FriendRequest(user_low_id=high_id,
                         user_high_id=low_id,
                         requested_by_id=second_user.id))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()

    db.add(FriendRequest(user_low_id=first_user.id,
                         user_high_id=first_user.id,
                         requested_by_id=first_user.id))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()

    db.add(FriendRequest(user_low_id=low_id,
                         user_high_id=high_id,
                         requested_by_id=999999))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()

    request = db.get(FriendRequest, (low_id, high_id))
    assert request is not None
    assert request.status == "pending"
    request.status = "rejected"
    db.commit()
    request.status = "pending"
    request.requested_by_id = second_user.id
    request.responded_at = None
    db.commit()
    assert request.status == "pending"
    assert request.requested_by_id == second_user.id

    db.delete(request)

    friendship = Friendship(user_low_id=low_id, user_high_id=high_id)
    db.add(friendship)
    db.commit()

    friendship = db.get(Friendship, (low_id, high_id))
    assert friendship is not None
    conversation = PrivateConversation(user_low_id=low_id,
                                      user_high_id=high_id)
    db.add(conversation)
    db.flush()
    db.add(PrivateMessage(conversation_id=conversation.id,
                          sender_id=low_id,
                          message="Persistent private message"))
    db.commit()

    db.delete(friendship)
    db.commit()

    assert db.scalar(select(func.count()).select_from(PrivateConversation)) == 0
    assert db.scalar(select(func.count()).select_from(PrivateMessage)) == 0
