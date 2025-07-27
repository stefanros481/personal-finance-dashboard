"""Redis caching service for the application."""

import json
import logging
from datetime import timedelta
from typing import Any, Optional

import redis
from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching service."""

    def __init__(self):
        """Initialize the cache service."""
        self._redis: Optional[Redis] = None
        self._connected = False

    def _get_redis_client(self) -> Redis:
        """Get Redis client, creating connection if needed."""
        if self._redis is None:
            try:
                self._redis = redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
                # Test connection
                self._redis.ping()
                self._connected = True
                logger.info("Successfully connected to Redis")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
                self._connected = False
                # Return a mock client that doesn't cache anything
                return self._create_fallback_client()

        return self._redis

    def _create_fallback_client(self):
        """Create a fallback client that doesn't actually cache."""

        class FallbackClient:
            """Fallback client when Redis is unavailable."""

            def get(self, key: str) -> None:
                return None

            def set(self, key: str, value: str, ex: int = None) -> bool:
                return True

            def delete(self, key: str) -> int:
                return 0

            def exists(self, key: str) -> int:
                return 0

            def ping(self) -> bool:
                return False

        logger.warning("Using fallback cache client - caching disabled")
        return FallbackClient()

    def _generate_key(self, prefix: str, identifier: str) -> str:
        """Generate a standardized cache key."""
        return f"{settings.APP_NAME.lower().replace(' ', '_')}:{prefix}:{identifier}"

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        try:
            client = self._get_redis_client()
            cached_value = client.get(key)

            if cached_value is None:
                logger.debug(f"Cache miss for key: {key}")
                return None

            # Try to deserialize JSON
            try:
                value = json.loads(cached_value)
                logger.debug(f"Cache hit for key: {key}")
                return value
            except json.JSONDecodeError:
                # Return as string if not JSON
                logger.debug(f"Cache hit (string) for key: {key}")
                return cached_value

        except RedisError as e:
            logger.error(f"Redis error getting key {key}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting cache key {key}: {str(e)}")
            return None

    async def set(
        self, key: str, value: Any, ttl_seconds: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds (default: CACHE_EXPIRE_MINUTES)

        Returns:
            True if successful, False otherwise
        """
        try:
            client = self._get_redis_client()

            # Default TTL from settings
            if ttl_seconds is None:
                ttl_seconds = settings.CACHE_EXPIRE_MINUTES * 60

            # Serialize value to JSON
            if isinstance(value, (dict, list, tuple)):
                cached_value = json.dumps(value, default=str)
            else:
                cached_value = str(value)

            result = client.set(key, cached_value, ex=ttl_seconds)

            if result:
                logger.debug(f"Cached key: {key} (TTL: {ttl_seconds}s)")
            else:
                logger.warning(f"Failed to cache key: {key}")

            return bool(result)

        except RedisError as e:
            logger.error(f"Redis error setting key {key}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error setting cache key {key}: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted, False if key didn't exist or error occurred
        """
        try:
            client = self._get_redis_client()
            result = client.delete(key)

            if result > 0:
                logger.debug(f"Deleted cache key: {key}")
                return True
            else:
                logger.debug(f"Cache key not found: {key}")
                return False

        except RedisError as e:
            logger.error(f"Redis error deleting key {key}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting cache key {key}: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists, False otherwise
        """
        try:
            client = self._get_redis_client()
            result = client.exists(key)
            return bool(result)

        except RedisError as e:
            logger.error(f"Redis error checking key {key}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking cache key {key}: {str(e)}")
            return False

    def generate_stock_price_key(self, ticker: str) -> str:
        """Generate cache key for stock price data."""
        return self._generate_key("stock_price", ticker.upper())

    def generate_stock_search_key(self, query: str) -> str:
        """Generate cache key for stock search results."""
        return self._generate_key("stock_search", query.lower())

    def generate_stock_history_key(
        self, ticker: str, period: str, interval: str
    ) -> str:
        """Generate cache key for historical stock data."""
        return self._generate_key(
            "stock_history", f"{ticker.upper()}_{period}_{interval}"
        )

    async def health_check(self) -> bool:
        """
        Check if Redis connection is healthy.

        Returns:
            True if Redis is accessible, False otherwise
        """
        try:
            client = self._get_redis_client()
            result = client.ping()
            return bool(result)
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return False


# Global cache service instance
cache_service = CacheService()
