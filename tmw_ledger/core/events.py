"""Module contains classes to configure initialization and disposing of services.

For example, a connection pool to a PostgreSQL database can be initialized at
application startup, and disposed when the application is stopped.

This class is common between, and abstracted from, front-end logic and data access
logic. See how it is used in app.program.py
app.on_start += context.initialize
"""

from typing import Self


class AsyncEventHandler:
    def __init__(self, context) -> None:
        self.__handlers = []
        self.context = context

    def __iadd__(self, handler) -> Self:
        self.__handlers.append(handler)
        return self

    def __isub__(self, handler) -> Self:
        self.__handlers.remove(handler)
        return self

    def __len__(self) -> int:
        return len(self.__handlers)

    def append(self, handler) -> None:
        self.__handlers.append(handler)

    async def __call__(self, *args, **kwargs) -> None:
        return await self.fire()

    async def fire(self) -> None:
        for handler in self.__handlers:
            await handler()


class ServicesRegistrationContext:
    def __init__(self) -> None:
        self.initialize = AsyncEventHandler(self)
        self.dispose = AsyncEventHandler(self)
