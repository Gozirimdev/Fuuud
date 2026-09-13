import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret-that-is-long-enough-for-tests"
from datetime import date, time, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import Availability, Practitioner, VerificationStatus

engine = create_engine(
    "sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
Testing = sessionmaker(bind=engine, expire_on_commit=False)


def override_db():
    with Testing() as db:
        yield db


app.dependency_overrides[get_db] = override_db


@pytest.fixture(autouse=True)
def database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with Testing() as db:
        p = Practitioner(
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
        db.add(p)
        db.flush()
        db.add(
            Availability(
                practitioner_id=p.id,
                date=date.today() + timedelta(days=2),
                start_time=time(10),
                end_time=time(11),
            )
        )
        db.commit()
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_factory():
    return Testing


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
