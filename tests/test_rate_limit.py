import pytest
from mcp import Client

from task_tracker import rate_limit
from task_tracker.errors import RateLimited
from task_tracker.rate_limit import RateLimiter
from task_tracker.tools import mcp


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_allows_calls_up_to_the_limit_then_refuses():
    limiter = RateLimiter(limit=2, window=60, clock=FakeClock())
    limiter.check(1)
    limiter.check(1)

    with pytest.raises(RateLimited):
        limiter.check(1)


def test_calls_are_allowed_again_after_the_window_passes():
    clock = FakeClock()
    limiter = RateLimiter(limit=1, window=60, clock=clock)
    limiter.check(1)
    with pytest.raises(RateLimited):
        limiter.check(1)

    clock.now += 61

    limiter.check(1)


def test_each_user_has_their_own_allowance():
    limiter = RateLimiter(limit=1, window=60, clock=FakeClock())
    limiter.check(1)

    limiter.check(2)  # a different user is unaffected

    with pytest.raises(RateLimited):
        limiter.check(1)


def test_retry_after_says_how_long_to_wait():
    clock = FakeClock()
    limiter = RateLimiter(limit=2, window=60, clock=clock)
    limiter.check(1)  # at t = 0
    clock.now += 10
    limiter.check(1)  # at t = 10
    clock.now += 10  # t = 20: the third call is too many

    with pytest.raises(RateLimited) as excinfo:
        limiter.check(1)

    assert excinfo.value.retry_after == 41  # the first call leaves the window at t = 60


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    async with Client(mcp, raise_exceptions=True) as c:
        yield c


@pytest.mark.anyio
async def test_tool_calls_over_the_limit_get_a_readable_error(client, monkeypatch):
    monkeypatch.setattr(rate_limit, "limiter", RateLimiter(limit=2))

    first = await client.call_tool("list_tasks", {})
    second = await client.call_tool("list_tasks", {})
    third = await client.call_tool("list_tasks", {})

    assert not first.is_error
    assert not second.is_error
    assert third.is_error
    assert "Too many requests" in third.content[0].text