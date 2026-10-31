from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session

from backend.models.friendship import Friendship
from backend.models.private_chat import PrivateConversation, PrivateMessage
from backend.models.user import User


class PrivateChatRepository:

    def __init__(self, db: Session):
        self.db = db

    def list_conversations(self, user_id: int) -> list[
            tuple[PrivateConversation, User]]:
        other_user_id = case(
            (PrivateConversation.user_low_id == user_id,
             PrivateConversation.user_high_id),
            else_=PrivateConversation.user_low_id,
        )
        statement = (select(PrivateConversation, User).join(
            User, User.id == other_user_id).join(
                Friendship,
                and_(
                    Friendship.user_low_id ==
                    PrivateConversation.user_low_id,
                    Friendship.user_high_id ==
                    PrivateConversation.user_high_id,
                )).where(
                    or_(
                        PrivateConversation.user_low_id == user_id,
                        PrivateConversation.user_high_id == user_id,
                    )).order_by(
                        PrivateConversation.created_at.desc(),
                        PrivateConversation.id.desc()))
        return list(self.db.execute(statement))

    def get_conversation_for_pair(
            self, user_a: int,
            user_b: int) -> PrivateConversation | None:
        low_id, high_id = sorted((user_a, user_b))
        statement = select(PrivateConversation).where(
            PrivateConversation.user_low_id == low_id,
            PrivateConversation.user_high_id == high_id,
        )
        return self.db.scalar(statement)

    def create_conversation(self, user_a: int,
                            user_b: int) -> PrivateConversation:
        low_id, high_id = sorted((user_a, user_b))
        conversation = PrivateConversation(user_low_id=low_id,
                                          user_high_id=high_id)
        self.db.add(conversation)
        self.db.flush()
        return conversation

    def get_accessible_conversation(
            self, conversation_id: int,
            user_id: int) -> PrivateConversation | None:
        statement = (select(PrivateConversation).join(
            Friendship,
            and_(
                Friendship.user_low_id == PrivateConversation.user_low_id,
                Friendship.user_high_id ==
                PrivateConversation.user_high_id,
            )).where(
                PrivateConversation.id == conversation_id,
                or_(
                    PrivateConversation.user_low_id == user_id,
                    PrivateConversation.user_high_id == user_id,
                )))
        return self.db.scalar(statement)

    def list_messages(
            self, conversation_id: int, offset: int,
            limit: int) -> tuple[list[tuple[PrivateMessage, str]], int]:
        statement = (select(PrivateMessage, User.username).join(
            User, User.id == PrivateMessage.sender_id).where(
                PrivateMessage.conversation_id == conversation_id).order_by(
                    PrivateMessage.created_at,
                    PrivateMessage.id).offset(offset).limit(limit))
        messages = list(self.db.execute(statement))
        count_statement = select(func.count()).select_from(
            PrivateMessage).where(
                PrivateMessage.conversation_id == conversation_id)
        total = self.db.scalar(count_statement)
        return messages, total or 0

    def create_message(self, conversation_id: int, sender_id: int,
                       message: str) -> PrivateMessage:
        private_message = PrivateMessage(conversation_id=conversation_id,
                                         sender_id=sender_id,
                                         message=message)
        self.db.add(private_message)
        self.db.flush()
        return private_message
