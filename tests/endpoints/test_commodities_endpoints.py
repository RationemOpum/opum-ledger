# ruff: noqa: S101, D100, D101, D102, D103
import asyncio
from typing import Any

from blacksheep import JSONContent
from blacksheep.testing import TestClient

from tests.base import BaseTestEndpoints


class TestCommoditiesEndpoints(BaseTestEndpoints):
    api_path: str = "/api/v1/commodities/"

    async def _create_ledger(self, api_client: TestClient, name: str = "Commodities Test Ledger") -> Any:
        """Help to create a ledger and return its parsed JSON."""
        path = "/api/v1/ledgers/"
        response = await api_client.post(
            path,
            content=JSONContent(
                data={
                    "name": name,
                    "description": "Ledger for commodities tests",
                }
            ),
        )
        assert response.status == 200
        return await response.json()

    async def test_create_and_list_commodities(self, api_client: TestClient) -> None:
        """Create commodities for a ledger and list them."""
        # create ledger
        ledger = await self._create_ledger(api_client)
        ledger_id = ledger["id"]

        # create commodities
        path = self._endpoint(f"/{ledger_id}")
        response = await api_client.post(
            path,
            content=JSONContent(
                data={
                    "name": "US Dollar",
                    "code": "USD",
                    "symbol": "$",
                    "subunit": 100,
                    "no_market": False,
                    "ledger_id": ledger_id,
                }
            ),
        )
        assert response.status == 200
        first = await response.json()
        assert first["name"] == "US Dollar"
        assert first["code"] == "USD"
        assert first["symbol"] == "$"
        assert first["subunit"] == 100
        assert "id" in first
        assert "created_at" in first
        assert "updated_at" in first

        # create second commodity
        response = await api_client.post(
            path,
            content=JSONContent(
                data={
                    "name": "Euro",
                    "code": "EUR",
                    "symbol": "€",
                    "subunit": 100,
                    "no_market": False,
                    "ledger_id": ledger_id,
                }
            ),
        )
        assert response.status == 200
        second = await response.json()
        assert second["name"] == "Euro"
        assert second["code"] == "EUR"
        assert second["symbol"] == "€"
        assert second["subunit"] == 100
        assert "id" in second
        assert "created_at" in second
        assert "updated_at" in second

        # list commodities for ledger
        list_response = await api_client.get(path)
        assert list_response.status == 200
        items = await list_response.json()
        assert len(items) == 2
        assert isinstance(items, list)
        codes = {i["code"] for i in items}
        assert {"USD", "EUR"}.issubset(codes)

    async def test_create_duplicate_code_conflict(self, api_client: TestClient) -> None:
        """Creating a commodity with duplicate code in the same ledger should return 409."""
        ledger = await self._create_ledger(api_client, name="Duplicate Code Ledger")
        ledger_id = ledger["id"]

        path = self._endpoint(f"/{ledger_id}")
        data = {
            "name": "First USD",
            "code": "USD",
            "symbol": "$",
            "subunit": 100,
            "no_market": False,
        }
        response = await api_client.post(path, content=JSONContent(data={**data, "ledger_id": ledger_id}))
        assert response.status == 200

        # attempt to create duplicate
        response = await api_client.post(
            path,
            content=JSONContent(
                data={
                    "name": "Duplicate USD",
                    "code": "USD",
                    "symbol": "$",
                    "subunit": 100,
                    "no_market": False,
                    "ledger_id": ledger_id,
                }
            ),
        )
        assert response.status == 409
        assert response.reason == "Conflict"
        assert response.content is not None
        error_content = await response.json()
        assert "duplicate key error collection" in error_content.get("detail", "")

    async def test_update_commodity_success_and_concurrency(self, api_client: TestClient) -> None:
        """Update commodity and test optimistic concurrency via updated_at."""
        ledger = await self._create_ledger(api_client, name="Concurrency Ledger")
        ledger_id = ledger["id"]
        path = self._endpoint(f"/{ledger_id}")

        # create a commodity
        create_resp = await api_client.post(
            path,
            content=JSONContent(
                data={
                    "name": "TestCoin",
                    "code": "TST",
                    "symbol": "T",
                    "subunit": 10,
                    "no_market": False,
                    "ledger_id": ledger_id,
                }
            ),
        )
        assert create_resp.status == 200
        commodity = await create_resp.json()
        commodity_id = commodity["id"]
        etag = create_resp.headers.get(b"ETag")

        # prepare update payload with updated_at from created commodity (should succeed)
        update_path = self._endpoint(f"/{ledger_id}/{commodity_id}")
        update_payload = {
            "name": "TestCoin Updated",
            "code": "TST",
            "symbol": "T",
            "subunit": 100,
            "no_market": False,
        }

        # small delay to ensure DB timestamps can differ if needed
        await asyncio.sleep(0.01)

        update_resp = await api_client.put(
            update_path,
            content=JSONContent(data=update_payload),
            headers={"If-Match": etag[0].decode("utf-8")},  # type: ignore
        )

        assert update_resp.status == 200
        updated = await update_resp.json()
        assert updated["name"] == "TestCoin Updated"
        assert updated["subunit"] == 100

        # Try to update again using stale updated_at — simulate concurrency conflict
        # Include all required fields expected by the UpdateCommodity model along with the stale timestamp.
        stale_payload = {
            "name": "Should Fail",
            "code": "TST",
            "symbol": "T",
            "subunit": 100,
            "no_market": False,
        }
        conflict_resp = await api_client.put(
            update_path,
            content=JSONContent(data=stale_payload),
            headers={"If-Match": etag[0].decode("utf-8")},  # type: ignore
        )

        assert conflict_resp.status == 412

    async def test_delete_commodity(self, api_client: TestClient) -> None:
        """Delete commodity from ledger and verify it is no longer listed."""
        ledger = await self._create_ledger(api_client, name="Delete Commodity Ledger")
        ledger_id = ledger["id"]
        path = self._endpoint(f"/{ledger_id}")

        create_resp = await api_client.post(
            path,
            content=JSONContent(
                data={
                    "name": "DeleteMe",
                    "code": "DEL",
                    "symbol": "D",
                    "subunit": 100,
                    "no_market": False,
                    "ledger_id": ledger_id,
                }
            ),
        )
        assert create_resp.status == 200
        commodity = await create_resp.json()
        commodity_id = commodity["id"]

        # ensure present in list
        list_resp = await api_client.get(path)
        assert list_resp.status == 200
        items = await list_resp.json()
        assert any(i["id"] == commodity_id for i in items)

        # delete
        delete_path = self._endpoint(f"/{ledger_id}/{commodity_id}")
        delete_resp = await api_client.delete(delete_path)
        # delete endpoint returns 200 or 204; controller declares None, error handlers may normalize -> expect 200/204
        assert delete_resp.status in (200, 204)

        # verify not in list anymore
        list_resp2 = await api_client.get(path)
        assert list_resp2.status == 200
        items2 = await list_resp2.json()
        assert not any(i["id"] == commodity_id for i in items2)

    async def test_create_commodity_validation_errors(self, api_client: TestClient) -> None:
        """Validation errors when creating commodity should return 400."""
        ledger = await self._create_ledger(api_client, name="Validation Ledger")
        ledger_id = ledger["id"]
        path = self._endpoint(f"/{ledger_id}")

        # A list of invalid payloads and descriptions to exercise validation rules.
        invalid_payloads = [
            # missing required fields: empty name and code
            ({"name": "", "code": "", "ledger_id": ledger_id}, "missing required fields"),
            # code too long (exceeds max_length=8)
            (
                {
                    "name": "Long Code",
                    "code": "TOO_LONG_CODE",  # exceeds max_length=8
                    "symbol": "$",
                    "subunit": 100,
                    "no_market": False,
                    "ledger_id": ledger_id,
                },
                "code too long",
            ),
            # symbol too long (exceeds max_length=8)
            (
                {
                    "name": "Bad Symbol",
                    "code": "BS",
                    "symbol": "S" * 9,  # 9 chars, exceeds max_length=8
                    "subunit": 100,
                    "no_market": False,
                    "ledger_id": ledger_id,
                },
                "symbol too long",
            ),
            # subunit too small (must be >= 1)
            (
                {
                    "name": "Zero Subunit",
                    "code": "ZRO",
                    "symbol": "$",
                    "subunit": 0,
                    "no_market": False,
                    "ledger_id": ledger_id,
                },
                "subunit too small",
            ),
            # subunit negative
            (
                {
                    "name": "Negative Subunit",
                    "code": "NEG",
                    "symbol": "$",
                    "subunit": -10,
                    "no_market": False,
                    "ledger_id": ledger_id,
                },
                "subunit negative",
            ),
            # missing ledger_id in payload (controller expects ledger_id in body for validation)
            (
                {
                    "name": "Missing Ledger",
                    "code": "ML",
                    "symbol": "$",
                    "subunit": 100,
                    "no_market": False,
                },
                "missing ledger_id",
            ),
            # empty symbol (symbol is allowed to be None but empty string should be invalid)
            (
                {
                    "name": "Symbol Empty",
                    "code": "SE",
                    "symbol": "",
                    "subunit": 100,
                    "no_market": False,
                    "ledger_id": ledger_id,
                },
                "symbol empty",
            ),
        ]

        for payload, description in invalid_payloads:
            resp = await api_client.post(path, content=JSONContent(data=payload))
            # Expect a 400 Bad Request for all validation errors
            assert resp.status == 400, f"Expected 400 for {description}, got {resp.status}"
