class UserAlreadyExists(Exception):
    "Raised when attempting to create a user that already exists."


class UserNotFound(Exception):
    "Raised when a requested user does not exist."


class InvalidCredentials(Exception):
    "Raised when using invalid credentials."
