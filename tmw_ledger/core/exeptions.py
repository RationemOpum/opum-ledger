"""Module defining custom exceptions for the TMW Ledge."""


class PreconditionFailed(Exception):
    """Exception raised when a precondition for an operation is not met."""

    def __init__(self, message="Precondition failed"):
        super().__init__(message)
