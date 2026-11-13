"""Thread-safe scan deduplication using monotonic time."""
from collections import OrderedDict
from hashlib import sha256
from threading import Lock
from time import monotonic

class Deduplicator:
    def __init__(self, window_ms: int = 1500, capacity: int = 512) -> None:
        self.window = max(0, window_ms) / 1000
        self.capacity = capacity
        self.items: OrderedDict[str, float] = OrderedDict()
        self.lock = Lock()

    def accept(self, content: str) -> bool:
        if self.window <= 0: return True
        now = monotonic()
        signature = sha256(content.strip().encode("utf-8", "surrogatepass")).hexdigest()
        with self.lock:
            while self.items:
                _, timestamp = next(iter(self.items.items()))
                if now - timestamp <= self.window: break
                self.items.popitem(last=False)
            if signature in self.items:
                self.items[signature] = now
                self.items.move_to_end(signature)
                return False
            self.items[signature] = now
            while len(self.items) > self.capacity: self.items.popitem(last=False)
            return True
