import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"

def test_health_shape():
    from app import live
    assert live() == {"status": "alive"}
