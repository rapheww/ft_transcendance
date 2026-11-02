from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class FriendUserResponse(BaseModel):
    id: int
    username: str
    avatar: str

    model_config = {"from_attributes": True}


class FriendPresenceResponse(FriendUserResponse):
    online: bool


class FriendRequestResponse(FriendUserResponse):
    requested_at: datetime
    status: Literal["pending"] = "pending"


class FriendRequestResult(BaseModel):
    user: FriendUserResponse
    status: Literal["pending", "accepted"]
