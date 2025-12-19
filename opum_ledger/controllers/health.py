"""Health check API controller module."""

from blacksheep import allow_anonymous, json
from blacksheep.server.controllers import APIController, get


class Health(APIController):
    """API controller for health checks."""

    @classmethod
    def route(cls) -> str:
        """Override route to place health check at root level."""
        return ""

    @classmethod
    def version(cls) -> str:
        """No versioning for health endpoint."""
        return ""

    @allow_anonymous
    @get("/healthz")
    async def health_check(self):
        """Health check endpoint.

        Returns a simple status response to indicate the service is running.
        """
        return json({"status": "ok"})
