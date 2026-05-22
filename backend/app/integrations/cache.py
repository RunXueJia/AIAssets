from copy import deepcopy
from time import monotonic
from typing import Any


class TtlCache:
    def __init__(self, *, ttl_s: float = 300, max_size: int = 256) -> None:
        self.ttl_s = ttl_s
        self.max_size = max_size
        self._items: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        item = self._items.get(key)
        if item is None:
            return None
        expires_at, value = item
        if expires_at <= monotonic():
            self._items.pop(key, None)
            return None
        return deepcopy(value)

    def set(self, key: str, value: Any) -> None:
        if len(self._items) >= self.max_size:
            oldest_key = min(self._items, key=lambda item_key: self._items[item_key][0])
            self._items.pop(oldest_key, None)
        self._items[key] = (monotonic() + self.ttl_s, deepcopy(value))
