import pytest
import redis
from fastapi.testclient import TestClient

import main


@pytest.mark.parametrize("redis_available", [True, False])
def test_health_never_connects_to_database(monkeypatch, redis_available):
    def database_access_forbidden(*args, **kwargs):
        pytest.fail("Health endpoint must not connect to PostgreSQL")

    def ping():
        if not redis_available:
            raise redis.ConnectionError("Redis unavailable in this test")
        return True

    monkeypatch.setattr(main.engine, "connect", database_access_forbidden)
    monkeypatch.setattr(main.redis_client, "ping", ping)
    # Do not enter the lifespan: application startup initializes tables, while
    # this unit test checks only the health request, without PostgreSQL.
    client = TestClient(main.app)
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["redis"] == ("healthy" if redis_available else "unhealthy")
    assert payload["timestamp"]
    client.close()
