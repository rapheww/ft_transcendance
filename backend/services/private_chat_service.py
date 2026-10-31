from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.exceptions.friend import FriendConflict, FriendshipNotFound
from backend.exceptions.private_chat import PrivateConversationNotFound
from backend.models.private_chat import PrivateConversation, PrivateMessage
from backend.models.user import User
from backend.repositories.friend_repository import FriendRepository
from backend.repositories.private_chat_repository import PrivateChatRepository


def list_conversations(
        db: Session,
        user_id: int) -> list[tuple[PrivateConversation, User]]:
    return PrivateChatRepository(db).list_conversations(user_id)


def get_or_create_conversation(db: Session, user_id: int,
                               friend_id: int) -> PrivateConversation:
    friends = FriendRepository(db)
    if friends.get_friendship(user_id, friend_id) is None:
        raise FriendshipNotFound()

    repository = PrivateChatRepository(db)
    conversation = repository.get_conversation_for_pair(user_id, friend_id)
    if conversation is not None:
        return conversation

    try:
        conversation = repository.create_conversation(user_id, friend_id)
        db.commit()
        db.refresh(conversation)
        return conversation
    except IntegrityError as error:
        db.rollback()
        conversation = repository.get_conversation_for_pair(
            user_id, friend_id)
        if conversation is not None:
            return conversation
        raise FriendConflict() from error


def _get_accessible_conversation(
        repository: PrivateChatRepository, conversation_id: int,
        user_id: int) -> PrivateConversation:
    conversation = repository.get_accessible_conversation(
        conversation_id, user_id)
    if conversation is None:
        raise PrivateConversationNotFound()
    return conversation


def get_accessible_conversation(
        db: Session, conversation_id: int,
        user_id: int) -> PrivateConversation:
    return _get_accessible_conversation(PrivateChatRepository(db),
                                        conversation_id, user_id)


def list_messages(
        db: Session, conversation_id: int, user_id: int, offset: int,
        limit: int) -> tuple[list[tuple[PrivateMessage, str]], int]:
    repository = PrivateChatRepository(db)
    _get_accessible_conversation(repository, conversation_id, user_id)
    return repository.list_messages(conversation_id, offset, limit)


def send_message(db: Session, conversation_id: int, sender_id: int,
                 message: str) -> PrivateMessage:
    repository = PrivateChatRepository(db)
    _get_accessible_conversation(repository, conversation_id, sender_id)
    try:
        private_message = repository.create_message(
            conversation_id, sender_id, message)
        db.commit()
        db.refresh(private_message)
        return private_message
    except SQLAlchemyError:
        db.rollback()
        raise
