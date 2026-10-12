import pytest

from cluster_agent_transport.limits import InMemoryRateLimiter, PostgresRateLimiter


@pytest.mark.parametrize(
    "factory",
    [
        lambda max_requests, window_seconds: InMemoryRateLimiter(
            max_requests=max_requests, window_seconds=window_seconds
        ),
        lambda max_requests, window_seconds: PostgresRateLimiter(
            lambda: None, max_requests=max_requests, window_seconds=window_seconds
        ),
    ],
)
@pytest.mark.parametrize(
    ("max_requests", "window_seconds"),
    [
        (0, 60),
        (60, 0),
        (-1, 60),
        (60, -1),
        (True, 60),
        (60, False),
        (1.5, 60),
        (60, 1.5),
    ],
)
def test_rate_limiters_reject_non_positive_or_non_integer_configuration(
    factory, max_requests, window_seconds
):
    with pytest.raises(ValueError, match="enteros positivos"):
        factory(max_requests, window_seconds)


def test_in_memory_rate_limiter_enforces_and_resets_window():
    limiter = InMemoryRateLimiter(max_requests=2, window_seconds=10)

    assert limiter.allow("node-a", now=100.0) is True
    assert limiter.allow("node-a", now=101.0) is True
    assert limiter.allow("node-a", now=102.0) is False
    assert limiter.allow("node-a", now=111.0) is True
