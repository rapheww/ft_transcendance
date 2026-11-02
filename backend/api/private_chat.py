from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.core.dependencies import get_current_user
from backend.db.session import get_db
from backend.exceptions.friend import FriendConflict, FriendshipNotFound
from backend.exceptions.private_chat import PrivateConversationNotFound
from backend.models.private_chat import PrivateConversation, PrivateMessage
from backend.models.user import User
from backend.schemas.friend import FriendUserResponse
from backend.schemas.private_chat import (
    PrivateConversationResponse,
    PrivateMessageCreate,
    PrivateMessagePage,
    PrivateMessageResponse,
)
from backend.services import private_chat_service

router = APIRouter()


def _http_error(error: Exception) -> HTTPException:
    if isinstance(error, (FriendshipNotFound, PrivateConversationNotFound)):
        code = status.HTTP_404_NOT_FOUND
    else:
        code = status.HTTP_409_CONFLICT
    return HTTPException(status_code=code, detail=str(error))


def _conversation_response(
        conversation: PrivateConversation,
        friend: User) -> PrivateConversationResponse:
    return PrivateConversationResponse(
        id=conversation.id,
        friend=FriendUserResponse.model_validate(friend),
        created_at=conversation.created_at,
    )


def _message_response(message: PrivateMessage,
                      sender_username: str) -> PrivateMessageResponse:
    return PrivateMessageResponse(
        id=message.id,
        sender_id=message.sender_id,
        sender_username=sender_username,
        message=message.message,
        created_at=message.created_at,
    )


@router.get("/conversations",
            response_model=list[PrivateConversationResponse])
def list_conversations(current_user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    conversations = private_chat_service.list_conversations(
        db, current_user.id)
    return [
        _conversation_response(conversation, friend)
        for conversation, friend in conversations
    ]


@router.post("/conversations/{friend_id}",
             response_model=PrivateConversationResponse)
def get_or_create_conversation(
        friend_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)):
    try:
        conversation = private_chat_service.get_or_create_conversation(
            db, current_user.id, friend_id)
        friend = db.get(User, friend_id)
        if friend is None:
            raise FriendshipNotFound()
        return _conversation_response(conversation, friend)
    except (FriendConflict, FriendshipNotFound) as error:
        raise _http_error(error) from error
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to open private conversation",
        ) from error


@router.get("/conversations/{conversation_id}/messages",
            response_model=PrivateMessagePage)
def list_messages(
        conversation_id: int,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=50, ge=1, le=100),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)):
    try:
        messages, total = private_chat_service.list_messages(
            db, conversation_id, current_user.id, offset, limit)
        return PrivateMessagePage(
            items=[
                _message_response(message, username)
                for message, username in messages
            ],
            total=total,
            offset=offset,
            limit=limit,
        )
    except PrivateConversationNotFound as error:
        raise _http_error(error) from error


@router.post("/conversations/{conversation_id}/messages",
             response_model=PrivateMessageResponse,
             status_code=status.HTTP_201_CREATED)
def send_message(conversation_id: int,
                 message_data: PrivateMessageCreate,
                 current_user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    try:
        message = private_chat_service.send_message(
            db, conversation_id, current_user.id, message_data.message)
        return _message_response(message, current_user.username)
    except PrivateConversationNotFound as error:
        raise _http_error(error) from error
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to send private message",
        ) from error
