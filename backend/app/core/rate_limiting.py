"""Rate limiting service for authentication endpoints."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


class RateLimitService:
    """Service for implementing rate limiting on authentication endpoints."""

    def __init__(self):
        self.login_attempts_prefix = "login_attempts"
        self.max_login_attempts = 5
        self.lockout_duration_minutes = 15
        self.rate_limit_window_minutes = 5

    async def is_rate_limited(self, identifier: str) -> bool:
        """
        Check if identifier (IP or email) is rate limited.

        Args:
            identifier: IP address or email to check

        Returns:
            True if rate limited, False otherwise
        """
        # Check if account is locked out
        lockout_key = f"{self.login_attempts_prefix}:lockout:{identifier}"
        is_locked = await cache_service.exists(lockout_key)

        if is_locked:
            logger.warning(f"Login attempt blocked - account locked: {identifier}")
            return True

        # Check current attempt count in the rate limit window
        attempts_key = f"{self.login_attempts_prefix}:count:{identifier}"
        current_attempts = await cache_service.get(attempts_key)

        if current_attempts is None:
            current_attempts = 0
        else:
            current_attempts = int(current_attempts)

        if current_attempts >= self.max_login_attempts:
            logger.warning(f"Login attempt blocked - rate limited: {identifier}")
            return True

        return False

    async def record_failed_attempt(self, identifier: str) -> int:
        """
        Record a failed login attempt.

        Args:
            identifier: IP address or email

        Returns:
            Current number of failed attempts
        """
        attempts_key = f"{self.login_attempts_prefix}:count:{identifier}"
        current_attempts = await cache_service.get(attempts_key)

        if current_attempts is None:
            current_attempts = 0
        else:
            current_attempts = int(current_attempts)

        current_attempts += 1

        # Store attempt count with expiration
        window_seconds = self.rate_limit_window_minutes * 60
        await cache_service.set(
            attempts_key, current_attempts, ttl_seconds=window_seconds
        )

        # If max attempts reached, lock the account
        if current_attempts >= self.max_login_attempts:
            lockout_key = f"{self.login_attempts_prefix}:lockout:{identifier}"
            lockout_seconds = self.lockout_duration_minutes * 60
            await cache_service.set(lockout_key, "locked", ttl_seconds=lockout_seconds)

            logger.warning(
                f"Account locked due to {current_attempts} failed attempts: {identifier}"
            )

        logger.info(
            f"Failed login attempt recorded: {identifier} ({current_attempts}/{self.max_login_attempts})"
        )
        return current_attempts

    async def record_successful_attempt(self, identifier: str) -> None:
        """
        Record a successful login attempt and clear any rate limiting.

        Args:
            identifier: IP address or email
        """
        attempts_key = f"{self.login_attempts_prefix}:count:{identifier}"
        lockout_key = f"{self.login_attempts_prefix}:lockout:{identifier}"

        # Clear attempt counter and lockout
        await cache_service.delete(attempts_key)
        await cache_service.delete(lockout_key)

        logger.info(f"Successful login - cleared rate limiting: {identifier}")

    async def get_remaining_attempts(self, identifier: str) -> int:
        """
        Get remaining login attempts before rate limiting.

        Args:
            identifier: IP address or email

        Returns:
            Number of remaining attempts
        """
        attempts_key = f"{self.login_attempts_prefix}:count:{identifier}"
        current_attempts = await cache_service.get(attempts_key)

        if current_attempts is None:
            return self.max_login_attempts

        remaining = self.max_login_attempts - int(current_attempts)
        return max(0, remaining)

    async def get_lockout_time_remaining(self, identifier: str) -> Optional[int]:
        """
        Get remaining lockout time in seconds.

        Args:
            identifier: IP address or email

        Returns:
            Remaining lockout time in seconds, or None if not locked
        """
        lockout_key = f"{self.login_attempts_prefix}:lockout:{identifier}"
        is_locked = await cache_service.exists(lockout_key)

        if not is_locked:
            return None

        # For simplicity, return the configured lockout duration
        # In a more sophisticated implementation, we could store the exact lockout time
        return self.lockout_duration_minutes * 60


# Global rate limiting service instance
rate_limit_service = RateLimitService()
