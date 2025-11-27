# ruff: noqa: S101, D100, D101, D102, D103
import asyncio

from blacksheep import JSONContent
from blacksheep.testing import TestClient

from tests.base import BaseTestEndpoints


class TestAccountsEndpoints(BaseTestEndpoints):
    api_path: str = "/api/v1/accounts/"

    async def _create_ledger(self, api_client: TestClient, name: str = "Accounts Test Ledger"):
        """Help to create a ledger and return its parsed JSON."""
        path = "/api/v1/ledgers/"
        response = await api_client.post(
            path,
            content=JSONContent(
                data={
                    "name": name,
                    "description": "Ledger for accounts tests",
                }
            ),
        )
        assert response.status == 200
        return await response.json()

    async def test_create_and_list_accounts(self, api_client: TestClient):
        """Create accounts for a ledger and list them."""
        ledger = await self._create_ledger(api_client)
        ledger_id = ledger["id"]

        # create accounts
        path = self._endpoint(f"/{ledger_id}")
        response = await api_client.post(
            path,
            content=JSONContent(
                data={
                    "name": "Cash",
                    "path": "Assets:Cash",
                }
            ),
        )
        assert response.status == 200
        first = await response.json()
        assert first["name"] == "Cash"
        assert first["path"] == "Assets:Cash"
        assert "id" in first

        # create second account
        response = await api_client.post(
            path,
            content=JSONContent(
                data={
                    "name": "Bank",
                    "path": "Assets:Bank",
                    "ledger_id": ledger_id,
                }
            ),
        )
        assert response.status == 200
        second = await response.json()
        assert second["name"] == "Bank"
        assert second["path"] == "Assets:Bank"
        assert "id" in second

        # list accounts for ledger
        list_response = await api_client.get(path)
        assert list_response.status == 200
        items = await list_response.json()

        assert isinstance(items, dict)
        # controller wraps accounts under 'accounts' key
        accounts = items.get("accounts")
        assert isinstance(accounts, list)
        ids = {i["id"] for i in accounts}
        assert {first["id"], second["id"]}.issubset(ids)

    async def test_account_validation_errors(self, api_client: TestClient):
        """Validation errors when creating account should return 400."""
        ledger = await self._create_ledger(api_client, name="Validation Ledger")
        ledger_id = ledger["id"]
        path = self._endpoint(f"/{ledger_id}")

        invalid_payloads = [
            ({"name": "", "path": "Assets:Empty", "ledger_id": ledger_id}, "empty name"),
            ({"name": "NoRoot", "path": "Unknown:Sub", "ledger_id": ledger_id}, "invalid root"),
            ({"path": "Assets:MissingName", "ledger_id": ledger_id}, "missing name"),
            ({"name": "MissingPath", "ledger_id": ledger_id}, "missing path"),
        ]

        for payload, description in invalid_payloads:
            resp = await api_client.post(path, content=JSONContent(data=payload))
            assert resp.status == 400, f"Expected 400 for {description}, got {resp.status}"

    async def test_get_update_delete_account_and_tree(self, api_client: TestClient):
        """Create an account, get it, update it, delete it and verify tree."""
        ledger = await self._create_ledger(api_client, name="Account Full Flow Ledger")
        ledger_id = ledger["id"]
        base_path = self._endpoint(f"/{ledger_id}")

        # create account
        create_resp = await api_client.post(
            base_path,
            content=JSONContent(
                data={
                    "name": "Checking",
                    "path": "Assets:Bank:Checking",
                    "ledger_id": ledger_id,
                }
            ),
        )
        assert create_resp.status == 200
        created = await create_resp.json()
        account_id = created["id"]

        # get account
        get_path = self._endpoint(f"/{ledger_id}/{account_id}")
        get_resp = await api_client.get(get_path)
        assert get_resp.status == 200
        got = await get_resp.json()
        assert got["id"] == account_id

        # update account
        await asyncio.sleep(0.01)
        update_payload = {"name": "Checking Updated", "path": "Assets:Bank:Checking"}
        update_resp = await api_client.put(get_path, content=JSONContent(data=update_payload))
        assert update_resp.status == 200
        updated = await update_resp.json()
        assert updated["name"] == "Checking Updated"

        # tree
        tree_path = self._endpoint(f"/tree/{ledger_id}")
        tree_resp = await api_client.get(tree_path)
        assert tree_resp.status == 200
        tree = await tree_resp.json()
        assert isinstance(tree, dict)
        assert "Assets:Bank:Checking" in tree

        # delete
        delete_path = self._endpoint(f"/{ledger_id}/{account_id}")
        delete_resp = await api_client.delete(delete_path)
        assert delete_resp.status in (200, 204)

        # verify deleted not present
        list_resp = await api_client.get(base_path)
        assert list_resp.status == 200
        items = await list_resp.json()
        accounts = items.get("accounts")
        assert not any(a["id"] == account_id for a in accounts)

    async def test_update_account_success_and_concurrency(self, api_client: TestClient):
        """Update account and test optimistic concurrency via updated_at."""
        ledger = await self._create_ledger(api_client, name="Concurrency Ledger")
        ledger_id = ledger["id"]
        path = self._endpoint(f"/{ledger_id}")

        # create an account
        create_resp = await api_client.post(
            path,
            content=JSONContent(
                data={
                    "name": "Savings",
                    "path": "Assets:Bank:Savings",
                    "ledger_id": ledger_id,
                }
            ),
        )
        assert create_resp.status == 200
        account = await create_resp.json()
        account_id = account["id"]
        etag = create_resp.headers.get(b"ETag")

        # prepare update payload
        update_path = self._endpoint(f"/{ledger_id}/{account_id}")
        update_payload = {"name": "Savings Updated", "path": "Assets:Bank:Savings"}

        # small delay to ensure DB timestamps can differ if needed
        await asyncio.sleep(0.01)

        update_resp = await api_client.put(
            update_path,
            content=JSONContent(data=update_payload),
            headers={"If-Match": etag[0].decode("utf-8")},  # type: ignore[reportUnknownVariableType] due to bug in headers.pyi
        )

        assert update_resp.status == 200
        updated = await update_resp.json()
        assert updated["name"] == "Savings Updated"

        # Try to update again using stale ETag — simulate concurrency conflict
        stale_payload = {"name": "Should Fail", "path": "Assets:Bank:Savings"}
        conflict_resp = await api_client.put(
            update_path,
            content=JSONContent(data=stale_payload),
            headers={"If-Match": etag[0].decode("utf-8")},  # type: ignore[reportUnknownVariableType] due to bug in headers.pyi
        )

        assert conflict_resp.status == 412
