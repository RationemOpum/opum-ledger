import asyncio

import pytest
from blacksheep import Application, Response
from blacksheep.contents import Content
from blacksheep.testing.helpers import CookiesType, HeadersType, QueryType
from blacksheep.testing.simulator import AbstractTestSimulator, TestSimulator
from blacksheep.testing.websocket import TestWebSocket


class TestClient:
    # Setting this dunder variable
    # We tell to pytest don't discover this up
    __test__ = False

    def __init__(
        self,
        app: Application,
        test_simulator: AbstractTestSimulator | None = None,
        extra_headers: HeadersType = None,
    ):
        self._test_simulator = test_simulator or TestSimulator(app)

        if isinstance(extra_headers, dict):
            extra_headers = [(key.encode(), value.encode()) for key, value in extra_headers.items()]

        self._extra_headers = extra_headers or []

    async def send_request(
        self,
        method: str,
        path: str,
        headers: HeadersType = None,
        query: QueryType = None,
        content: Content | None = None,
        cookies: CookiesType = None,
    ) -> Response:
        """Send a simulated HTTP request."""
        if headers is not None and isinstance(headers, dict):
            headers = tuple((key.encode(), value.encode()) for key, value in headers.items())

        if headers is None:
            headers = self._extra_headers
        else:
            headers = tuple(headers) + tuple(self._extra_headers)

        return await self._test_simulator.send_request(
            method=method,
            path=path,
            headers=headers,
            query=query,
            content=content,
            cookies=cookies,
        )

    async def get(
        self,
        path: str,
        headers: HeadersType = None,
        query: QueryType = None,
        cookies: CookiesType = None,
    ) -> Response:
        """Simulate HTTP GET method."""
        return await self.send_request(
            method="GET",
            path=path,
            headers=headers,
            query=query,
            cookies=cookies,
            content=None,
        )

    async def post(
        self,
        path: str,
        headers: HeadersType = None,
        query: QueryType = None,
        content: Content | None = None,
        cookies: CookiesType = None,
    ) -> Response:
        """Simulate HTTP POST method."""
        return await self.send_request(
            method="POST",
            path=path,
            headers=headers,
            query=query,
            cookies=cookies,
            content=content,
        )

    async def patch(
        self,
        path: str,
        headers: HeadersType = None,
        query: QueryType = None,
        content: Content | None = None,
        cookies: CookiesType = None,
    ) -> Response:
        """Simulate HTTP PATCH method."""
        return await self.send_request(
            method="PATCH",
            path=path,
            headers=headers,
            query=query,
            cookies=cookies,
            content=content,
        )

    async def put(
        self,
        path: str,
        headers: HeadersType = None,
        query: QueryType = None,
        content: Content | None = None,
        cookies: CookiesType = None,
    ) -> Response:
        """Simulate HTTP PUT method."""
        return await self.send_request(
            method="PUT",
            path=path,
            headers=headers,
            query=query,
            content=content,
            cookies=cookies,
        )

    async def delete(
        self,
        path: str,
        headers: HeadersType = None,
        query: QueryType = None,
        content: Content | None = None,
        cookies: CookiesType = None,
    ) -> Response:
        """Simulate HTTP DELETE method."""
        return await self.send_request(
            method="DELETE",
            path=path,
            headers=headers,
            query=query,
            content=content,
            cookies=cookies,
        )

    async def options(
        self,
        path: str,
        headers: HeadersType = None,
        query: QueryType = None,
        cookies: CookiesType = None,
    ) -> Response:
        """Simulate HTTP OPTIONS method."""
        return await self.send_request(
            method="OPTIONS",
            path=path,
            headers=headers,
            query=query,
            content=None,
            cookies=cookies,
        )

    async def head(
        self,
        path: str,
        headers: HeadersType = None,
        query: QueryType = None,
        cookies: CookiesType = None,
    ) -> Response:
        """Simulate HTTP HEAD method."""
        return await self.send_request(
            method="HEAD",
            path=path,
            headers=headers,
            query=query,
            content=None,
            cookies=cookies,
        )

    async def trace(
        self,
        path: str,
        headers: HeadersType = None,
        query: QueryType = None,
        cookies: CookiesType = None,
    ) -> Response:
        """Simulate HTTP TRACE method."""
        return await self.send_request(
            method="TRACE",
            path=path,
            headers=headers,
            query=query,
            content=None,
            cookies=cookies,
        )

    def websocket_connect(
        self,
        path: str,
        headers: HeadersType = None,
        query: QueryType = None,
        cookies: CookiesType = None,
    ) -> TestWebSocket:
        return self._test_simulator.websocket_connect(  # type: ignore
            path=path,
            headers=headers,
            query=query,
            content=None,
            cookies=cookies,
        )

    async def websocket_all_closed(self):
        await asyncio.gather(*self._test_simulator.websocket_tasks)  # type: ignore
        self._test_simulator.websocket_tasks = []  # type: ignore


async def make_api_client(extra_headers: HeadersType = None) -> TestClient:
    from opum_ledger.app import app

    await app.start()

    return TestClient(app, extra_headers=extra_headers)


@pytest.fixture
async def api_client(mongodb, init_db) -> TestClient:
    return await make_api_client(
        extra_headers={"X-API-KEY": "rw_test_api_key"},
    )


@pytest.fixture
async def api_client_ro(mongodb, init_db) -> TestClient:
    return await make_api_client(
        extra_headers={"X-API-KEY": "ro_test_api_key"},
    )
