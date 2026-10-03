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


class GameNotActive(Exception):
    """Raised when a move is attempted on a game that isn't active."""

    def __init__(self, message: str = "Game is not active"):
        super().__init__(message)


class NotAPlayer(Exception):
    """Raised when a user attempts to play a game they aren't part of."""

    def __init__(self, message: str = "User is not a player in this game"):
        super().__init__(message)


class NotYourTurn(Exception):
    """Raised when a player attempts to move out of turn."""

    def __init__(self, message: str = "It is not your turn"):
        super().__init__(message)


class IllegalMove(Exception):
    """Raised when a chess move is illegal."""

    def __init__(self, message: str = "Illegal move"):
        super().__init__(message)


class CannotResignFinishedGame(Exception):
    """Raised when trying to resign a finished game."""

    def __init__(self, message: str = "Game is already finished"):
        super().__init__(message)


class DrawOfferAlreadyExists(Exception):
    """Raised when a game already has a pending draw offer."""

    def __init__(self, message: str = "A draw offer is already pending"):
        super().__init__(message)


class NoDrawOffer(Exception):
    """Raised when there is no pending draw offer."""

    def __init__(self, message: str = "There is no pending draw offer"):
        super().__init__(message)


class CannotAcceptOwnDrawOffer(Exception):
    """Raised when a player tries to accept their own draw offer."""

    def __init__(self, message: str = "Cannot accept your own draw offer"):
        super().__init__(message)


class DrawNotClaimable(Exception):
    """Raised when a requested draw claim is not currently valid."""

    def __init__(self, message: str = "Draw cannot be claimed"):
        super().__init__(message)
