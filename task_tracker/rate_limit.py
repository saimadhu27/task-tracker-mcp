import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable

from task_tracker.config import settings
from task_tracker.errors import RateLimited


class RateLimiter:
    """Allows at most `limit` calls per `window` seconds for each user.

    State lives in this process's memory, which is enough for one instance. With several
    instances, each keeps its own count, so a shared store or a gateway would be needed.
    """

    def __init__(
        self,
        limit: int,
        window: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.limit = limit
        self.window = window
        self._clock = clock
        self._calls: dict[int, deque[float]] = defaultdict(deque)
        # Sync tools run on worker threads, so two calls can arrive at the same moment.
        self._lock = threading.Lock()

    def check(self, user_id: int) -> None:
        """Record a call, or raise RateLimited if this user is over the limit."""
        now = self._clock()
        with self._lock:
            calls = self._calls[user_id]
            while calls and now - calls[0] >= self.window:
                calls.popleft()
            if len(calls) >= self.limit:
                retry_after = int(self.window - (now - calls[0])) + 1
                raise RateLimited(retry_after)
            calls.append(now)

    def reset(self) -> None:
        with self._lock:
            self._calls.clear()


limiter = RateLimiter(limit=settings.rate_limit_per_minute)


def enforce(user_id: int) -> None:
    if settings.rate_limit_per_minute > 0:
        limiter.check(user_id)