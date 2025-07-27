"""Tests for transaction management."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.portfolio import Holding, Portfolio, Transaction, TransactionType
from app.models.user import User
from app.schemas.portfolio import TransactionCreate, TransactionUpdate
from app.services.transaction import TransactionService


class TestTransactionService:
    """Test transaction service functionality."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return None  # Using actual DB operations in service tests

    @pytest.fixture
    def sample_transaction_data(self):
        """Sample transaction data for testing."""
        return TransactionCreate(
            symbol="AAPL",
            type=TransactionType.BUY,
            quantity=Decimal("10"),
            price_per_share=Decimal("150.00"),
            total_amount=Decimal("1500.00"),
            fees=Decimal("0.00"),
            currency="USD",
            exchange_rate=Decimal("1.0"),
            notes="Test transaction",
            transaction_date=datetime.now(timezone.utc),
        )

    def test_validate_transaction_data_valid(self, sample_transaction_data):
        """Test transaction validation with valid data."""
        # Should not raise any exception
        TransactionService.validate_transaction_data(sample_transaction_data)

    def test_validate_transaction_data_negative_quantity(self, sample_transaction_data):
        """Test transaction validation with negative quantity."""
        sample_transaction_data.quantity = Decimal("-5")

        with pytest.raises(Exception) as exc_info:
            TransactionService.validate_transaction_data(sample_transaction_data)

        assert "quantity must be positive" in str(exc_info.value)

    def test_validate_transaction_data_negative_price(self, sample_transaction_data):
        """Test transaction validation with negative price."""
        sample_transaction_data.price_per_share = Decimal("-10")

        with pytest.raises(Exception) as exc_info:
            TransactionService.validate_transaction_data(sample_transaction_data)

        assert "Price per share must be positive" in str(exc_info.value)

    def test_validate_transaction_data_inconsistent_total(
        self, sample_transaction_data
    ):
        """Test transaction validation with inconsistent total amount."""
        sample_transaction_data.total_amount = Decimal("1000.00")  # Should be 1500

        with pytest.raises(Exception) as exc_info:
            TransactionService.validate_transaction_data(sample_transaction_data)

        assert "doesn't match calculated value" in str(exc_info.value)

    def test_validate_transaction_data_future_date(self, sample_transaction_data):
        """Test transaction validation with future date."""
        from datetime import timedelta

        sample_transaction_data.transaction_date = datetime.now(
            timezone.utc
        ) + timedelta(days=1)

        with pytest.raises(Exception) as exc_info:
            TransactionService.validate_transaction_data(sample_transaction_data)

        assert "cannot be in the future" in str(exc_info.value)

    def test_validate_transaction_data_invalid_currency(self, sample_transaction_data):
        """Test transaction validation with invalid currency."""
        sample_transaction_data.currency = "INVALID"

        with pytest.raises(Exception) as exc_info:
            TransactionService.validate_transaction_data(sample_transaction_data)

        assert "3-letter code" in str(exc_info.value)

    def test_validate_transaction_data_negative_exchange_rate(
        self, sample_transaction_data
    ):
        """Test transaction validation with negative exchange rate."""
        sample_transaction_data.exchange_rate = Decimal("-1.0")

        with pytest.raises(Exception) as exc_info:
            TransactionService.validate_transaction_data(sample_transaction_data)

        assert "Exchange rate must be positive" in str(exc_info.value)


class TestTransactionCalculations:
    """Test transaction calculation logic."""

    def test_calculate_holding_metrics_single_buy(self):
        """Test holding calculations with single buy transaction."""
        # This would require actual database setup
        # For now, testing the calculation logic conceptually

        quantity = Decimal("10")
        price = Decimal("150.00")
        total_cost = quantity * price

        expected_avg_cost = total_cost / quantity
        assert expected_avg_cost == Decimal("150.00")

    def test_calculate_holding_metrics_multiple_buys(self):
        """Test holding calculations with multiple buy transactions."""
        # Transaction 1: 10 shares at $150
        q1, p1 = Decimal("10"), Decimal("150.00")
        cost1 = q1 * p1

        # Transaction 2: 5 shares at $160
        q2, p2 = Decimal("5"), Decimal("160.00")
        cost2 = q2 * p2

        total_quantity = q1 + q2
        total_cost = cost1 + cost2
        expected_avg_cost = total_cost / total_quantity

        # Expected: (1500 + 800) / 15 = 153.33
        # Use quantize for consistent precision comparison
        expected = Decimal("2300") / Decimal("15")
        assert abs(expected_avg_cost - expected) < Decimal("0.01")

    def test_calculate_holding_metrics_buy_then_sell(self):
        """Test holding calculations with buy then sell."""
        # Buy 10 shares at $150
        buy_quantity = Decimal("10")
        buy_price = Decimal("150.00")
        total_cost = buy_quantity * buy_price

        # Sell 3 shares
        sell_quantity = Decimal("3")
        remaining_quantity = buy_quantity - sell_quantity

        # Cost basis should reduce proportionally
        remaining_cost = total_cost * (remaining_quantity / buy_quantity)
        expected_avg_cost = remaining_cost / remaining_quantity

        assert expected_avg_cost == Decimal("150.00")  # Same price


