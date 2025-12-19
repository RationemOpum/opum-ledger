# ruff: noqa: S101, D100, D101, D102, D103
import asyncio
from datetime import datetime, timezone
from urllib.parse import quote

from blacksheep import JSONContent
from blacksheep.testing import TestClient

from tests.base import BaseTestEndpoints
from tmw_ledger.domain.accounts import Account
from tmw_ledger.domain.commodities import Commodity
from tmw_ledger.domain.ledgers import Ledger


class TestTransactionsEndpoints(BaseTestEndpoints):
    api_path: str = "/api/v1/transactions/"

    async def test_create_simple_transaction(
        self,
        api_client: TestClient,
        ledger_one: Ledger,
        commodity_usd_ledger_one: Commodity,
        account_assets_cash_ledger_one: Account,
        account_expenses_groceries_ledger_one: Account,
    ) -> None:
        """Create a simple balanced transaction and verify it."""
        ledger_id = str(ledger_one.id)
        commodity_id = str(commodity_usd_ledger_one.id)
        cash_account_id = str(account_assets_cash_ledger_one.id)
        expense_account_id = str(account_expenses_groceries_ledger_one.id)

        # Create transaction
        path = self._endpoint(f"/{ledger_id}")
        transaction_data = {
            "description": "Grocery shopping",
            "date_time": "2024-01-15T10:30:00Z",
            "details": [
                {
                    "account_id": cash_account_id,
                    "amount": {"commodity_id": commodity_id, "amount": -5000},
                },
                {
                    "account_id": expense_account_id,
                    "amount": {"commodity_id": commodity_id, "amount": 5000},
                },
            ],
            "tags": ["groceries", "food"],
            "state": "cleared",
        }

        response = await api_client.post(path, content=JSONContent(data=transaction_data))
        assert response.status == 200

        transaction = await response.json()
        assert transaction["description"] == "Grocery shopping"
        assert transaction["ledger_id"] == ledger_id
        assert len(transaction["details"]) == 2
        assert transaction["state"] == "cleared"
        assert "groceries" in transaction["tags"]
        assert "food" in transaction["tags"]
        assert "id" in transaction
        assert "created_at" in transaction
        assert "updated_at" in transaction
        assert b"ETag" in response.headers

    async def test_create_unbalanced_transaction_fails(
        self,
        api_client: TestClient,
        ledger_one: Ledger,
        commodity_usd_ledger_one: Commodity,
        account_assets_cash_ledger_one: Account,
        account_expenses_food_ledger_one: Account,
    ) -> None:
        """Creating an unbalanced transaction should return 400."""
        ledger_id = str(ledger_one.id)
        commodity_id = str(commodity_usd_ledger_one.id)
        cash_account_id = str(account_assets_cash_ledger_one.id)
        expense_account_id = str(account_expenses_food_ledger_one.id)

        path = self._endpoint(f"/{ledger_id}")
        unbalanced_data = {
            "description": "Unbalanced transaction",
            "date_time": "2024-01-15T10:30:00Z",
            "details": [
                {
                    "account_id": cash_account_id,
                    "amount": {"commodity_id": commodity_id, "amount": -5000},
                },
                {
                    "account_id": expense_account_id,
                    "amount": {"commodity_id": commodity_id, "amount": 3000},
                },
            ],
        }

        response = await api_client.post(path, content=JSONContent(data=unbalanced_data))
        assert response.status == 400

    async def test_create_transaction_with_exchange(
        self,
        api_client: TestClient,
        ledger_one: Ledger,
        commodity_usd_ledger_one: Commodity,
        commodity_eur_ledger_one: Commodity,
        account_assets_cash_usd_ledger_one: Account,
        account_assets_cash_eur_ledger_one: Account,
    ) -> None:
        """Create a transaction with currency exchange (price field)."""
        ledger_id = str(ledger_one.id)
        usd_id = str(commodity_usd_ledger_one.id)
        eur_id = str(commodity_eur_ledger_one.id)
        usd_account_id = str(account_assets_cash_usd_ledger_one.id)
        eur_account_id = str(account_assets_cash_eur_ledger_one.id)

        path = self._endpoint(f"/{ledger_id}")
        # Exchange 100 USD to EUR at rate of 0.92 EUR per USD
        # This results in 92 EUR credit and 100 USD debit
        # Both sides expressed in EUR: -92 EUR + (-100 USD * 0.92 EUR/USD) = -92 EUR + 92 EUR = 0 EUR
        # To balance: we need the EUR side to be 0 EUR
        exchange_data = {
            "description": "Currency exchange",
            "date_time": "2024-01-15T10:30:00Z",
            "details": [
                {
                    "account_id": eur_account_id,
                    "amount": {"commodity_id": eur_id, "amount": 9200},
                },
                {
                    "account_id": usd_account_id,
                    "amount": {"commodity_id": usd_id, "amount": -10000},
                    "price": {
                        "commodity_id": eur_id,
                        "price": {"numerator": 9200, "denominator": 10000},
                    },
                },
            ],
            "tags": ["exchange"],
        }

        response = await api_client.post(path, content=JSONContent(data=exchange_data))
        assert response.status == 200

        transaction = await response.json()
        assert transaction["description"] == "Currency exchange"
        assert len(transaction["details"]) == 2
        assert transaction["details"][1]["price"] is not None

    async def test_get_transaction(
        self,
        api_client: TestClient,
        ledger_one: Ledger,
        commodity_usd_ledger_one: Commodity,
        account_assets_cash_ledger_one: Account,
        account_expenses_food_ledger_one: Account,
    ) -> None:
        """Get a specific transaction by ID."""
        ledger_id = str(ledger_one.id)
        commodity_id = str(commodity_usd_ledger_one.id)
        account1_id = str(account_assets_cash_ledger_one.id)
        account2_id = str(account_expenses_food_ledger_one.id)

        # Create transaction
        create_path = self._endpoint(f"/{ledger_id}")
        transaction_data = {
            "description": "Test transaction",
            "date_time": "2024-01-15T10:30:00Z",
            "details": [
                {
                    "account_id": account1_id,
                    "amount": {"commodity_id": commodity_id, "amount": -1000},
                },
                {
                    "account_id": account2_id,
                    "amount": {"commodity_id": commodity_id, "amount": 1000},
                },
            ],
        }

        create_response = await api_client.post(create_path, content=JSONContent(data=transaction_data))
        assert create_response.status == 200
        created = await create_response.json()
        transaction_id = created["id"]

        # Get transaction
        get_path = self._endpoint(f"/{ledger_id}/{transaction_id}")
        get_response = await api_client.get(get_path)
        assert get_response.status == 200

        transaction = await get_response.json()
        assert transaction["id"] == transaction_id
        assert transaction["description"] == "Test transaction"
        assert b"ETag" in get_response.headers

    async def test_get_nonexistent_transaction_returns_404(
        self,
        api_client: TestClient,
        ledger_one: Ledger,
    ) -> None:
        """Getting a nonexistent transaction should return 404."""
        ledger_id = str(ledger_one.id)

        fake_transaction_id = "01234567-89ab-7def-0123-456789abcdef"
        path = self._endpoint(f"/{ledger_id}/{fake_transaction_id}")
        response = await api_client.get(path)
        assert response.status == 404

    async def test_list_transactions(
        self,
        api_client: TestClient,
        ledger_one: Ledger,
        commodity_usd_ledger_one: Commodity,
        account_assets_cash_ledger_one: Account,
        account_expenses_food_ledger_one: Account,
    ) -> None:
        """List all transactions in a ledger."""
        ledger_id = str(ledger_one.id)
        commodity_id = str(commodity_usd_ledger_one.id)
        account1_id = str(account_assets_cash_ledger_one.id)
        account2_id = str(account_expenses_food_ledger_one.id)

        # Create multiple transactions
        create_path = self._endpoint(f"/{ledger_id}")
        for i in range(3):
            transaction_data = {
                "description": f"Transaction {i}",
                "date_time": f"2024-01-{15 + i:02d}T10:30:00Z",
                "details": [
                    {
                        "account_id": account1_id,
                        "amount": {"commodity_id": commodity_id, "amount": -1000 * (i + 1)},
                    },
                    {
                        "account_id": account2_id,
                        "amount": {"commodity_id": commodity_id, "amount": 1000 * (i + 1)},
                    },
                ],
            }
            response = await api_client.post(create_path, content=JSONContent(data=transaction_data))
            assert response.status == 200

        # List transactions
        list_path = self._endpoint(f"/{ledger_id}")
        response = await api_client.get(list_path)
        assert response.status == 200

        result = await response.json()
        assert isinstance(result, dict)
        assert "transactions" in result
        assert "skip" in result
        assert "limit" in result
        assert "count" in result
        assert result["count"] == 3
        assert len(result["transactions"]) == 3

    async def test_list_transactions_with_pagination(
        self,
        api_client: TestClient,
        ledger_one: Ledger,
        commodity_usd_ledger_one: Commodity,
        account_assets_cash_ledger_one: Account,
        account_expenses_food_ledger_one: Account,
    ) -> None:
        """List transactions with pagination parameters."""
        ledger_id = str(ledger_one.id)
        commodity_id = str(commodity_usd_ledger_one.id)
        account1_id = str(account_assets_cash_ledger_one.id)
        account2_id = str(account_expenses_food_ledger_one.id)

        # Create 5 transactions
        create_path = self._endpoint(f"/{ledger_id}")
        for i in range(5):
            transaction_data = {
                "description": f"Transaction {i}",
                "date_time": f"2024-01-{10 + i:02d}T10:30:00Z",
                "details": [
                    {
                        "account_id": account1_id,
                        "amount": {"commodity_id": commodity_id, "amount": -1000},
                    },
                    {
                        "account_id": account2_id,
                        "amount": {"commodity_id": commodity_id, "amount": 1000},
                    },
                ],
            }
            response = await api_client.post(create_path, content=JSONContent(data=transaction_data))
            assert response.status == 200

        # Get first page
        list_path = self._endpoint(f"/{ledger_id}?skip=0&limit=2")
        response = await api_client.get(list_path)
        assert response.status == 200

        result = await response.json()
        assert result["count"] == 5
        assert len(result["transactions"]) == 2
        assert result["skip"] == 0
        assert result["limit"] == 2

        # Get second page
        list_path = self._endpoint(f"/{ledger_id}?skip=2&limit=2")
        response = await api_client.get(list_path)
        assert response.status == 200

        result = await response.json()
        assert result["count"] == 5
        assert len(result["transactions"]) == 2
        assert result["skip"] == 2

    async def test_list_transactions_with_account_filter(
        self,
        api_client: TestClient,
        ledger_one: Ledger,
        commodity_usd_ledger_one: Commodity,
        account_assets_cash_ledger_one: Account,
        account_expenses_food_ledger_one: Account,
        account_expenses_rent_ledger_one: Account,
    ) -> None:
        """List transactions filtered by account."""
        ledger_id = str(ledger_one.id)
        commodity_id = str(commodity_usd_ledger_one.id)
        cash_account_id = str(account_assets_cash_ledger_one.id)
        food_account_id = str(account_expenses_food_ledger_one.id)
        rent_account_id = str(account_expenses_rent_ledger_one.id)

        # Create transactions with different accounts
        create_path = self._endpoint(f"/{ledger_id}")

        # Transaction 1: Cash -> Food. Buys food with cash
        await api_client.post(
            create_path,
            content=JSONContent(
                data={
                    "description": "Food expense",
                    "date_time": "2024-01-15T10:30:00Z",
                    "details": [
                        {
                            "account_id": cash_account_id,
                            "amount": {"commodity_id": commodity_id, "amount": -1000},
                        },
                        {
                            "account_id": food_account_id,
                            "amount": {"commodity_id": commodity_id, "amount": 1000},
                        },
                    ],
                }
            ),
        )

        # Transaction 2: Cash -> Rent. Pays rent with cash
        await api_client.post(
            create_path,
            content=JSONContent(
                data={
                    "description": "Rent payment",
                    "date_time": "2024-01-16T10:30:00Z",
                    "details": [
                        {
                            "account_id": cash_account_id,
                            "amount": {"commodity_id": commodity_id, "amount": -2000},
                        },
                        {
                            "account_id": rent_account_id,
                            "amount": {"commodity_id": commodity_id, "amount": 2000},
                        },
                    ],
                }
            ),
        )

        # Filter by food account (using path)
        list_path = self._endpoint(f"/{ledger_id}?accounts=Expenses:Food")
        response = await api_client.get(list_path)
        assert response.status == 200

        result = await response.json()
        assert result["count"] == 1
        assert result["transactions"][0]["description"] == "Food expense"

    async def test_list_transactions_with_account_direction_filter(
        self,
        api_client: TestClient,
        ledger_one: Ledger,
        commodity_usd_ledger_one: Commodity,
        account_assets_cash_ledger_one: Account,
        account_incomes_salary_ledger_one: Account,
        account_expenses_food_ledger_one: Account,
    ) -> None:
        """List transactions filtered by account with direction (+ for credit, - for debit)."""
        ledger_id = str(ledger_one.id)
        commodity_id = str(commodity_usd_ledger_one.id)
        cash_account_id = str(account_assets_cash_ledger_one.id)
        income_account_id = str(account_incomes_salary_ledger_one.id)
        expense_account_id = str(account_expenses_food_ledger_one.id)

        create_path = self._endpoint(f"/{ledger_id}")

        # Transaction 1: Income -> Cash. Paycheck deposited to cash
        await api_client.post(
            create_path,
            content=JSONContent(
                data={
                    "description": "Salary",
                    "date_time": "2024-01-15T10:30:00Z",
                    "details": [
                        {
                            "account_id": income_account_id,
                            "amount": {"commodity_id": commodity_id, "amount": -5000},
                        },
                        {
                            "account_id": cash_account_id,
                            "amount": {"commodity_id": commodity_id, "amount": 5000},
                        },
                    ],
                }
            ),
        )

        # Transaction 2: Cash -> Expense. Buys food with cash
        await api_client.post(
            create_path,
            content=JSONContent(
                data={
                    "description": "Food expense",
                    "date_time": "2024-01-16T10:30:00Z",
                    "details": [
                        {
                            "account_id": cash_account_id,
                            "amount": {"commodity_id": commodity_id, "amount": -1000},
                        },
                        {
                            "account_id": expense_account_id,
                            "amount": {"commodity_id": commodity_id, "amount": 1000},
                        },
                    ],
                }
            ),
        )

        # Filter by cash account receiving money (positive amount)
        list_path = self._endpoint(f"/{ledger_id}?accounts={quote('+Assets:Cash', safe='')}")
        response = await api_client.get(list_path)
        assert response.status == 200

        result = await response.json()
        # So we expect only Transaction 1 (Salary)
        assert result["count"] == 1
        # Check that at least one transaction is Salary
        assert "Salary" in result["transactions"][0]["description"]

        # Filter by cash account paying money (negative amount)
        list_path = self._endpoint(f"/{ledger_id}?accounts={quote('-Assets:Cash', safe='')}")
        response = await api_client.get(list_path)
        assert response.status == 200

        result = await response.json()
        assert result["count"] == 1
        assert "Food expense" in result["transactions"][0]["description"]

    async def test_list_transactions_with_date_range(
        self,
        api_client: TestClient,
        ledger_one: Ledger,
        commodity_usd_ledger_one: Commodity,
        account_assets_cash_ledger_one: Account,
        account_expenses_food_ledger_one: Account,
    ) -> None:
        """List transactions filtered by date range."""
        ledger_id = str(ledger_one.id)
        commodity_id = str(commodity_usd_ledger_one.id)
        account1_id = str(account_assets_cash_ledger_one.id)
        account2_id = str(account_expenses_food_ledger_one.id)

        create_path = self._endpoint(f"/{ledger_id}")

        # Create transactions with different dates
        dates = [
            "2024-01-10T10:00:00Z",
            "2024-01-15T10:00:00Z",
            "2024-01-20T10:00:00Z",
        ]

        for i, date in enumerate(dates):
            await api_client.post(
                create_path,
                content=JSONContent(
                    data={
                        "description": f"Transaction {i}",
                        "date_time": date,
                        "details": [
                            {
                                "account_id": account1_id,
                                "amount": {"commodity_id": commodity_id, "amount": -1000},
                            },
                            {
                                "account_id": account2_id,
                                "amount": {"commodity_id": commodity_id, "amount": 1000},
                            },
                        ],
                    }
                ),
            )

        # Filter by date range: after Jan 12
        after_ts = int(datetime(2024, 1, 12, 0, 0, 0, tzinfo=timezone.utc).timestamp())
        list_path = self._endpoint(f"/{ledger_id}?after={after_ts}")
        response = await api_client.get(list_path)
        assert response.status == 200

        result = await response.json()
        assert result["count"] == 2

        # Filter by date range: before Jan 18
        before_ts = int(datetime(2024, 1, 18, 0, 0, 0, tzinfo=timezone.utc).timestamp())
        list_path = self._endpoint(f"/{ledger_id}?before={before_ts}")
        response = await api_client.get(list_path)
        assert response.status == 200

        result = await response.json()
        assert result["count"] == 2

        # Filter by date range: between Jan 12 and Jan 18
        list_path = self._endpoint(f"/{ledger_id}?after={after_ts}&before={before_ts}")
        response = await api_client.get(list_path)
        assert response.status == 200

        result = await response.json()
        assert result["count"] == 1
        assert result["transactions"][0]["description"] == "Transaction 1"

    async def test_list_transactions_with_exchange_filter(
        self,
        api_client: TestClient,
        ledger_one: Ledger,
        commodity_usd_ledger_one: Commodity,
        commodity_eur_ledger_one: Commodity,
        account_assets_cash_usd_ledger_one: Account,
        account_assets_cash_eur_ledger_one: Account,
        account_expenses_food_ledger_one: Account,
    ) -> None:
        """List transactions filtered by exchange flag."""
        ledger_id = str(ledger_one.id)
        usd_id = str(commodity_usd_ledger_one.id)
        eur_id = str(commodity_eur_ledger_one.id)
        usd_cash_id = str(account_assets_cash_usd_ledger_one.id)
        eur_cash_id = str(account_assets_cash_eur_ledger_one.id)
        expense_id = str(account_expenses_food_ledger_one.id)

        create_path = self._endpoint(f"/{ledger_id}")

        # Create regular transaction
        await api_client.post(
            create_path,
            content=JSONContent(
                data={
                    "description": "Regular expense",
                    "date_time": "2024-01-15T10:30:00Z",
                    "details": [
                        {
                            "account_id": usd_cash_id,
                            "amount": {"commodity_id": usd_id, "amount": -1000},
                        },
                        {
                            "account_id": expense_id,
                            "amount": {"commodity_id": usd_id, "amount": 1000},
                        },
                    ],
                }
            ),
        )

        # Create exchange transaction
        await api_client.post(
            create_path,
            content=JSONContent(
                data={
                    "description": "Currency exchange",
                    "date_time": "2024-01-16T10:30:00Z",
                    "details": [
                        {
                            "account_id": eur_cash_id,
                            "amount": {"commodity_id": eur_id, "amount": 9200},
                        },
                        {
                            "account_id": usd_cash_id,
                            "amount": {"commodity_id": usd_id, "amount": -10000},
                            "price": {
                                "commodity_id": eur_id,
                                "price": {"numerator": 9200, "denominator": 10000},
                            },
                        },
                    ],
                }
            ),
        )

        # Filter for exchange transactions
        list_path = self._endpoint(f"/{ledger_id}?exchange=true")
        response = await api_client.get(list_path)
        assert response.status == 200

        result = await response.json()
        assert result["count"] == 1
        assert result["transactions"][0]["description"] == "Currency exchange"

        # Filter for non-exchange transactions
        list_path = self._endpoint(f"/{ledger_id}?exchange=false")
        response = await api_client.get(list_path)
        assert response.status == 200

        result = await response.json()
        assert result["count"] == 1
        assert result["transactions"][0]["description"] == "Regular expense"

    async def test_list_transactions_with_ordering(
        self,
        api_client: TestClient,
        ledger_one: Ledger,
        commodity_usd_ledger_one: Commodity,
        account_assets_cash_ledger_one: Account,
        account_expenses_food_ledger_one: Account,
    ) -> None:
        """List transactions with different ordering."""
        ledger_id = str(ledger_one.id)
        commodity_id = str(commodity_usd_ledger_one.id)
        account1_id = str(account_assets_cash_ledger_one.id)
        account2_id = str(account_expenses_food_ledger_one.id)

        create_path = self._endpoint(f"/{ledger_id}")

        # Create transactions with different dates
        dates = ["2024-01-10T10:00:00Z", "2024-01-15T10:00:00Z", "2024-01-20T10:00:00Z"]

        for i, date in enumerate(dates):
            await api_client.post(
                create_path,
                content=JSONContent(
                    data={
                        "description": f"Transaction {i}",
                        "date_time": date,
                        "details": [
                            {
                                "account_id": account1_id,
                                "amount": {"commodity_id": commodity_id, "amount": -1000},
                            },
                            {
                                "account_id": account2_id,
                                "amount": {"commodity_id": commodity_id, "amount": 1000},
                            },
                        ],
                    }
                ),
            )

        # Default order (descending by date)
        list_path = self._endpoint(f"/{ledger_id}")
        response = await api_client.get(list_path)
        result = await response.json()
        assert result["transactions"][0]["description"] == "Transaction 2"
        assert result["transactions"][2]["description"] == "Transaction 0"

        # Ascending order
        list_path = self._endpoint(f"/{ledger_id}?order_by=%2Bdate_time")
        response = await api_client.get(list_path)
        result = await response.json()
        assert result["transactions"][0]["description"] == "Transaction 0"
        assert result["transactions"][2]["description"] == "Transaction 2"

    async def test_update_transaction(
        self,
        api_client: TestClient,
        ledger_one: Ledger,
        commodity_usd_ledger_one: Commodity,
        account_assets_cash_ledger_one: Account,
        account_expenses_food_ledger_one: Account,
    ) -> None:
        """Update a transaction."""
        ledger_id = str(ledger_one.id)
        commodity_id = str(commodity_usd_ledger_one.id)
        account1_id = str(account_assets_cash_ledger_one.id)
        account2_id = str(account_expenses_food_ledger_one.id)

        # Create transaction
        create_path = self._endpoint(f"/{ledger_id}")
        transaction_data = {
            "description": "Original description",
            "date_time": "2024-01-15T10:30:00Z",
            "details": [
                {
                    "account_id": account1_id,
                    "amount": {"commodity_id": commodity_id, "amount": -1000},
                },
                {
                    "account_id": account2_id,
                    "amount": {"commodity_id": commodity_id, "amount": 1000},
                },
            ],
            "state": "uncleared",
        }

        create_response = await api_client.post(create_path, content=JSONContent(data=transaction_data))
        assert create_response.status == 200
        created = await create_response.json()
        transaction_id = created["id"]

        # Wait a moment to ensure updated_at will be different
        await asyncio.sleep(0.01)

        # Update transaction
        update_path = self._endpoint(f"/{ledger_id}/{transaction_id}")
        update_data = {
            "description": "Updated description",
            "state": "cleared",
        }

        update_response = await api_client.put(update_path, content=JSONContent(data=update_data))
        assert update_response.status == 200

        updated = await update_response.json()
        assert updated["id"] == transaction_id
        assert updated["description"] == "Updated description"
        assert updated["state"] == "cleared"
        assert b"ETag" in update_response.headers

    async def test_update_transaction_with_etag(
        self,
        api_client: TestClient,
        ledger_one: Ledger,
        commodity_usd_ledger_one: Commodity,
        account_assets_cash_ledger_one: Account,
        account_expenses_food_ledger_one: Account,
    ) -> None:
        """Update a transaction using ETag for optimistic locking."""
        ledger_id = str(ledger_one.id)
        commodity_id = str(commodity_usd_ledger_one.id)
        account1_id = str(account_assets_cash_ledger_one.id)
        account2_id = str(account_expenses_food_ledger_one.id)

        # Create transaction
        create_path = self._endpoint(f"/{ledger_id}")
        transaction_data = {
            "description": "Original",
            "date_time": "2024-01-15T10:30:00Z",
            "details": [
                {
                    "account_id": account1_id,
                    "amount": {"commodity_id": commodity_id, "amount": -1000},
                },
                {
                    "account_id": account2_id,
                    "amount": {"commodity_id": commodity_id, "amount": 1000},
                },
            ],
        }

        await asyncio.sleep(0.1)

        create_response = await api_client.post(create_path, content=JSONContent(data=transaction_data))
        created = await create_response.json()
        transaction_id = created["id"]
        original_etag = create_response.headers.get(b"ETag")[0].decode("utf-8")  # type: ignore

        # Update with the original ETag - should succeed
        update_path = self._endpoint(f"/{ledger_id}/{transaction_id}")
        first_update = await api_client.put(
            update_path,
            content=JSONContent(data={"description": "First update"}),
            headers={"If-Match": original_etag},
        )
        assert first_update.status == 200
        assert first_update.headers.get(b"ETag") is not None
        assert first_update.headers.get(b"ETag")[0].decode("utf-8") != original_etag  # type: ignore

        stale_update = await api_client.put(
            update_path,
            content=JSONContent(data={"description": "Should fail"}),
            headers={"If-Match": original_etag},
        )
        assert stale_update.status == 412

    async def test_delete_transaction(
        self,
        api_client: TestClient,
        ledger_one: Ledger,
        commodity_usd_ledger_one: Commodity,
        account_assets_cash_ledger_one: Account,
        account_expenses_food_ledger_one: Account,
    ) -> None:
        """Delete a transaction."""
        ledger_id = str(ledger_one.id)
        commodity_id = str(commodity_usd_ledger_one.id)
        account1_id = str(account_assets_cash_ledger_one.id)
        account2_id = str(account_expenses_food_ledger_one.id)

        # Create transaction
        create_path = self._endpoint(f"/{ledger_id}")
        transaction_data = {
            "description": "To be deleted",
            "date_time": "2024-01-15T10:30:00Z",
            "details": [
                {
                    "account_id": account1_id,
                    "amount": {"commodity_id": commodity_id, "amount": -1000},
                },
                {
                    "account_id": account2_id,
                    "amount": {"commodity_id": commodity_id, "amount": 1000},
                },
            ],
        }

        create_response = await api_client.post(create_path, content=JSONContent(data=transaction_data))
        created = await create_response.json()
        transaction_id = created["id"]

        # Delete transaction
        delete_path = self._endpoint(f"/{ledger_id}/{transaction_id}")
        delete_response = await api_client.delete(delete_path)
        assert delete_response.status in (200, 204)

        # Verify deletion
        get_response = await api_client.get(delete_path)
        assert get_response.status == 404

    async def test_delete_transaction_with_etag(
        self,
        api_client: TestClient,
        ledger_one: Ledger,
        commodity_usd_ledger_one: Commodity,
        account_assets_cash_ledger_one: Account,
        account_expenses_food_ledger_one: Account,
    ) -> None:
        """Delete a transaction using ETag for optimistic locking."""
        ledger_id = str(ledger_one.id)
        commodity_id = str(commodity_usd_ledger_one.id)
        account1_id = str(account_assets_cash_ledger_one.id)
        account2_id = str(account_expenses_food_ledger_one.id)

        # Create transaction
        create_path = self._endpoint(f"/{ledger_id}")
        transaction_data = {
            "description": "To be deleted",
            "date_time": "2024-01-15T10:30:00Z",
            "details": [
                {
                    "account_id": account1_id,
                    "amount": {"commodity_id": commodity_id, "amount": -1000},
                },
                {
                    "account_id": account2_id,
                    "amount": {"commodity_id": commodity_id, "amount": 1000},
                },
            ],
        }

        create_response = await api_client.post(create_path, content=JSONContent(data=transaction_data))
        created = await create_response.json()
        transaction_id = created["id"]
        etag: str = create_response.headers.get(b"ETag")[0].decode("utf-8")  # type: ignore

        # Update transaction to change ETag
        await asyncio.sleep(0.01)
        update_path = self._endpoint(f"/{ledger_id}/{transaction_id}")
        await api_client.put(update_path, content=JSONContent(data={"description": "Updated"}))

        # Try to delete with old ETag (should fail)
        delete_path = self._endpoint(f"/{ledger_id}/{transaction_id}")
        delete_response = await api_client.delete(delete_path, headers=[(b"If-Match", etag.encode())])
        assert delete_response.status == 412

    async def test_create_transaction_with_empty_details_fails(
        self,
        api_client: TestClient,
        ledger_one: Ledger,
    ) -> None:
        """Creating a transaction with empty details should return 400."""
        ledger_id = str(ledger_one.id)

        path = self._endpoint(f"/{ledger_id}")
        transaction_data = {
            "description": "Empty details",
            "date_time": "2024-01-15T10:30:00Z",
            "details": [],
        }

        response = await api_client.post(path, content=JSONContent(data=transaction_data))
        assert response.status == 400

    async def test_create_transaction_for_nonexistent_ledger_fails(self, api_client: TestClient) -> None:
        """Creating a transaction for a nonexistent ledger should return 404 or 400."""
        # Using UUID4 instead of UUID7 will fail validation, returning 400
        # This is expected behavior - validation happens before ledger existence check
        fake_ledger_id = "01234567-89ab-7def-0123-456789abcdef"

        path = self._endpoint(f"/{fake_ledger_id}")
        transaction_data = {
            "description": "Should fail",
            "date_time": "2024-01-15T10:30:00Z",
            "details": [
                {
                    "account_id": "01234567-89ab-7def-0123-456789abcdef",
                    "amount": {
                        "commodity_id": "01234567-89ab-7def-0123-456789abcdef",
                        "amount": 1000,
                    },
                }
            ],
        }

        response = await api_client.post(path, content=JSONContent(data=transaction_data))
        # Should return 400 due to UUID version validation
        assert response.status == 400

    async def test_transaction_state_transitions(
        self,
        api_client: TestClient,
        ledger_one: Ledger,
        commodity_usd_ledger_one: Commodity,
        account_assets_cash_ledger_one: Account,
        account_expenses_food_ledger_one: Account,
    ) -> None:
        """Test transaction state changes from uncleared to pending to cleared."""
        ledger_id = str(ledger_one.id)
        commodity_id = str(commodity_usd_ledger_one.id)
        account1_id = str(account_assets_cash_ledger_one.id)
        account2_id = str(account_expenses_food_ledger_one.id)

        # Create uncleared transaction
        create_path = self._endpoint(f"/{ledger_id}")
        transaction_data = {
            "description": "State transition test",
            "date_time": "2024-01-15T10:30:00Z",
            "details": [
                {
                    "account_id": account1_id,
                    "amount": {"commodity_id": commodity_id, "amount": -1000},
                },
                {
                    "account_id": account2_id,
                    "amount": {"commodity_id": commodity_id, "amount": 1000},
                },
            ],
            "state": "uncleared",
        }

        create_response = await api_client.post(create_path, content=JSONContent(data=transaction_data))
        created = await create_response.json()
        transaction_id = created["id"]
        assert created["state"] == "uncleared"

        # Update to pending
        await asyncio.sleep(0.01)
        update_path = self._endpoint(f"/{ledger_id}/{transaction_id}")
        await api_client.put(update_path, content=JSONContent(data={"state": "pending"}))

        get_response = await api_client.get(update_path)
        transaction = await get_response.json()
        assert transaction["state"] == "pending"

        # Update to cleared
        await asyncio.sleep(0.01)
        await api_client.put(update_path, content=JSONContent(data={"state": "cleared"}))

        get_response = await api_client.get(update_path)
        transaction = await get_response.json()
        assert transaction["state"] == "cleared"
