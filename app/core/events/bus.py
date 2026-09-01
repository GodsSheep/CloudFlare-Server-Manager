import threading
from typing import Callable, Any, Dict, List


class EventBus:
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event: str, handler: Callable):
        with self._lock:
            self._listeners.setdefault(event, []).append(handler)

    def publish(self, event: str, *args, **kwargs):
        with self._lock:
            handlers = list(self._listeners.get(event, []))
        for handler in handlers:
            try:
                handler(*args, **kwargs)
            except Exception:
                pass

    def clear(self):
        with self._lock:
            self._listeners.clear()
