class PrivateConversationNotFound(Exception):
    """Raised when a conversation does not exist or is not accessible."""

    def __init__(self,
                 message: str = "Private conversation not found"):
        super().__init__(message)
