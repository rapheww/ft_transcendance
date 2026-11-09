import logging

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from backend.core.security import decode_access_token
from backend.db.session import SessionLocal
from backend.exceptions.private_chat import PrivateConversationNotFound
from backend.models.private_chat import PrivateConversation
from backend.models.user import User
from backend.schemas.private_chat import PrivateMessageCreate
from backend.services import private_chat_service
from backend.websocket.private_chat_manager import private_chat_manager

router = APIRouter()
logger = logging.getLogger(__name__)


def _participant_ids(conversation: PrivateConversation) -> tuple[int, int]:
    return conversation.user_low_id, conversation.user_high_id


@router.websocket("/private-chat/{conversation_id}")
async def private_chat_websocket(websocket: WebSocket, conversation_id: int):
    token = websocket.query_params.get("token")
    if token is None:
        await websocket.close(code=1008)
        return

    try:
        payload = decode_access_token(token)
        if payload.get("type") != "access":
            await websocket.close(code=1008)
            return
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError, TypeError):
        await websocket.close(code=1008)
        return

    try:
        with SessionLocal() as db:
            conversation = private_chat_service.get_accessible_conversation(
                db, conversation_id, user_id)
            participant_ids = _participant_ids(conversation)
    except PrivateConversationNotFound:
        await websocket.close(code=1008)
        return
    except SQLAlchemyError:
        logger.exception("Unable to authorize private chat connection")
        await websocket.close(code=1011)
        return

    connected = False
    try:
        await private_chat_manager.connect(conversation_id, user_id,
                                           websocket)
        connected = True
        await websocket.send_json({
            "type": "private_chat_connected",
            "conversation_id": conversation_id,
        })

        while True:
            invalid_json = False
            try:
                data = await websocket.receive_json()
            except ValueError:
                data = None
                invalid_json = True

            try:
                with SessionLocal() as db:
                    db.expire_all()
                    conversation = (
                        private_chat_service.get_accessible_conversation(
                            db, conversation_id, user_id))
                    participant_ids = _participant_ids(conversation)

                    if invalid_json:
                        await websocket.send_json({
                            "type": "error",
                            "code": "invalid_json",
                            "message": "Invalid JSON",
                        })
                        continue

                    if not isinstance(data, dict):
                        await websocket.send_json({
                            "type": "error",
                            "code": "invalid_event",
                            "message": "Invalid event",
                        })
                        continue

                    event_type = data.get("type")
                    if event_type == "ping":
                        await websocket.send_json({"type": "pong"})
                        continue
                    if event_type != "message":
                        await websocket.send_json({
                            "type": "error",
                            "code": "invalid_event",
                            "message": "Unsupported private chat event",
                        })
                        continue

                    try:
                        message_data = PrivateMessageCreate.model_validate(data)
                    except ValidationError as error:
                        await websocket.send_json({
                            "type": "error",
                            "code": "invalid_message",
                            "message": error.errors()[0]["msg"],
                        })
                        continue

                    message = private_chat_service.send_message(
                        db, conversation_id, user_id, message_data.message)
                    sender = db.get(User, user_id)
                    if sender is None:
                        await websocket.close(code=1008)
                        return
                    event = {
                        "type": "private_message",
                        "id": message.id,
                        "conversation_id": conversation_id,
                        "sender_id": user_id,
                        "sender_username": sender.username,
                        "message": message.message,
                        "created_at": message.created_at.isoformat(),
                    }
            except PrivateConversationNotFound:
                await websocket.close(code=1008)
                return
            except SQLAlchemyError:
                logger.exception(
                    "Unable to process message in private conversation %s",
                    conversation_id)
                await websocket.send_json({
                    "type": "error",
                    "code": "server_error",
                    "message": "Unable to send private message",
                })
                continue

            await private_chat_manager.send_to_conversation(
                conversation_id, participant_ids, event)

    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        if connected:
            private_chat_manager.disconnect(conversation_id, user_id,
                                            websocket)
