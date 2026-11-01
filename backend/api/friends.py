from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.core.dependencies import get_current_user
from backend.db.session import get_db
from backend.exceptions.friend import (FriendConflict,
                                       FriendRequestNotFound,
                                       FriendshipNotFound,
                                       InvalidFriendRequest,
                                       SelfFriendRequest)
from backend.exceptions.user import UserNotFound
from backend.models.friend_request import FriendRequest
from backend.models.user import User
from backend.schemas.friend import (FriendRequestResponse,
                                    FriendRequestResult,
                                    FriendUserResponse)
from backend.services import friend_service

router = APIRouter()


def _http_error(error: Exception) -> HTTPException:
    if isinstance(error, (UserNotFound, FriendRequestNotFound,
                          FriendshipNotFound)):
        code = status.HTTP_404_NOT_FOUND
    elif isinstance(error, SelfFriendRequest):
        code = status.HTTP_422_UNPROCESSABLE_CONTENT
    elif isinstance(error, InvalidFriendRequest):
        code = status.HTTP_403_FORBIDDEN
    else:
        code = status.HTTP_409_CONFLICT
    return HTTPException(status_code=code, detail=str(error))


def _request_responses(
        requests: list[tuple[FriendRequest, User]]
        ) -> list[FriendRequestResponse]:
    return [
        FriendRequestResponse(id=user.id,
                              username=user.username,
                              avatar=user.avatar,
                              requested_at=request.requested_at)
        for request, user in requests
    ]


@router.get("/search", response_model=list[FriendUserResponse])
def search_users(query: str = Query(min_length=2, max_length=50),
                 current_user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    return friend_service.search_users(db, current_user.id, query)


@router.post("/requests/{user_id}", response_model=FriendRequestResult)
def send_friend_request(user_id: int,
                        current_user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    try:
        user, request_status = friend_service.send_friend_request(
            db, current_user.id, user_id)
        return FriendRequestResult(user=user, status=request_status)
    except (FriendConflict, SelfFriendRequest, UserNotFound) as error:
        raise _http_error(error) from error


@router.get("/requests/incoming",
            response_model=list[FriendRequestResponse])
def list_incoming_requests(current_user: User = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    return _request_responses(
        friend_service.list_incoming_requests(db, current_user.id))


@router.get("/requests/outgoing",
            response_model=list[FriendRequestResponse])
def list_outgoing_requests(current_user: User = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    return _request_responses(
        friend_service.list_outgoing_requests(db, current_user.id))


@router.post("/requests/{user_id}/accept",
             response_model=FriendUserResponse)
def accept_friend_request(user_id: int,
                          current_user: User = Depends(get_current_user),
                          db: Session = Depends(get_db)):
    try:
        return friend_service.accept_friend_request(db, current_user.id,
                                                    user_id)
    except (FriendConflict, FriendRequestNotFound, InvalidFriendRequest,
            SelfFriendRequest, UserNotFound) as error:
        raise _http_error(error) from error


@router.post("/requests/{user_id}/reject",
             response_model=FriendUserResponse)
def reject_friend_request(user_id: int,
                          current_user: User = Depends(get_current_user),
                          db: Session = Depends(get_db)):
    try:
        return friend_service.reject_friend_request(db, current_user.id,
                                                    user_id)
    except (FriendConflict, FriendRequestNotFound, InvalidFriendRequest,
            SelfFriendRequest, UserNotFound) as error:
        raise _http_error(error) from error


@router.get("/", response_model=list[FriendUserResponse])
def list_friends(current_user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    return friend_service.list_friends(db, current_user.id)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_friend(user_id: int,
                  current_user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    try:
        friend_service.remove_friend(db, current_user.id, user_id)
    except (FriendConflict, FriendshipNotFound) as error:
        raise _http_error(error) from error
