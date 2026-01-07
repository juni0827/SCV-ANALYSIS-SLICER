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
        """Cache에서 Data Import"""
        if key in self._cache:
            # LRU 순서 Update
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key]
        return None

    def set(self, key, value):
        """Cache에 Data Save"""
        if key in self._cache:
            self._access_order.remove(key)
        elif len(self._cache) >= self._max_size:
            # 가장 오래된 항목 Remove
            oldest_key = self._access_order.pop(0)
            del self._cache[oldest_key]

        self._cache[key] = value
        self._access_order.append(key)

    def clear(self):
        """Cache 비우기"""
        self._cache.clear()
        self._access_order.clear()
