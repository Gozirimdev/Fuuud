# Account email and administrator operations

## Deployment

Apply `alembic upgrade head` from `apps/api` before deploying this revision. Migration `0008_account_emails` adds the durable delivery queue. Keep API and email-worker code and configuration on the same revision.

Set these server-side values using the hosting platform's secrets/configuration controls:

- `JWT_SECRET`: a randomly generated secret of at least 32 characters, shared by API and worker.
- `PUBLIC_APP_URL`: the frontend origin, such as `https://app.example.com`; no path, query, or fragment. HTTPS is required outside development.
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_SECURITY`: the provider's host, port, and either `starttls` (default, commonly port 587) or `ssl` (commonly port 465). TLS certificate verification is enabled.
- `SMTP_USERNAME`, `SMTP_PASSWORD`: set both when authentication is required.
- `MAIL_FROM`: the sender email address verified with the email provider.
- `DATABASE_URL`: the same PostgreSQL database used by the API.
- `ENVIRONMENT=production`: raw verification/reset tokens are excluded from API responses.

Schedule this bounded command every minute, from `apps/api`:

```sh
python -m app.mail_worker --limit 50
```

The command exits after processing its batch; it is not a continuously running service. A scheduler must invoke it repeatedly. PostgreSQL row locks with `SKIP LOCKED` prevent concurrent workers from processing the same queued row simultaneously. This concurrency behavior still needs verification against hosted PostgreSQL.

Registration and recovery requests write token hashes and delivery jobs in the same transaction. The queue contains no raw bearer token or message body: the worker derives the token using HMAC-SHA256, the secret, message kind, and random token UUID. Treat `JWT_SECRET` as sensitive; rotating it makes queued links obsolete, requiring new requests.

Delivery retries after 1, 2, 4, and 8 minutes, then marks the job failed after the fifth unsuccessful attempt. Used, expired, and secret-mismatched tokens are marked obsolete. SMTP errors are logged without provider exception text, recipients, tokens, or credentials. Delivery is at least once: a process crash after SMTP acceptance but before database commit can cause a duplicate email containing the same single-use link. SMTP acceptance is not proof of inbox delivery.

Monitor pending job age and failed jobs, along with scheduler health. After correcting an email-provider problem, users can request another link. Add queue retention/cleanup and provider bounce monitoring before public launch. No live email has been sent or inbox delivery verified by the automated tests.

Verification links expire after 24 hours; password reset links expire after 30 minutes. Each account can request a given kind once per minute and at most five times per hour. Cooldown and unknown-account responses remain generic. This does not replace login/IP abuse protection, which remains a launch task.

## Administrator provisioning

Use a dedicated patient account, complete its email verification, then run this command using trusted server access:

```sh
python -m app.admin --email admin@example.com
```

The command requires an existing active, verified account. It refuses to convert provider accounts, records `account.admin_provisioned`, and invalidates the account's existing sessions. Repeating it for an existing active administrator is harmless. Public registration cannot assign the administrator role. The administrator must log in again afterward. No real administrator was provisioned during implementation.

## Account access

Pending accounts can sign in and view their account/onboarding state. API actions using `require_roles` require an active account as well as an allowed role. Suspended accounts cannot authenticate or use existing sessions. Provider approval workflows and broader login-abuse controls are still pending.

## Required staging acceptance

- Apply the full migration chain to PostgreSQL and run API and worker against it.
- Verify registration email delivery, confirmation, recovery, password reset, and old-session invalidation using controlled test accounts.
- Verify SMTP failure recovery, scheduler monitoring, and concurrent worker behavior.
- Provision a dedicated administrator and confirm role access.
- Test the verification page in a browser, including an expired link and requesting a replacement.