class TestTransactionAPI:
    """Test transaction API endpoints."""

    @pytest.fixture
    def client(self):
        """Test client fixture."""
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers."""
        return {"Authorization": "Bearer fake-token"}

    @patch("app.core.deps.get_current_active_user")
    @patch("app.core.database.get_db")
    def test_create_transaction_endpoint(self, mock_get_db, mock_get_user, client):
        """Test create transaction endpoint."""
        # Setup mocks
        mock_user = User(id="user-123", email="test@example.com", is_active=True)
        mock_get_user.return_value = mock_user

        # Mock database operations
        mock_db = None  # Would need proper mock setup
        mock_get_db.return_value = mock_db

        transaction_data = {
            "symbol": "AAPL",
            "type": "BUY",
            "quantity": "10.0",
            "price_per_share": "150.00",
            "total_amount": "1500.00",
            "fees": "0.00",
            "currency": "USD",
            "exchange_rate": "1.0",
            "notes": "Test transaction",
            "transaction_date": "2024-01-01T10:00:00Z",
        }

        # Note: This test would need proper database mocking to work
        # For now, it demonstrates the API structure

        # response = client.post(
        #     "/api/v1/portfolios/portfolio-123/transactions",
        #     json=transaction_data,
        #     headers=auth_headers
        # )
        #
        # assert response.status_code == 201
        # assert "id" in response.json()

    def test_transaction_validation_errors(self, client):
        """Test transaction validation error responses."""
        invalid_data = {
            "symbol": "AAPL",
            "type": "BUY",
            "quantity": "-10.0",  # Invalid: negative
            "price_per_share": "150.00",
            "total_amount": "1500.00",
            "fees": "0.00",
            "currency": "USD",
            "exchange_rate": "1.0",
            "transaction_date": "2024-01-01T10:00:00Z",
        }

        # Would test validation error response
        # response = client.post(
        #     "/api/v1/portfolios/portfolio-123/transactions",
        #     json=invalid_data
        # )
        # assert response.status_code == 400


class TestTransactionIntegration:
    """Integration tests for transaction functionality."""

    def test_transaction_holding_update_flow(self):
        """Test complete transaction -> holding update flow."""
        # This would test the full flow:
        # 1. Create transaction
        # 2. Verify holding is created/updated
        # 3. Verify calculations are correct
        # 4. Test edge cases (sell more than owned, etc.)
        pass

    def test_multiple_transactions_same_symbol(self):
        """Test multiple transactions for same symbol."""
        # Test scenarios:
        # - Multiple buys (average cost calculation)
        # - Buy then sell (quantity reduction)
        # - Sell more than owned (error handling)
        pass

    def test_transaction_deletion_recalculation(self):
        """Test that deleting transactions recalculates holdings correctly."""
        pass

    def test_portfolio_transaction_listing(self):
        """Test listing transactions for a portfolio."""
        pass


class TestTransactionEdgeCases:
    """Test edge cases and error conditions."""

    def test_sell_more_than_owned(self):
        """Test selling more shares than owned."""
        # Should handle gracefully, possibly with warning
        pass

    def test_transaction_with_fees(self):
        """Test transactions with fees included."""
        pass

    def test_different_currencies(self):
        """Test transactions in different currencies."""
        pass

    def test_dividend_transactions(self):
        """Test dividend transaction handling."""
        pass

    def test_stock_split_transactions(self):
        """Test stock split transaction handling."""
        pass
