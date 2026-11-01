class FriendConflict(Exception):
    """Raised when a friendship or request conflicts with existing state."""

    def __init__(self,
                 message: str = "Friend request conflicts with existing state"):
        super().__init__(message)


class FriendRequestNotFound(Exception):
    """Raised when a pending incoming request does not exist."""

    def __init__(self, message: str = "Incoming friend request not found"):
        super().__init__(message)


class FriendshipNotFound(Exception):
    """Raised when a friendship does not exist."""

    def __init__(self, message: str = "Friendship not found"):
        super().__init__(message)


class InvalidFriendRequest(Exception):
    """Raised when a request action is not valid for the current user."""

    def __init__(self,
                 message: str =
                 "You can only respond to an incoming friend request"):
        super().__init__(message)


class SelfFriendRequest(Exception):
    """Raised when a user attempts to friend themselves."""

    def __init__(
            self,
            message: str = "You cannot send a friend request to yourself"):
        super().__init__(message)
