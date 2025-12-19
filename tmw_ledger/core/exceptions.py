"""Module defining custom exceptions for the TMW Ledger."""


class PreconditionFailed(Exception):
    """Exception raised when a precondition for an operation is not met."""

    def __init__(self, message="Precondition failed") -> None:
        super().__init__(message)
