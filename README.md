# Fuuud — Care, closer.

Fuuud is a healthcare access and navigation platform for patients, doctors, and hospitals. This repository combines a broad UI/UX prototype with the first backend-supported workflows.

## Stack and setup

Next.js App Router, strict TypeScript, Tailwind CSS, and Lucide icons.

```bash
npm install
npm run dev
```

Quality commands: `npm run lint`, `npm run typecheck`, and `npm run build`.

## Product structure

Routes cover onboarding/auth, home, doctors and profiles, appointment booking, hospitals and emergency access, messaging, prescriptions, pharmacies, nutrition, FU agent, and profile. Shared components live in `src/components`; typed fictional fixtures in `src/data`; replaceable async accessors in `src/lib/services`.

The service boundary is deliberately API-shaped. A later phase can replace its local implementations with HTTP calls without rewriting page UI. Authentication, maps, payments, clinical decisions, realtime chat, provider availability, and emergency notifications are explicitly simulated.

See `docs/ui-system.md` for design guidance and `docs/architecture.md` for Phase 1 architecture.

See `docs/product-roadmap.md` for the component-by-component path to a production-ready platform.

## MongoDB backend setup

The Python API uses MongoDB with PyMongo and validated document models. Use MongoDB Atlas for deployment or the local replica set in `docker-compose.yml`.

See [MongoDB deployment and local setup](docs/mongodb-deployment.md) for the exact Render commands, environment variables, database conventions, and test instructions. The old PostgreSQL/Alembic commands no longer apply.

Frontend checks: `npm run lint`, `npm run typecheck`, and `npm run build`. Backend checks from `apps/api`: `ruff check .` and `pytest` against a MongoDB replica set.

Account verification and recovery now queue email delivery. Configure SMTP and schedule `python -m app.mail_worker --limit 50` to send queued messages. See `docs/account-operations.md` for deployment, retries, and administrator provisioning. Development responses still include local verification/reset tokens; production responses do not.

The seed command creates 15 fictional practitioners and bookable slots across Awka, Onitsha, Enugu, Lagos, Abuja and Port Harcourt. These are demonstration records, not verified real clinicians.
