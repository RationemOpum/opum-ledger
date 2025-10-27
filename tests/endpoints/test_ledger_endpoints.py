import asyncio

import pytest
from blacksheep import JSONContent
from blacksheep.testing import TestClient

from tests.base import BaseTestEndpoints


class TestLedgerEndpoints(BaseTestEndpoints):
    api_path: str = "/api/v1/ledgers/"

    @pytest.mark.parametrize(
        "name,description",
        [
            ("Test Ledger #1 Name", "Test Ledger #1 Description"),
            ("My Personal Ledger", "This is my personal finance ledger"),
            ("Business Expenses", None),
        ],
    )
    async def test_create_ledger_success(
        self,
        api_client: TestClient,
        name: str,
        description: str | None,
    ):
        """Test successful ledger creation."""
        path = self._endpoint("/")

        request_data = {"name": name}
        if description is not None:
            request_data["description"] = description

        response = await api_client.post(
            path,
            content=JSONContent(data=request_data),
        )

        assert response.status == 200
        data = await response.json()
        assert data["name"] == name
        assert data["description"] == description
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_ledger_invalid_name_empty(self, api_client: TestClient):
        """Test ledger creation with empty name fails."""
        path = self._endpoint("/")

        response = await api_client.post(
            path,
            content=JSONContent(
                data={
                    "name": "",
                    "description": "Valid description",
                }
            ),
        )

        assert response.status == 400

    async def test_create_ledger_invalid_name_too_long(self, api_client: TestClient):
        """Test ledger creation with name too long fails."""
        path = self._endpoint("/")
        long_name = "x" * 257  # Exceeds max_length=256

        response = await api_client.post(
            path,
            content=JSONContent(
                data={
                    "name": long_name,
                    "description": "Valid description",
                }
            ),
        )

        assert response.status == 400

    async def test_create_ledger_invalid_description_too_long(self, api_client: TestClient):
        """Test ledger creation with description too long fails."""
        path = self._endpoint("/")
        long_description = "x" * 1025  # Exceeds max_length=1024

        response = await api_client.post(
            path,
            content=JSONContent(
                data={
                    "name": "Valid Name",
                    "description": long_description,
                }
            ),
        )

        assert response.status == 400

    async def test_create_ledger_missing_name(self, api_client: TestClient):
        """Test ledger creation without required name fails."""
        path = self._endpoint("/")

        response = await api_client.post(
            path,
            content=JSONContent(
                data={
                    "description": "Valid description",
                }
            ),
        )

        assert response.status == 400

    async def test_create_ledger_duplicate_name(self, api_client: TestClient):
        """Test ledger creation with duplicate name fails."""
        path = self._endpoint("/")
        ledger_data = {
            "name": "Duplicate Name Test",
            "description": "First ledger",
        }

        # Create first ledger
        response = await api_client.post(
            path,
            content=JSONContent(data=ledger_data),
        )
        assert response.status == 200

        # Try to create second ledger with same name
        response = await api_client.post(
            path,
            content=JSONContent(
                data={
                    "name": "Duplicate Name Test",
                    "description": "Second ledger",
                }
            ),
        )
        assert response.status == 409  # Conflict

    async def test_get_all_ledgers_empty(self, api_client: TestClient):
        """Test getting all ledgers when none exist."""
        path = self._endpoint("/")

        response = await api_client.get(path)

        assert response.status == 200
        data = await response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_get_all_ledgers_with_data(self, api_client: TestClient):
        """Test getting all ledgers when some exist."""
        path = self._endpoint("/")

        # Create test ledgers
        ledgers_to_create = [
            {"name": "Ledger 1", "description": "First ledger"},
            {"name": "Ledger 2", "description": "Second ledger"},
            {"name": "Ledger 3", "description": None},
        ]

        created_ledgers = []
        for ledger_data in ledgers_to_create:
            response = await api_client.post(
                path,
                content=JSONContent(data=ledger_data),
            )
            assert response.status == 200
            created_ledgers.append(await response.json())

        # Get all ledgers
        response = await api_client.get(path)

        assert response.status == 200
        data = await response.json()
        assert isinstance(data, list)
        assert len(data) == 3

        # Verify all created ledgers are returned
        returned_names = {ledger["name"] for ledger in data}
        expected_names = {ledger["name"] for ledger in ledgers_to_create}
        assert returned_names == expected_names

    async def test_update_ledger_success(self, api_client: TestClient):
        """Test successful ledger update."""
        path = self._endpoint("/")

        # Create a ledger first
        create_response = await api_client.post(
            path,
            content=JSONContent(
                data={
                    "name": "Original Name",
                    "description": "Original Description",
                }
            ),
        )
        assert create_response.status == 200
        created_ledger = await create_response.json()
        ledger_id = created_ledger["id"]

        # Add small delay to ensure timestamp difference
        await asyncio.sleep(0.1)

        # Update the ledger
        update_path = self._endpoint(f"/{ledger_id}")
        update_response = await api_client.put(
            update_path,
            content=JSONContent(
                data={
                    "name": "Updated Name",
                    "description": "Updated Description",
                }
            ),
        )

        assert update_response.status == 200
        updated_ledger = await update_response.json()
        assert updated_ledger["id"] == ledger_id
        assert updated_ledger["name"] == "Updated Name"
        assert updated_ledger["description"] == "Updated Description"
        # Verify timestamps are present and in expected format
        assert "created_at" in updated_ledger
        assert "updated_at" in updated_ledger
        assert updated_ledger["created_at"]  # Not empty
        assert updated_ledger["updated_at"]  # Not empty

    async def test_update_ledger_partial(self, api_client: TestClient):
        """Test partial ledger update (only name or description)."""
        path = self._endpoint("/")

        # Create a ledger first
        create_response = await api_client.post(
            path,
            content=JSONContent(
                data={
                    "name": "Original Name",
                    "description": "Original Description",
                }
            ),
        )
        assert create_response.status == 200
        created_ledger = await create_response.json()
        ledger_id = created_ledger["id"]

        # Update only the name
        update_path = self._endpoint(f"/{ledger_id}")
        update_response = await api_client.put(
            update_path,
            content=JSONContent(
                data={
                    "name": "Updated Name Only",
                }
            ),
        )

        assert update_response.status == 200
        updated_ledger = await update_response.json()
        assert updated_ledger["name"] == "Updated Name Only"
        assert updated_ledger["description"] == "Original Description"  # Should remain unchanged
        assert "created_at" in updated_ledger
        assert "updated_at" in updated_ledger

    async def test_update_ledger_nonexistent(self, api_client: TestClient):
        """Test updating a non-existent ledger."""
        # Use a valid UUID7 format that doesn't exist
        fake_id = "01234567-89ab-7def-0123-456789abcdef"
        update_path = self._endpoint(f"/{fake_id}")

        update_response = await api_client.put(
            update_path,
            content=JSONContent(
                data={
                    "name": "Updated Name",
                    "description": "Updated Description",
                }
            ),
        )

        assert update_response.status == 404

    async def test_update_ledger_invalid_id(self, api_client: TestClient):
        """Test updating a ledger with invalid ID format."""
        invalid_id = "not-a-valid-uuid"
        update_path = self._endpoint(f"/{invalid_id}")

        update_response = await api_client.put(
            update_path,
            content=JSONContent(
                data={
                    "name": "Updated Name",
                    "description": "Updated Description",
                }
            ),
        )

        assert update_response.status == 400

    async def test_update_ledger_validation_errors(self, api_client: TestClient):
        """Test ledger update with validation errors."""
        path = self._endpoint("/")

        # Create a ledger first
        create_response = await api_client.post(
            path,
            content=JSONContent(
                data={
                    "name": "Original Name",
                    "description": "Original Description",
                }
            ),
        )
        assert create_response.status == 200
        created_ledger = await create_response.json()
        ledger_id = created_ledger["id"]

        # Try to update with invalid name (too long)
        update_path = self._endpoint(f"/{ledger_id}")
        long_name = "x" * 257  # Exceeds max_length=256

        update_response = await api_client.put(
            update_path,
            content=JSONContent(
                data={
                    "name": long_name,
                }
            ),
        )

        assert update_response.status == 400

    async def test_ledger_workflow_complete(self, api_client: TestClient):
        """Test complete ledger workflow: create -> get all -> update -> get all."""
        path = self._endpoint("/")

        # 1. Create multiple ledgers
        ledger1_response = await api_client.post(
            path,
            content=JSONContent(
                data={
                    "name": "Workflow Test 1",
                    "description": "First test ledger",
                }
            ),
        )
        assert ledger1_response.status == 200
        ledger1 = await ledger1_response.json()

        ledger2_response = await api_client.post(
            path,
            content=JSONContent(
                data={
                    "name": "Workflow Test 2",
                    "description": "Second test ledger",
                }
            ),
        )
        assert ledger2_response.status == 200
        ledger2 = await ledger2_response.json()

        # 2. Get all ledgers
        get_response = await api_client.get(path)
        assert get_response.status == 200
        all_ledgers = await get_response.json()
        assert len(all_ledgers) >= 2

        # 3. Update one ledger
        update_path = self._endpoint(f"/{ledger1['id']}")
        update_response = await api_client.put(
            update_path,
            content=JSONContent(
                data={
                    "name": "Updated Workflow Test 1",
                    "description": "Updated first test ledger",
                }
            ),
        )
        assert update_response.status == 200
        updated_ledger1 = await update_response.json()
        assert updated_ledger1["name"] == "Updated Workflow Test 1"

        # 4. Get all ledgers again to verify update
        final_get_response = await api_client.get(path)
        assert final_get_response.status == 200
        final_ledgers = await final_get_response.json()

        # Find the updated ledger in the list
        updated_ledger_in_list = next((ledger for ledger in final_ledgers if ledger["id"] == ledger1["id"]), None)
        assert updated_ledger_in_list is not None
        assert updated_ledger_in_list["name"] == "Updated Workflow Test 1"
        assert updated_ledger_in_list["description"] == "Updated first test ledger"

    async def test_update_ledger_if_unmodified_since_success(self, api_client: TestClient):
        """Test update succeeds when If-Unmodified-Since matches current updated_at."""
        path = self._endpoint("/")

        # Create a ledger first
        create_response = await api_client.post(
            path,
            content=JSONContent(
                data={
                    "name": "IUS Success Original",
                    "description": "Original Description",
                }
            ),
        )
        assert create_response.status == 200
        created_ledger = await create_response.json()
        ledger_id = created_ledger["id"]
        etag = create_response.headers.get(b"ETag")

        # Attempt update with If-Unmodified-Since header equal to current updated_at
        update_path = self._endpoint(f"/{ledger_id}")
        update_response = await api_client.put(
            update_path,
            headers={"If-Match": etag[0].decode("utf-8")},
            content=JSONContent(
                data={
                    "name": "IUS Success Updated",
                    "description": "Updated Description",
                }
            ),
        )

        assert update_response.status == 200
        updated_ledger = await update_response.json()
        assert updated_ledger["id"] == ledger_id
        assert updated_ledger["name"] == "IUS Success Updated"

    async def test_update_ledger_if_unmodified_since_conflict(self, api_client: TestClient):
        """Test update fails with 412 when ledger was modified after the provided If-Unmodified-Since."""
        path = self._endpoint("/")

        # Create a ledger first
        create_response = await api_client.post(
            path,
            content=JSONContent(
                data={
                    "name": "IUS Conflict Original",
                    "description": "Original Description",
                }
            ),
        )
        assert create_response.status == 200
        created_ledger = await create_response.json()
        ledger_id = created_ledger["id"]
        etag = create_response.headers.get(b"ETag")

        # Perform another update to advance the ledger's updated_at (simulate another client)
        update_path = self._endpoint(f"/{ledger_id}")
        first_update_response = await api_client.put(
            update_path,
            content=JSONContent(
                data={
                    "name": "IUS Conflict Intermediate",
                    "description": "Intermediate Description",
                }
            ),
        )
        assert first_update_response.status == 200
        assert first_update_response.headers.get(b"ETag") != etag  # ETag should have changed

        # Attempt update with stale If-Unmodified-Since header — should fail with 412
        conflict_update_response = await api_client.put(
            update_path,
            headers={"If-Match": etag[0].decode("utf-8")},
            content=JSONContent(
                data={
                    "name": "IUS Conflict Attempt",
                    "description": "Should Fail",
                }
            ),
        )

        assert conflict_update_response.status == 412
