# Deploy Fuuud with MongoDB Atlas and Render

The API now uses MongoDB through PyMongo. SQLAlchemy, PostgreSQL and Alembic are no longer part of the runtime. The frontend API paths and JSON field names are unchanged; IDs are now 24-character MongoDB ObjectId strings.

## MongoDB Atlas

1. Create an Atlas cluster, and create a database user with read/write access to the `fuuud` database. This is separate from your Atlas dashboard login.
2. Under Network Access, allow the Render API's outbound IP ranges shown in its dashboard. Add the worker's ranges too if separate. For local development, allow your own IP.
3. Choose Connect > Drivers > Python and copy the connection URI. Replace the username and password placeholders with your database user's credentials. URL-encode special characters in credentials.
4. Keep the `mongodb+srv://` prefix. Do not use the old `postgresql+psycopg://` prefix.

## Render API

Runtime: Python 3 (Python 3.12 or newer).
Root directory: `apps/api`.
Build command:

```sh
pip install .
```

Start command:

```sh
python -m app.init_db && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Health check: `/health`. Readiness (including a database ping): `/ready`.

Paste these names using Add from .env, replacing every placeholder:

```dotenv
MONGODB_URI=mongodb+srv://YOUR_DB_USER:YOUR_DB_PASSWORD@YOUR_CLUSTER.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=fuuud
JWT_SECRET=YOUR_EXISTING_RANDOM_SECRET
ENVIRONMENT=production
PUBLIC_APP_URL=https://YOUR_SITE.vercel.app
CORS_ORIGINS=https://YOUR_SITE.vercel.app
```

Remove `DATABASE_URL` from Render. Keep the existing JWT secret unless you intend to invalidate sessions and outstanding email links. MongoDB Atlas provides the replica-set transactions needed by registration, token consumption and booking. A standalone MongoDB server is not supported; initialization fails with a clear message instead of silently weakening consistency.

On Vercel set `API_URL` to your Render API origin (without `/api/v1`) and redeploy.

## Email worker

Use the same code revision, MongoDB settings, JWT secret, public app URL and SMTP settings as the API. Schedule `python -m app.mail_worker --limit 50` every minute, from `apps/api`. See [account operations](account-operations.md) for SMTP settings.

## Existing data

This change targets a new MongoDB database. It does not copy or delete any existing PostgreSQL records. If PostgreSQL has real accounts or bookings, export and migrate them with an explicit ID mapping before switching traffic. UUID-based sessions and saved record links from PostgreSQL cannot address the new MongoDB IDs; users need to sign in to their migrated or newly created MongoDB accounts.

Do not run `app.seed` on a live directory of real providers. It is an optional demonstration dataset only.

## Local development and tests

Run `docker compose up -d --wait db` at the repository root. The development-only container binds to loopback and initializes a single-node replica set. Copy `apps/api/.env.example` to `apps/api/.env`, set a JWT secret, then run from `apps/api`:

```sh
pip install -e ".[dev]"
python -m app.init_db
python -m app.seed
uvicorn app.main:app --reload
```

The test suite requires a real replica set. Set `MONGODB_TEST_URI` to the local replica-set URI (for Docker, `mongodb://localhost:27017/?replicaSet=rs0`) and run `pytest`. Tests create and drop only uniquely named `fuuud_test_*` databases. The default test port is 27018 so tests do not assume the development server is running.

## Document conventions

- Native BSON ObjectId `_id` and reference fields in MongoDB; string `id` fields over HTTP.
- UTC BSON datetimes for timestamps and scheduled appointments; ISO date/time strings for separate availability fields.
- BSON Decimal128 for consultation fees and ratings, preserving exact decimal values.
- Unique normalized email and licence indexes; compound availability and query indexes.
- A partial unique index prevents more than one active appointment per slot while preserving cancelled history.
- Account creation, token consumption, administrator changes and booking/cancellation use retried transactions.
- Email jobs use atomic claims with five-minute leases, recoverable after worker failure. Delivery remains at least once.
- Expired verification/reset records are eligible for TTL cleanup one day after expiry. API validity checks enforce expiry immediately, independently of TTL cleanup.

References: [PyMongo transactions](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/transactions/), [Atlas connection setup](https://www.mongodb.com/docs/atlas/connect-your-application/).
