def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_registration_login_and_me(client):
    data = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "password": "password123",
    }
    assert client.post("/api/v1/auth/register", json=data).status_code == 201
    assert client.post("/api/v1/auth/register", json=data).status_code == 409
    assert (
        client.post(
            "/api/v1/auth/login", json={"email": data["email"], "password": "wrongpass"}
        ).status_code
        == 401
    )
    token = client.post(
        "/api/v1/auth/login", json={"email": data["email"], "password": data["password"]}
    ).json()["access_token"]
    assert (
        client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}).json()["email"]
        == data["email"]
    )
    me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}).json()
    assert me["role"] == "patient"
    assert me["account_status"] == "active"


def test_provider_registration_is_pending_and_admin_role_is_private(client):
    provider = {
        "first_name": "Ada",
        "last_name": "Doctor",
        "email": "doctor@example.com",
        "password": "securePass123",
        "role": "doctor",
    }
    created = client.post("/api/v1/auth/register", json=provider)
    assert created.status_code == 201
    assert created.json()["role"] == "doctor"
    assert created.json()["account_status"] == "pending"
    blocked = client.post(
        "/api/v1/auth/register", json={**provider, "email": "admin@example.com", "role": "admin"}
    )
    assert blocked.status_code == 422


def test_password_reset_is_private_single_use_and_changes_password(client):
    account = {
        "first_name": "Reset",
        "last_name": "User",
        "email": "reset@example.com",
        "password": "oldPassword123",
    }
    client.post("/api/v1/auth/register", json=account)
    old_token = client.post(
        "/api/v1/auth/login", json={"email": account["email"], "password": account["password"]}
    ).json()["access_token"]
    old_headers = {"Authorization": f"Bearer {old_token}"}
    assert client.get("/api/v1/users/me", headers=old_headers).status_code == 200
    missing = client.post("/api/v1/auth/forgot-password", json={"email": "missing@example.com"})
    assert missing.status_code == 200
    assert missing.json()["reset_token"] is None
    requested = client.post("/api/v1/auth/forgot-password", json={"email": account["email"]})
    token = requested.json()["reset_token"]
    assert token
    changed = client.post(
        "/api/v1/auth/reset-password", json={"token": token, "password": "newPassword123"}
    )
    assert changed.status_code == 200
    assert client.get("/api/v1/users/me", headers=old_headers).status_code == 401
    assert (
        client.post(
            "/api/v1/auth/reset-password", json={"token": token, "password": "anotherPassword123"}
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/api/v1/auth/login", json={"email": account["email"], "password": account["password"]}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/login", json={"email": account["email"], "password": "newPassword123"}
        ).status_code
        == 200
    )
    new_token = client.post(
        "/api/v1/auth/login", json={"email": account["email"], "password": "newPassword123"}
    ).json()["access_token"]
    assert (
        client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {new_token}"}).status_code
        == 200
    )


def test_email_verification_is_private_and_single_use(client):
    account = {
        "first_name": "Verify",
        "last_name": "User",
        "email": "verify@example.com",
        "password": "securePass123",
    }
    created = client.post("/api/v1/auth/register", json=account)
    assert created.status_code == 201
    assert created.json()["email_verified"] is False
    token = created.json()["verification_token"]
    assert token
    verified = client.post("/api/v1/auth/email-verification/verify", json={"token": token})
    assert verified.status_code == 200
    assert (
        client.post("/api/v1/auth/email-verification/verify", json={"token": token}).status_code
        == 400
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": account["email"], "password": account["password"]},
    ).json()
    me = client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {login['access_token']}"}
    )
    assert me.json()["email_verified"] is True
    hidden = client.post(
        "/api/v1/auth/email-verification/request",
        json={"email": "missing@example.com"},
    )
    assert hidden.status_code == 200
    assert hidden.json()["verification_token"] is None


def test_only_patients_can_use_patient_appointment_routes(client):
    provider = {
        "first_name": "Ada",
        "last_name": "Doctor",
        "email": "doctor-access@example.com",
        "password": "securePass123",
        "role": "doctor",
    }
    client.post("/api/v1/auth/register", json=provider)
    token = client.post(
        "/api/v1/auth/login", json={"email": provider["email"], "password": provider["password"]}
    ).json()["access_token"]
    response = client.get("/api/v1/appointments/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_user_can_only_read_own_audit_events(client, auth):
    events = client.get("/api/v1/users/me/audit-events", headers=auth)
    assert events.status_code == 200
    event_types = {item["event_type"] for item in events.json()}
    assert "account.registered" in event_types
    assert "account.login" in event_types
    assert client.get("/api/v1/users/me/audit-events").status_code == 401


def test_doctor_search_filters_details_availability(client):
    result = client.get("/api/v1/doctors?specialty=Dermatology&city=Awka&verified_only=true").json()
    assert result["total"] == 1
    doctor = result["items"][0]
    assert client.get(f"/api/v1/doctors/{doctor['id']}").status_code == 200
    assert len(client.get(f"/api/v1/doctors/{doctor['id']}/availability").json()) == 1
    assert client.get("/api/v1/doctors?search=Okafor").json()["total"] == 1


def test_booking_double_booking_listing_cancel(client, auth):
    doctor = client.get("/api/v1/doctors").json()["items"][0]
    slot = client.get(f"/api/v1/doctors/{doctor['id']}/availability").json()[0]
    payload = {
        "practitioner_id": doctor["id"],
        "availability_id": slot["id"],
        "appointment_type": "online",
        "reason": "Routine consultation",
    }
    booked = client.post("/api/v1/appointments", json=payload, headers=auth)
    assert booked.status_code == 201
    assert client.post("/api/v1/appointments", json=payload, headers=auth).status_code == 409
    items = client.get("/api/v1/appointments/me", headers=auth).json()
    assert len(items) == 1
    item_id = items[0]["id"]
    assert client.get(f"/api/v1/appointments/{item_id}", headers=auth).status_code == 200
    assert (
        client.patch(f"/api/v1/appointments/{item_id}/cancel", headers=auth).json()["status"]
        == "cancelled"
    )


def test_appointments_require_auth_and_are_object_scoped(client, auth):
    assert client.get("/api/v1/appointments/me").status_code == 401
    doctor = client.get("/api/v1/doctors").json()["items"][0]
    slot = client.get(f"/api/v1/doctors/{doctor['id']}/availability").json()[0]
    booking = client.post(
        "/api/v1/appointments",
        json={
            "practitioner_id": doctor["id"],
            "availability_id": slot["id"],
            "appointment_type": "online",
            "reason": "Routine care",
        },
        headers=auth,
    ).json()
    client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Other",
            "last_name": "User",
            "email": "other@example.com",
            "password": "securePass123",
        },
    )
    other = client.post(
        "/api/v1/auth/login", json={"email": "other@example.com", "password": "securePass123"}
    ).json()["access_token"]
    assert (
        client.get(
            f"/api/v1/appointments/{booking['id']}", headers={"Authorization": f"Bearer {other}"}
        ).status_code
        == 404
    )
