import cluster_agent_transport.app as app_module
import cluster_agent_transport.db_auth as db_auth
import cluster_agent_transport.domain_handlers as domain_handlers
import cluster_agent_transport.idempotency as idempotency
import cluster_agent_transport.replay as replay


def test_postgres_app_factory_wires_database_backed_guards(monkeypatch):
    connect = lambda: None
    captured = {}
    auth = object()
    nonce_consumer = object()
    handlers = {object(): object()}
    idempotency_runner = object()

    class FakePostgresRateLimiter:
        def __init__(self, connect_callback):
            self.connect = connect_callback

    def fake_create_agent_app(**kwargs):
        captured.update(kwargs)
        return "test-app"

    monkeypatch.setattr(db_auth, "make_database_authenticator", lambda callback: auth)
    monkeypatch.setattr(replay, "make_database_nonce_consumer", lambda callback: nonce_consumer)
    monkeypatch.setattr(domain_handlers, "make_postgres_agent_handlers", lambda callback: handlers)
    monkeypatch.setattr(idempotency, "make_database_idempotency_runner", lambda callback: idempotency_runner)
    monkeypatch.setattr(app_module, "PostgresRateLimiter", FakePostgresRateLimiter)
    monkeypatch.setattr(app_module, "create_agent_app", fake_create_agent_app)

    result = app_module.create_postgres_agent_app(connect, max_body_bytes=4096)

    assert result == "test-app"
    assert captured["authenticate"] is auth
    assert captured["consume_nonce"] is nonce_consumer
    assert captured["handlers"] is handlers
    assert captured["idempotency_runner"] is idempotency_runner
    assert isinstance(captured["rate_limiter"], FakePostgresRateLimiter)
    assert captured["rate_limiter"].connect is connect
    assert captured["max_body_bytes"] == 4096
