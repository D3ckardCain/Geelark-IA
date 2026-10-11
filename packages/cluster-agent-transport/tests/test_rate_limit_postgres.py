import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import psycopg
import pytest

from cluster_agent_transport.limits import PostgresRateLimiter


DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="requiere PostgreSQL de integración")


def test_postgres_rate_limit_is_global_across_concurrent_connections():
    node_id = uuid4()
    connect = lambda: psycopg.connect(DATABASE_URL)
    limiter = PostgresRateLimiter(connect, max_requests=5, window_seconds=60)
    try:
        with connect() as conn:
            conn.execute(
                "INSERT INTO geelark_control.nodes (node_id, display_name, admin_state) VALUES (%s, %s, 'pending')",
                (node_id, "test-rate-" + str(node_id)),
            )

        with ThreadPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(lambda _: limiter.allow(str(node_id)), range(12)))
        assert sum(results) == 5
        assert limiter.allow("not-a-uuid") is False
        assert limiter.allow(str(uuid4())) is False

        with connect() as conn:
            row = conn.execute(
                "SELECT agent_rate_window_count FROM geelark_control.nodes WHERE node_id = %s",
                (node_id,),
            ).fetchone()
            assert row[0] == 6  # 5 admitidas + contador saturado en max_requests + 1

            conn.execute(
                """
                UPDATE geelark_control.nodes
                   SET agent_rate_window_started_at = now() - interval '61 seconds',
                       agent_rate_window_count = 5
                 WHERE node_id = %s
                """,
                (node_id,),
            )
        assert limiter.allow(str(node_id)) is True
        with connect() as conn:
            row = conn.execute(
                "SELECT agent_rate_window_count FROM geelark_control.nodes WHERE node_id = %s",
                (node_id,),
            ).fetchone()
            assert row[0] == 1
    finally:
        with connect() as conn:
            conn.execute("DELETE FROM geelark_control.nodes WHERE node_id = %s", (node_id,))
