class TournamentNotFound(Exception):
    """Raised when a tournament doesn't exist."""

    def __init__(self, message: str = "Tournament not found"):
        super().__init__(message)


class TournamentAlreadyStarted(Exception):
    """Raised when trying to register for or start a tournament that has already started."""

    def __init__(self, message: str = "Tournament has already started"):
        super().__init__(message)


class AlreadyRegistered(Exception):
    """Raised when a user tries to register twice for the same tournament."""

    def __init__(self,
                 message: str = "Already registered for this tournament"):
        super().__init__(message)


class NotRegistered(Exception):
    """Raised when a user who isn't registered tries to start the tournament."""

    def __init__(self,
                 message: str = "You are not registered for this tournament"):
        super().__init__(message)


class InvalidParticipantCount(Exception):
    """Raised when the tournament doesn't have a bracket-friendly number of participants."""

    def __init__(
        self,
        message:
        str = "At least two participants are required"):
        super().__init__(message)


class NotTournamentOrganizer(Exception):
    def __init__(self):
        super().__init__("Only the tournament organizer can perform this action")


class TournamentExpired(Exception):
    def __init__(self):
        super().__init__("Tournament registration has expired")


class PlayerUnavailable(Exception):
    def __init__(self):
        super().__init__("Player is already in a tournament, matchmaking or an unfinished game")
