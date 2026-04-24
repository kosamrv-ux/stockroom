import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  (ensures tables are registered on Base.metadata)
from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client():
    """A TestClient backed by a fresh in-memory SQLite database per test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def product(client):
    """Creates and returns a sample product."""
    resp = client.post(
        "/products",
        json={"sku": "WIDGET-1", "name": "Blue widget", "unit_price": 9.99, "reorder_level": 5},
    )
    assert resp.status_code == 201
    return resp.json()
