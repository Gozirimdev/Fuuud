> Database update: the backend now uses MongoDB. SQL/Alembic details below are historical. Use [MongoDB deployment](mongodb-deployment.md) for current setup and commands.

# FUUUD launch checklist

This checklist turns the product roadmap into a delivery sequence. Existing code is a starting point, not evidence that a feature has passed production verification. Unchecked tasks require implementation, verification, or both.

## Launch scope

Proposed first release: patients can register, find verified doctors and hospital contact details, book real appointments, and manage bookings. Doctors manage availability and appointments; administrators verify providers and handle support. Initially launch with a small group of onboarded providers.

Hospital operations, payments, messaging, prescriptions, pharmacy, nutrition, emergency alerts, and FU Agent follow as separate milestones unless explicitly included in the first release. Hide unfinished features from public navigation and prevent direct access to demo workflows.

## 1. Establish a reliable baseline

- [x] Run frontend lint, type checking, and production build; run backend lint and tests. Fix failures.
- [ ] Apply all migrations to a clean PostgreSQL database and verify registration, login, discovery, booking, and cancellation end to end.
- [ ] Review implemented roles, account status, verification, recovery, and audit events against the roadmap; update stale architecture documentation.
- [ ] Establish version control and a remote repository; exclude secrets, generated files, and local environments.
- [ ] Record first-release scope and acceptance criteria for each public workflow.

Done when the current application is reproducible and its working and unfinished features are documented.

## 2. Finish accounts, roles, and access

- [ ] Connect real email delivery for verification and password recovery, with expiry and resend limits.
- [ ] Verify registration, login, logout, verification, recovery, and expired-session behavior in the UI and API.
- [ ] Enforce patient, doctor, hospital staff, and admin permissions on the server and protected pages.
- [ ] Prevent public privilege escalation and define how the first administrator is provisioned.
- [ ] Enforce pending and suspended account restrictions and review session invalidation after password resets or suspension.
- [ ] Complete account audit events and authentication abuse protection.

Done when each role can access only its permitted actions and account recovery works through actual email.

## 3. Complete patient accounts

- [ ] Persist patient profile and contact edits with validation.
- [ ] Implement consent and privacy controls needed for the first-release data flows.
- [ ] Connect appointment history and account settings to real data.
- [ ] Provide usable loading, empty, validation, error, and retry states.

Done when a patient can manage their account without mock data or dead-end controls.

## 4. Build doctor onboarding and workspace

- [ ] Link doctor accounts to practitioner records.
- [ ] Implement professional profile, licence and identity submission, and restricted document storage.
- [ ] Build administrator approval/rejection and prevent unverified providers from accepting public bookings.
- [ ] Allow doctors to manage consultation fees, appointment types, and availability.
- [ ] Build appointment queue, patient-detail permissions, and consultation status updates.

Done when an onboarded, approved doctor can publish real availability and manage bookings.

## 5. Finish the appointment lifecycle

- [ ] Verify booking and cancellation with real patient and doctor accounts.
- [ ] Implement rescheduling, confirmation rules, completion, no-show handling, and status history.
- [ ] Verify concurrent booking protection and safe retries against PostgreSQL.
- [ ] Handle time zones, past slots, unavailable slots, and cancellation rules consistently.
- [ ] Connect booking confirmations, changes, cancellations, and reminders to real notifications.
- [ ] Make the consultation location or supported online meeting instructions clear.

Done when a patient and doctor can complete the entire booking lifecycle and both see consistent status.

## 6. Make the hospital directory real

- [ ] Replace fictional public listings with reviewed hospital records and a process for keeping them current.
- [ ] Show accurate contact details, locations, directions, services, and listing status.
- [ ] Clearly distinguish listed hospitals from registered and verified partners.
- [ ] Limit non-partner interactions to contact and directions; remove simulated acceptance and availability.

Done when every public listing is usable and accurately represents the hospital's relationship with FUUUD.

## 7. Complete administration and support

- [ ] Build provider verification, account suspension, and directory maintenance controls.
- [ ] Add appointment issue lookup and a support contact/reporting flow.
- [ ] Restrict sensitive records and documents to authorized staff; audit important changes.
- [ ] Publish onboarding and support procedures for the initial providers.

Done when staff can run the pilot through supported workflows.

## 8. Set up hosted staging and production

Start this alongside account work so completed flows can be tested online early.

