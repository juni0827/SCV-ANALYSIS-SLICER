"""
Data caching component
"""

from __future__ import annotations


class DataCache:
    """Data Caching system - LRU cache implementation"""

    def __init__(self, max_size: int = 50):
        self._cache = {}
        self._max_size = max_size
        self._access_order = []

    def get(self, key):
        """load data from cache"""
        if key in self._cache:
            # update LRU order
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key]
        return None

    def set(self, key, value):
        """save data to cache"""
        if key in self._cache:
            self._access_order.remove(key)
        elif len(self._cache) >= self._max_size:
            # remove oldest item
            oldest_key = self._access_order.pop(0)
            del self._cache[oldest_key]

        self._cache[key] = value
        self._access_order.append(key)

    def clear(self):
        """clear cache"""
        self._cache.clear()
        self._access_order.clear()
