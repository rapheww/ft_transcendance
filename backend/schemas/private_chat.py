from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, StringConstraints

from backend.schemas.friend import FriendUserResponse


PrivateMessageText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=500),
]


class PrivateConversationResponse(BaseModel):
    id: int
    friend: FriendUserResponse
    created_at: datetime


class PrivateMessageCreate(BaseModel):
    message: PrivateMessageText


class PrivateMessageResponse(BaseModel):
    id: int
    sender_id: int
    sender_username: str
    message: str
    created_at: datetime


class PrivateMessagePage(BaseModel):
    items: list[PrivateMessageResponse]
    total: int
    offset: int
    limit: int