- [ ] Select hosting, region, domain, and budget for the frontend, FastAPI backend, and hosted PostgreSQL.
- [ ] Create separate staging and production databases and secrets; keep Docker optional for local development.
- [ ] Configure database TLS, restricted access, connection limits, migrations, and backup retention.
- [ ] Configure HTTPS, API addresses, allowed origins, secure cookies, email credentials, and production settings.
- [ ] Automate checks and deployments with a documented migration and rollback procedure.
- [ ] Add health checks, error monitoring, operational alerts, and logs that avoid sensitive health information.
- [ ] Restore a backup into an isolated database and verify it works.
- [ ] Keep fictional seed data out of production; define any required data transfer and validate it.

Done when staging works online and production can be deployed, monitored, and recovered reliably.

## 9. Pass launch readiness checks

- [ ] Review data collection, privacy notice, terms, retention, deletion requests, and applicable obligations for the launch market.
- [ ] Test access controls, cross-account record access, authentication abuse, uploads, and secret handling.
- [ ] Run end-to-end patient, doctor, and administrator journeys against staging.
- [ ] Test mobile layouts, keyboard access, form accessibility, slow networks, and failure states.
- [ ] Check performance and booking concurrency against the expected pilot traffic.
- [ ] Remove or clearly restrict every remaining demo route, placeholder action, and fictional provider.
- [ ] Resolve launch-blocking defects and document known non-blocking limitations.

Done when all first-release workflows pass and no public screen implies an unavailable service.

## 10. Pilot and public launch

- [ ] Onboard a small set of verified providers and consenting pilot patients.
- [ ] Complete real bookings and collect feedback on the entire care-access journey.
- [ ] Confirm support ownership, incident response, monitoring, and rollback readiness.
- [ ] Fix pilot blockers and repeat affected acceptance checks.
- [ ] Review launch readiness, open public registration, and monitor initial usage closely.

Done when real users can complete the promised workflows and the team can support them.

## Follow-on milestones for the full platform

Each milestone needs its own data model, API, permissions, interface, validation, operational process, and acceptance checks before release.

- [ ] Hospital onboarding: authority verification, staff permissions, departments, affiliated doctors, appointments, and referrals.
- [ ] Messaging: patient/provider conversations, attachments, delivery status, reporting, and retention.
- [ ] Payments: provider choice, collection, signed webhooks, safe retries, receipts, refunds, settlement, and reconciliation. Move before launch if launch appointments require in-app payment.
- [ ] Prescriptions: clinician issuance, patient access, change history, and pharmacy handoff.
- [ ] Pharmacy: verified listings, medicine enquiries, and controlled prescription access.
- [ ] Emergency access: partner availability, consent-based location sharing, acknowledged incoming-patient alerts, and escalation procedures.
- [ ] Nutrition: define the service, content ownership, personalization boundaries, and implement real data flows.
- [ ] FU Agent: permission-aware service tools, reliable booking/navigation assistance, evaluation, and clinical handoff boundaries.

Immediate next task: verify the baseline, then finish accounts, roles, and access while establishing hosted staging.

## Progress — 2026-09-08

- Frontend lint, TypeScript checking, and production build passed. Backend Ruff passed; 11 tests passed with one upstream TestClient deprecation warning.
- Removed invalid Python from migration `0002_hardening` that prevented migration loading. Added a PostgreSQL SQL-generation regression test covering the migration chain. This does not replace applying migrations to PostgreSQL.
- Password resets now increment a stored session version, invalidating previously issued access tokens. A regression test verifies old sessions fail and new logins work.
- Added migration `0007_session_version`. Apply `alembic upgrade head` before running the updated backend. Previously issued tokens without a session version require users to log in again.
- Excluded the backend virtual environment and temporary dependency files from frontend lint traversal; expanded Git ignores for Python and TypeScript generated files.
- PostgreSQL migration execution and real-database workflow verification remain pending: the local Docker daemon was unavailable during this pass. Hosted PostgreSQL can be used instead.
- Account access is still in progress: email delivery, abuse controls, pending-account restrictions, administrator provisioning, and broader lifecycle verification remain open.

### Account delivery implementation

- Added a durable account-email queue, SMTP TLS transport, and bounded retry worker. SMTP credentials, a scheduled worker, and real inbox acceptance testing remain pending.
- Added per-account resend limits: once per minute and five times per hour for each email kind. Broader login/IP abuse controls remain open.
- Role-protected API operations now require active account status; pending accounts retain access to account/onboarding information.
- Added a trusted-server administrator provisioning command requiring an active, verified account. It audits the change and revokes existing sessions.
- Verification now requires an explicit confirmation button and supports requesting a replacement from an expired link.
- See `account-operations.md` for required configuration and staging acceptance checks. These changes do not mark the complete account milestone or hosted deployment complete.
