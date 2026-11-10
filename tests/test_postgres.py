import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from database import get_db
from main import app
from models import Base, User, WishList


@pytest.mark.integration
def test_wishlist_endpoint_reads_real_postgres():
    # Mandatory explicit test URL: never fall back to the developer's .env.
    url = os.environ["TEST_DATABASE_URL"]
    parsed = make_url(url)
    assert parsed.get_backend_name() == "postgresql"
    assert parsed.database.endswith("_test"), "Use a dedicated *_test database"
    engine = create_engine(url, connect_args={"connect_timeout": 3})
    try:
        Base.metadata.create_all(engine)
        with engine.connect() as connection:
            transaction = connection.begin()
            session = Session(bind=connection, join_transaction_mode="create_savepoint")
            try:
                user = User(email=f"{uuid4().hex}@example.com", hashed_password="unused")
                session.add(user)
                session.flush()
                wishlist = WishList(title=f"Postgres test {uuid4().hex}", owner=user)
                session.add(wishlist)
                session.flush()
                expected_id, expected_title = wishlist.id, wishlist.title
                # Expunge objects so the endpoint must issue an actual SQL SELECT.
                session.expunge_all()

                def test_database():
                    yield session

                app.dependency_overrides[get_db] = test_database
                client = TestClient(app)
                try:
                    response = client.get(f"/wishlists/{expected_id}")
                    assert response.status_code == 200
                    assert response.json()["id"] == expected_id
                    assert response.json()["title"] == expected_title
                    assert session.scalar(select(WishList.title).where(
                        WishList.id == expected_id
                    )) == expected_title
                finally:
                    client.close()
            finally:
                app.dependency_overrides.clear()
                session.close()
                transaction.rollback()
    finally:
        engine.dispose()
