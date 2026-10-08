class MatchmakingException(Exception):
    pass


class AlreadyInMatchmaking(MatchmakingException):

    def __init__(self):
        super().__init__("User is already in the matchmaking queue")


class NotInMatchmaking(MatchmakingException):

    def __init__(self):
        super().__init__("User is not in the matchmaking queue")


class NoMatchFound(MatchmakingException):

    def __init__(self):
        super().__init__("No compatible opponent found")
