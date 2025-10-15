"""Base model for all application models."""

from datetime import datetime, timezone

from beanie import Document


class BaseAppModel(Document):
    """Base model for all application models."""

    updated_at: datetime = datetime.now(timezone.utc)
    created_at: datetime = datetime.now(timezone.utc)
    deleted_at: datetime | None = None
