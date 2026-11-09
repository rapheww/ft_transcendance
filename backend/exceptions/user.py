class UserAlreadyExists(Exception):
    """Raised when attempting to create a user that already exists."""

    def __init__(self, message: str = "User already exists"):
        super().__init__(message)


class UserNotFound(Exception):
    """Raised when a requested user does not exist."""

    def __init__(self, message: str = "User not found"):
        super().__init__(message)


class InvalidCredentials(Exception):
    """Raised when using invalid credentials."""

    def __init__(self, message: str = "Invalid username or password"):
        super().__init__(message)
