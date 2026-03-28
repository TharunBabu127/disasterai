"""
Caching utilities for DisasterAI.
Provides time-based and size-based caching mechanisms.
"""

import time
import hashlib
import pickle
from functools import wraps, lru_cache
from typing import Any, Callable, Dict, Tuple, Optional
from pathlib import Path
import json


class TimedCache:
    """
    Time-based in-memory cache with TTL support.
    """

    def __init__(self, ttl: int = 300):
        """
        Initialize cache with TTL (time-to-live) in seconds.

        Args:
            ttl: Default TTL for cache entries in seconds
        """
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if expired/missing
        """
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                return value
            else:
                # Expired, remove it
                del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set cache value with optional custom TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional custom TTL in seconds
        """
        expiry = time.time() + (ttl or self._ttl)
        self._cache[key] = (value, expiry)

    def invalidate(self, key: str):
        """Remove specific key from cache."""
        if key in self._cache:
            del self._cache[key]

    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        now = time.time()
        active = sum(1 for _, ts in self._cache.values() if now - ts < self._ttl)
        expired = len(self._cache) - active
        return {
            "total": len(self._cache),
            "active": active,
            "expired": expired,
            "ttl": self._ttl
        }


# Global cache instances
geocode_cache = TimedCache(ttl=3600)  # Cache geocoding for 1 hour
api_cache = TimedCache(ttl=300)       # Cache API responses for 5 minutes


def cache_key_generator(*args, **kwargs) -> str:
    """
    Generate a cache key from function arguments.

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        MD5 hash string as cache key
    """
    key_data = {
        "args": args,
        "kwargs": kwargs
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


def timed_cache(ttl: int = 300):
    """
    Decorator for time-based caching of function results.

    Args:
        ttl: Time-to-live in seconds

    Returns:
        Decorator function
    """
    cache = TimedCache(ttl=ttl)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{cache_key_generator(*args, **kwargs)}"
            result = cache.get(key)
            if result is not None:
                return result

            result = func(*args, **kwargs)
            cache.set(key, result)
            return result

        # Add cache control methods to wrapper
        wrapper.cache_clear = cache.clear
        wrapper.cache_stats = cache.get_stats
        wrapper.cache_invalidate = lambda k: cache.invalidate(f"{func.__name__}:{k}")

        return wrapper
    return decorator


def persistent_cache(cache_file: str = "cache/file_cache.pkl"):
    """
    Decorator for persistent disk-based caching.

    Args:
        cache_file: Path to cache file

    Returns:
        Decorator function
    """
    cache_path = Path(cache_file)
    cache_path.parent.mkdir(exist_ok=True)

    # Load existing cache
    if cache_path.exists():
        try:
            with open(cache_path, 'rb') as f:
                cache = pickle.load(f)
        except:
            cache = {}
    else:
        cache = {}

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = cache_key_generator(*args, **kwargs)
            full_key = f"{func.__name__}:{key}"

            if full_key in cache:
                entry = cache[full_key]
                if entry['expiry'] > time.time():
                    return entry['value']
                else:
                    # Expired, remove it
                    del cache[full_key]

            # Calculate fresh value
            result = func(*args, **kwargs)
            cache[full_key] = {
                'value': result,
                'expiry': time.time() + 3600  # 1 hour default
            }

            # Save to disk
            try:
                with open(cache_path, 'wb') as f:
                    pickle.dump(cache, f)
            except Exception as e:
                print(f"Failed to save cache: {e}")

            return result

        return wrapper
    return decorator


def memoize(maxsize: int = 128):
    """
    Simple memoization decorator using lru_cache.
    Good for pure functions with small, hashable arguments.

    Args:
        maxsize: Maximum cache size

    Returns:
        Decorator function
    """
    return lru_cache(maxsize=maxsize)


# Convenience functions
def get_or_compute(key: str, compute_func: Callable, cache: Optional[TimedCache] = None, *args, **kwargs) -> Any:
    """
    Get from cache or compute and store.

    Args:
        key: Cache key
        compute_func: Function to call if cache miss
        cache: Cache instance (uses global api_cache if None)
        *args, **kwargs: Arguments to compute_func

    Returns:
        Computed or cached value
    """
    if cache is None:
        cache = api_cache

    result = cache.get(key)
    if result is not None:
        return result

    result = compute_func(*args, **kwargs)
    cache.set(key, result)
    return result


def warm_cache(func: Callable, *args, **kwargs):
    """
    Pre-populate cache by calling function and storing result.

    Args:
        func: Function to warm cache with
        *args, **kwargs: Arguments to the function
    """
    try:
        func(*args, **kwargs)
        print(f"Cache warmed for {func.__name__}")
    except Exception as e:
        print(f"Failed to warm cache for {func.__name__}: {e}")