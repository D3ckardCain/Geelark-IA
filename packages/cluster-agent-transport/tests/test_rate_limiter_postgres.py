from concurrent.futures import ThreadPoolExecutor
import os
from uuid import uuid4

import psycopg
import pytest

from cluster_agent_transport.limits import PostgresRateLimiter


DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="requiere PostgreSQL de integración")


def test_postgres_rate_limiter_is_atomic_shared_and_fails_closed():
    connect = lambda: psycopg.connect(DATABASE_URL)
    node_id = uuid4()
    limiter = PostgresRateLimiter(connect, max_requests=3, window_seconds=60)

    try:
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO geelark_control.nodes
                    (node_id, display_name, admin_state, health_state)
                VALUES (%s, %s, 'active', 'healthy')
                """,
                (node_id, "rate-limit-test-" + str(node_id)),
            )

        # Concurrent calls use independent PostgreSQL connections. The atomic
        # UPDATE must admit exactly the configured number, regardless of order.
        with ThreadPoolExecutor(max_workers=8) as pool:
            outcomes = list(pool.map(lambda _: limiter.allow(str(node_id)), range(8)))

        assert sum(outcomes) == 3
        with connect() as conn:
            count, started_at = conn.execute(
                """
                SELECT agent_rate_window_count, agent_rate_window_started_at
                  FROM geelark_control.nodes
                 WHERE node_id = %s
                """,
                (node_id,),
            ).fetchone()
            assert count == 4  # saturated at max_requests + 1
            assert started_at is not None

            conn.execute(
                """
                UPDATE geelark_control.nodes
                   SET agent_rate_window_started_at = now() - interval '61 seconds'
                 WHERE node_id = %s
                """,
                (node_id,),
            )

        assert limiter.allow(str(node_id)) is True
        with connect() as conn:
            count = conn.execute(
                "SELECT agent_rate_window_count FROM geelark_control.nodes WHERE node_id = %s",
                (node_id,),
            ).fetchone()[0]
            assert count == 1

            conn.execute(
                "UPDATE geelark_control.nodes SET revoked_at = now() WHERE node_id = %s",
                (node_id,),
            )

        assert limiter.allow(str(node_id)) is False
        assert limiter.allow("not-a-uuid") is False
    finally:
        with connect() as conn:
            conn.execute("DELETE FROM geelark_control.nodes WHERE node_id = %s", (node_id,))
