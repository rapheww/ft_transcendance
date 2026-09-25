class GameCreationError(Exception):
    """Raised when a game cannot be created."""


class GameNotFound(Exception):
    """Raised when a game doesn't exist."""

    def __init__(self, message: str = "Game not found"):
        super().__init__(message)


class GameNotJoinable(Exception):
    """Raised when user can't join game."""

    def __init__(self, message: str = "Game is not joinable"):
        super().__init__(message)


class CannotPlayAgainstSelf(Exception):
    """Raised when user joins his own game."""

    def __init__(self, message: str = "Cannot play against yourself"):
        super().__init__(message)
