# FUUUD architecture

```text
Next.js UI
  ↓ typed client / HttpOnly session BFF
FastAPI routes
  ↓
Service layer (reusable by future agent tools)
  ↓
Repositories / SQLAlchemy
  ↓
PostgreSQL (Aurora-compatible)

Future: Amazon Bedrock agent → the same service layer
```

Phase 1 is a modular monolith. Only authentication, practitioner discovery, availability and appointments use the backend. Hospitals, messaging, prescriptions, pharmacy, nutrition and FU remain Phase 0 demonstrations. Browser JWT access is mediated by Next.js and stored in an HttpOnly, SameSite=Lax cookie; production enables Secure. Passwords use Argon2 and never leave the backend after registration/login.

Accounts now include patient, doctor, hospital staff, and administrator roles, account status, single-use password reset and email verification tokens, and account audit events. A transactional email queue and SMTP worker support delivery with retries; SMTP configuration and live delivery verification remain pending. Access tokens carry a session version checked against the user record on authenticated requests; password resets and administrator provisioning increment that version to invalidate older sessions. Apply migrations through `0008_account_emails` before running this backend revision. See `account-operations.md` for worker and administrator setup.

Double booking is prevented by a row lock during booking plus a unique database constraint on `appointments.availability_id`. Cancellation locks and releases the associated slot in the same transaction.
