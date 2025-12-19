"""Use this module to register required services.

Services registered inside a `rodi.Container` are automatically injected into request
handlers.

For more information and documentation, see:
    https://www.neoteroi.dev/blacksheep/dependency-injection/
"""

from typing import Literal, TypeVar

from rodi import Container

from tmw_ledger.settings import Settings

# Singleton container for services
container = Container()

ScopeType = Literal["scoped", "scoped_factory", "singleton", "transient"]

T = TypeVar("T")


def add_service(scope: ScopeType = "scoped"):
    """Register a service in the container with the specified scope."""

    def decorator(target: T) -> T:
        match scope:
            case "scoped":
                _ = container.add_scoped(target)
            case "singleton":
                _ = container.add_singleton(target)
            case "transient":
                _ = container.add_transient(target)
            case "scoped_factory":
                _ = container.add_scoped_by_factory(target)
            case _:
                raise ValueError(f"Invalid scope: {scope}")

        return target

    return decorator


def configure_services(
    settings: Settings,
) -> tuple[Container, Settings]:
    container.add_instance(settings)

    return container, settings
