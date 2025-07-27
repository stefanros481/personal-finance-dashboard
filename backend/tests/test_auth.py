"""Tests for authentication endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_refresh_token, get_password_hash
from app.main import app
from app.models.user import User


class TestAuthEndpoints:
    """Test authentication endpoints."""

    @pytest.fixture
    def client(self):
        """Test client fixture."""
        return TestClient(app)

    @pytest.fixture
    def test_user_data(self):
        """Test user data fixture."""
        return {
            "email": "test@example.com",
            "password": "TestPass123!",
            "hashed_password": get_password_hash("TestPass123!"),
        }

    @pytest.fixture
    def mock_user(self, test_user_data):
        """Mock user fixture."""
        user = User(
            id="test-user-id",
            email=test_user_data["email"],
            hashed_password=test_user_data["hashed_password"],
            is_active=True,
        )
        return user

    @patch("app.api.v1.endpoints.auth.get_db")
    @patch("app.services.user.authenticate_user")
    @patch("app.core.rate_limiting.rate_limit_service.is_rate_limited")
    @patch("app.core.rate_limiting.rate_limit_service.record_successful_attempt")
    @patch("app.services.user.update_user_login_info")
    def test_successful_login(
        self,
        mock_update_login,
        mock_record_success,
        mock_rate_limited,
        mock_authenticate,
        mock_get_db,
        client,
        mock_user,
    ):
        """Test successful login."""
        # Setup mocks
        mock_rate_limited.return_value = False
        mock_authenticate.return_value = mock_user
        mock_record_success.return_value = None
        mock_update_login.return_value = None

        # Make login request
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "TestPass123!"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"

    @patch("app.services.user.authenticate_user")
    @patch("app.core.rate_limiting.rate_limit_service.is_rate_limited")
    @patch("app.core.rate_limiting.rate_limit_service.record_failed_attempt")
    @patch("app.core.rate_limiting.rate_limit_service.get_remaining_attempts")
    def test_failed_login_invalid_credentials(
        self,
        mock_remaining_attempts,
        mock_record_failed,
        mock_rate_limited,
        mock_authenticate,
        client,
    ):
        """Test failed login with invalid credentials."""
        # Setup mocks
        mock_rate_limited.return_value = False
        mock_authenticate.return_value = None
        mock_record_failed.return_value = None
        mock_remaining_attempts.return_value = 4

        # Make login request with wrong password
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "WrongPassword123!"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        # Assertions
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["error"] == "invalid_credentials"
        assert data["detail"]["message"] == "Incorrect email or password"
        assert data["detail"]["remaining_attempts"] == 4

    @patch("app.core.rate_limiting.rate_limit_service.is_rate_limited")
    @patch("app.core.rate_limiting.rate_limit_service.get_remaining_attempts")
    @patch("app.core.rate_limiting.rate_limit_service.get_lockout_time_remaining")
    def test_rate_limited_login(
        self, mock_lockout_time, mock_remaining_attempts, mock_rate_limited, client
    ):
        """Test rate limited login."""
        # Setup mocks
        mock_rate_limited.return_value = True
        mock_remaining_attempts.return_value = 0
        mock_lockout_time.return_value = 900  # 15 minutes

        # Make login request
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "TestPass123!"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        # Assertions
        assert response.status_code == 429
        data = response.json()
        assert data["detail"]["error"] == "too_many_attempts"
        assert "lockout_time_seconds" in data["detail"]

    @patch("app.core.security.verify_refresh_token")
    @patch("app.services.user.get_user")
    def test_successful_token_refresh(
        self, mock_get_user, mock_verify_refresh, client, mock_user
    ):
        """Test successful token refresh."""
        # Setup mocks
        mock_verify_refresh.return_value = "test-user-id"
        mock_get_user.return_value = mock_user

        refresh_token = create_refresh_token("test-user-id")

        # Make refresh request
        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    @patch("app.core.security.verify_refresh_token")
    def test_invalid_refresh_token(self, mock_verify_refresh, client):
        """Test refresh with invalid token."""
        # Setup mocks
        mock_verify_refresh.return_value = None

        # Make refresh request with invalid token
        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "invalid-token"}
        )

        # Assertions
        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["error"] == "invalid_refresh_token"

    @patch("app.core.deps.get_current_active_user")
    @patch("app.core.security.blacklist_refresh_token")
    def test_logout(self, mock_blacklist, mock_get_user, client, mock_user):
        """Test logout endpoint."""
        # Setup mocks
        mock_get_user.return_value = mock_user
        mock_blacklist.return_value = True

        # Make logout request
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": "Bearer fake-token"},
            params={"refresh_token": "fake-refresh-token"},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully logged out"

    @patch("app.core.deps.get_current_active_user")
    def test_get_current_user(self, mock_get_user, client, mock_user):
        """Test get current user endpoint."""
        # Setup mocks
        mock_get_user.return_value = mock_user

        # Make request
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer fake-token"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["is_active"] is True


class TestRateLimitingService:
    """Test rate limiting service."""

    @pytest.fixture
    def rate_limit_service(self):
        """Rate limiting service fixture."""
        from app.core.rate_limiting import RateLimitService

        return RateLimitService()

    @patch("app.services.cache_service.cache_service.exists")
    @patch("app.services.cache_service.cache_service.get")
    async def test_is_not_rate_limited(
        self, mock_cache_get, mock_cache_exists, rate_limit_service
    ):
        """Test that new identifier is not rate limited."""
        mock_cache_exists.return_value = False
        mock_cache_get.return_value = None

        result = await rate_limit_service.is_rate_limited("test@example.com")
        assert result is False

    @patch("app.services.cache_service.cache_service.exists")
    async def test_is_rate_limited_locked_account(
        self, mock_cache_exists, rate_limit_service
    ):
        """Test that locked account is rate limited."""
        mock_cache_exists.return_value = True

        result = await rate_limit_service.is_rate_limited("test@example.com")
        assert result is True

    @patch("app.services.cache_service.cache_service.exists")
    @patch("app.services.cache_service.cache_service.get")
    async def test_is_rate_limited_max_attempts(
        self, mock_cache_get, mock_cache_exists, rate_limit_service
    ):
        """Test that max attempts triggers rate limiting."""
        mock_cache_exists.return_value = False
        mock_cache_get.return_value = 5  # Max attempts reached

        result = await rate_limit_service.is_rate_limited("test@example.com")
        assert result is True

    @patch("app.services.cache_service.cache_service.get")
    @patch("app.services.cache_service.cache_service.set")
    async def test_record_failed_attempt(
        self, mock_cache_set, mock_cache_get, rate_limit_service
    ):
        """Test recording failed attempt."""
        mock_cache_get.return_value = 2
        mock_cache_set.return_value = True

        result = await rate_limit_service.record_failed_attempt("test@example.com")
        assert result == 3

    @patch("app.services.cache_service.cache_service.delete")
    async def test_record_successful_attempt(
        self, mock_cache_delete, rate_limit_service
    ):
        """Test recording successful attempt clears counters."""
        mock_cache_delete.return_value = True

        await rate_limit_service.record_successful_attempt("test@example.com")
        # Should call delete twice (attempts and lockout keys)
        assert mock_cache_delete.call_count == 2


class TestSecurityFunctions:
    """Test security utility functions."""

    def test_password_strength_validation_valid(self):
        """Test password strength validation with valid password."""
        from app.core.security import validate_password_strength

        result = validate_password_strength("SecurePass123!")
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0

    def test_password_strength_validation_too_short(self):
        """Test password strength validation with short password."""
        from app.core.security import validate_password_strength

        result = validate_password_strength("Short1!")
        assert result["is_valid"] is False
        assert "at least 8 characters" in str(result["errors"])

    def test_password_strength_validation_missing_requirements(self):
        """Test password strength validation missing requirements."""
        from app.core.security import validate_password_strength

        result = validate_password_strength("lowercase123")
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0
        assert any("uppercase" in error for error in result["errors"])
        assert any("special character" in error for error in result["errors"])
