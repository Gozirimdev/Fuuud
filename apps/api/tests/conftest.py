import os
from datetime import date, time, timedelta
from decimal import Decimal
from uuid import uuid4

os.environ["JWT_SECRET"] = "test-secret-that-is-long-enough-for-tests"
os.environ["ENVIRONMENT"] = "development"

import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient

from app.db import Store, get_db
from app.init_db import initialize
from app.main import app
from app.models import Availability, Practitioner, VerificationStatus


@pytest.fixture(scope="session")
def mongo_client():
    uri = os.environ.get("MONGODB_TEST_URI", "mongodb://localhost:27018/?replicaSet=rs0")
    client = MongoClient(uri, tz_aware=True, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    yield client
    client.close()


@pytest.fixture(autouse=True)
def database(mongo_client):
    # Always use an isolated, randomly named test database; never drop application data.
    name = "fuuud_test_" + uuid4().hex
    raw = mongo_client[name]
    initialize(raw)
    db = Store(raw)

    def override_db():
        yield Store(raw)

    app.dependency_overrides[get_db] = override_db
    p = db.insert(
        Practitioner(
            first_name="Adaeze",
            last_name="Okafor",
            specialty="Dermatology",
            professional_title="Consultant",
            license_number="DEMO-1",
            country="Nigeria",
            state="Anambra",
            city="Awka",
            consultation_fee=Decimal("15000"),
            years_of_experience=9,
            verification_status=VerificationStatus.verified,
            bio="Demo",
            rating=Decimal("4.8"),
        )
    )
    db.insert(
        Availability(
            practitioner_id=p.id,
            date=date.today() + timedelta(days=2),
            start_time=time(10),
            end_time=time(11),
        )
    )
    yield db
    app.dependency_overrides.clear()
    mongo_client.drop_database(name)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_factory(database):
    return lambda: Store(database.database)


@pytest.fixture
def auth(client):
    data = {
        "first_name": "Favour",
        "last_name": "Okeke",
        "email": "favour@example.com",
        "password": "securePass123",
    }
    client.post("/api/v1/auth/register", json=data)
    token = client.post(
        "/api/v1/auth/login", json={"email": data["email"], "password": data["password"]}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
