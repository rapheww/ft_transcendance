class FriendConflict(Exception):
    """Raised when a friendship or request conflicts with existing state."""


class FriendRequestNotFound(Exception):
    """Raised when a pending incoming request does not exist."""


class FriendshipNotFound(Exception):
    """Raised when a friendship does not exist."""


class InvalidFriendRequest(Exception):
    """Raised when a request action is not valid for the current user."""


class SelfFriendRequest(Exception):
    """Raised when a user attempts to friend themselves."""
