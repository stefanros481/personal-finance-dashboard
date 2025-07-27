"""Simple tests for authentication functionality."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.rate_limiting import RateLimitService
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    validate_password_strength,
    verify_password,
)


class TestSecurityFunctions:
    """Test security utility functions."""

    def test_password_strength_validation_valid(self):
        """Test password strength validation with valid password."""
        result = validate_password_strength("SecurePass123!")
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0

    def test_password_strength_validation_too_short(self):
        """Test password strength validation with short password."""
        result = validate_password_strength("Short1!")
        assert result["is_valid"] is False
        assert any("at least 8 characters" in error for error in result["errors"])

    def test_password_strength_validation_missing_requirements(self):
        """Test password strength validation missing requirements."""
        result = validate_password_strength("lowercase123")
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0
        assert any("uppercase" in error for error in result["errors"])
        assert any("special character" in error for error in result["errors"])

    def test_password_hashing_and_verification(self):
        """Test password hashing and verification."""
        password = "TestPassword123!"
        hashed = get_password_hash(password)

        # Verify correct password
        assert verify_password(password, hashed) is True

        # Verify incorrect password
        assert verify_password("WrongPassword", hashed) is False

    def test_access_token_creation(self):
        """Test access token creation."""
        token = create_access_token({"sub": "test@example.com"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_refresh_token_creation(self):
        """Test refresh token creation."""
        token = create_refresh_token("user-id-123")
        assert isinstance(token, str)
        assert len(token) > 0


class TestRateLimitingServiceUnit:
    """Test rate limiting service unit functions."""

    @pytest.fixture
    def rate_limit_service(self):
        """Rate limiting service fixture."""
        return RateLimitService()

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    @patch("app.services.cache_service.cache_service.exists")
    async def test_is_rate_limited_locked_account(
        self, mock_cache_exists, rate_limit_service
    ):
        """Test that locked account is rate limited."""
        mock_cache_exists.return_value = True

        result = await rate_limit_service.is_rate_limited("test@example.com")
        assert result is True

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
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

        # Should call set for both attempt count and potentially lockout
        assert mock_cache_set.called

    @pytest.mark.asyncio
    @patch("app.services.cache_service.cache_service.delete")
    async def test_record_successful_attempt(
        self, mock_cache_delete, rate_limit_service
    ):
        """Test recording successful attempt clears counters."""
        mock_cache_delete.return_value = True

        await rate_limit_service.record_successful_attempt("test@example.com")

        # Should call delete twice (attempts and lockout keys)
        assert mock_cache_delete.call_count == 2


class TestAuthSchemas:
    """Test authentication schemas."""

    def test_login_request_validation(self):
        """Test login request schema validation."""
        from app.schemas.auth import LoginRequest

        # Valid request
        valid_request = LoginRequest(
            email="test@example.com", password="SecurePass123!"
        )
        assert valid_request.email == "test@example.com"
        assert valid_request.password == "SecurePass123!"

        # Test email validation
        with pytest.raises(ValueError):
            LoginRequest(email="invalid-email", password="SecurePass123!")

        # Test password length validation
        with pytest.raises(ValueError):
            LoginRequest(email="test@example.com", password="short")  # Too short

    def test_token_response_schema(self):
        """Test token response schema."""
        from app.schemas.auth import LoginResponse

        response = LoginResponse(
            access_token="access-token-123",
            refresh_token="refresh-token-123",
            token_type="bearer",
            expires_in=1800,
            user={"id": "user-123", "email": "test@example.com", "is_active": True},
        )

        assert response.access_token == "access-token-123"
        assert response.refresh_token == "refresh-token-123"
        assert response.token_type == "bearer"
        assert response.expires_in == 1800
        assert response.user["email"] == "test@example.com"
