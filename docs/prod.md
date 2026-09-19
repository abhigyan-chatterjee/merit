# Merit Production Handoff — Clerk OAuth (Google/GitHub)

Password login is untouched. This doc covers enabling **Sign in with
Google/GitHub via Clerk**, linked to existing Merit accounts.

How it works:

- Frontend (`/login`, `/register` only) renders Clerk `<SignIn/>`/`<SignUp/>`
  **iff** `VITE_CLERK_PUBLISHABLE_KEY` is set. On Clerk success the page
  POSTs `{clerk_token}` to the backend and follows the normal logged-in flow.
- Backend `POST /api/v1/auth/oauth/clerk` verifies the Clerk session JWT
  against the **Clerk JWKS** with the existing `pyjwt` dependency (no Clerk
  SDK; `jwt.PyJWKClient` fetches + caches the JWKS). It checks
  audience/issuer/expiry, extracts the verified email + Clerk user id, then:
  - `users.clerk_id` match → sign in as that user;
  - verified email matches an existing row → **LINK** (`clerk_id` set,
    password hash and all data kept);
  - else **CREATE** (`password_hash="oauth$clerk"`, `is_active=1`,
    `auth_provider="clerk"`, display name from Clerk).
  - Issues the existing `merit_access`/`merit_refresh` cookies through the
    same rotation code path as password login. No parallel session system.
- If `CLERK_JWKS_URL` is empty, the endpoint returns
  `501 OAUTH_NOT_CONFIGURED` (never crashes).

## 1. Clerk dashboard steps (owner)

1. Go to <https://dashboard.clerk.com> → **Create application** (name it
   e.g. `Merit`), choose Google + GitHub as social options at creation
   (or add later).
2. **Enable Google + GitHub:**
   Configure → **SSO connections** (a.k.a. Social connections) → enable
   **Google** and **GitHub**. For production, supply your own Google OAuth
   Client ID/secret and GitHub OAuth App Client ID/secret on those pages;
   Clerk's shared dev keys only work on Clerk dev domains.
3. **Copy the keys** (Configure → **API keys**):
   - **Publishable key** → `pk_live_...` (or `pk_test_...` for staging)
   - **Frontend API URL** → e.g. `https://spiffy-panda-12.clerk.accounts.dev`
4. **Derive the JWKS URL + audience** from the Frontend API URL:
   - `CLERK_JWKS_URL=https://<frontend-api-domain>/.well-known/jwks.json`
     (JWKS URL pattern — keep the `/.well-known/jwks.json` suffix; the
     backend derives the expected token issuer by stripping that suffix.)
   - `CLERK_AUDIENCE`: leave empty unless you configured a custom JWT
     template with an `aud` claim, in which case paste that audience.
5. **Add an email claim (REQUIRED):** the backend links accounts by the
   **verified email inside the signed token**. Clerk's default session token
   carries no email, so create a JWT template:
   Configure → **JWT templates** → New template → name it `merit`,
   add claims `{"email": "{{user.primary_email_address}}",
   "name": "{{user.full_name}}"}`, Save. Then set
   `VITE_CLERK_JWT_TEMPLATE=merit` on the frontend (see below). Without this,
   login fails with `401 OAUTH_EMAIL_MISSING`.
6. **Paste keys into env files (never commit — both are gitignored):**
   - `apps/api/.env`:
     ```ini
     CLERK_JWKS_URL=https://<frontend-api-domain>/.well-known/jwks.json
     CLERK_AUDIENCE=
     ```
   - `apps/web/.env` (create next to `package.json`):
     ```ini
     VITE_CLERK_PUBLISHABLE_KEY=pk_live_...
     VITE_CLERK_JWT_TEMPLATE=merit
     ```
7. Restart both servers (`uvicorn app.main:app --reload --port 8000` and
   `npm run dev`), hard-refresh the browser, and confirm the
   “or continue with Google / GitHub” block appears on `/login`.

## 2. Owner verification (owner executes — real token, live keys)

```bash
API=http://localhost:8000

# 1. Password register still works (untouched flow)
curl -s -i -X POST $API/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"owner+pw@example.com","display_name":"Owner","password":"VeryStrongPass123"}' \
| head -20   # expect 201 + merit_access/merit_refresh cookies

# 2. Password login still works
curl -s -i -X POST $API/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"owner+pw@example.com","password":"VeryStrongPass123"}' \
| head -12   # expect 200 + cookies

# 3. OAuth with a REAL Clerk session token:
#    sign in via the web UI once, then in browser devtools run:
#      await window.Clerk.session.getToken({ template: 'merit' })
#    and paste the result as REAL_TOKEN below.
REAL_TOKEN='<paste-real-clerk-session-jwt>'
#    New email -> expect 201 (created, auth_provider=clerk) + cookies:
curl -s -i -X POST $API/api/v1/auth/oauth/clerk \
  -H 'Content-Type: application/json' \
  -d "{\"clerk_token\":\"$REAL_TOKEN\"}" | head -20
#    Same token again -> expect 200 (same user id, linked):
curl -s -X POST $API/api/v1/auth/oauth/clerk \
  -H 'Content-Type: application/json' \
  -d "{\"clerk_token\":\"$REAL_TOKEN\"}"

# 4. Bogus token -> expect 401 OAUTH_INVALID_TOKEN:
curl -s -X POST $API/api/v1/auth/oauth/clerk \
  -H 'Content-Type: application/json' \
  -d '{"clerk_token":"bogus"}'

# 5. Unconfigured backend (CLERK_JWKS_URL empty) -> expect 501 OAUTH_NOT_CONFIGURED.
```

## 3. Notes / known behaviour

- OAuth-only accounts have `password_hash="oauth$clerk"` and cannot use
  password login (it fails closed with invalid credentials); linking an
  existing password account preserves its password.
- Secrets live only in `apps/api/.env` / `apps/web/.env` (gitignored).
  Never commit them, never paste real tokens into tests (tests mock JWKS —
  no network, no real keys).
- Frontend social block renders only on `/login` + `/register`; all other
  routes are unchanged.

## 4. Neon Postgres prod DB (SQLite stays for dev/test)

Local dev/test keep using SQLite with zero env needed. Only prod on the VPS
points at Neon. No live URL exists yet — everything below is ready short of
the owner-run cutover.

Why it works without a data migration: all models use `String`/`Text`/
`Integer`/`Float` (no SQLite-only DDL in any of the 9 migrations), UUID
primary keys are generated client-side (`str(uuid.uuid4())`, no `pgcrypto`
needed), `server_default`s are plain string literals valid on Postgres, and
the Clerk migration (`c4f1a2b3d4e5`) uses a unique *index* on nullable
`clerk_id` — Postgres unique indexes permit multiple NULLs, matching SQLite
semantics. Offline pg-compat coverage lives in
`apps/api/tests/test_pg_compat.py` (engine builds from a pg URL, metadata
compiles on the Postgres dialect, migration chain inspected — no live
server required).

### 4.1 Owner steps: create the Neon project (owner executes)

1. Go to <https://console.neon.tech> → **Create project** (name it e.g.
   `merit-prod`, pick the region closest to the VPS).
2. Copy the **pooled** connection string (Neon shows a "Pooled connection"
   toggle — keep it on) → looks like
   `postgresql://USER:PASSWORD@HOST/dbname?sslmode=require`.
3. Convert the scheme for the psycopg v3 driver (required):
   `postgresql://` → `postgresql+psycopg://`, keeping the rest identical:
   `postgresql+psycopg://USER:PASSWORD@HOST/dbname?sslmode=require`
4. On the VPS, set it in the API env (never commit it — `.env` is
   gitignored):
   ```ini
   # /opt/merit/apps/api/.env (VPS only)
   ENVIRONMENT=production
   SECRET_KEY=<output of: python3 -c "import secrets; print(secrets.token_urlsafe(48))">
   DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/dbname?sslmode=require
   ```
   For `docker compose` deploys, export it instead (compose falls back to
   SQLite when unset — see the `DATABASE_URL` comment in
   `docker-compose.yml`):
   ```bash
   export DATABASE_URL='postgresql+psycopg://USER:PASSWORD@HOST/dbname?sslmode=require'
   ```

### 4.2 Owner steps: cutover commands (owner executes on the VPS)

```bash
cd /opt/merit/apps/api

# 1. Migrate the EMPTY Neon DB to head (safe to re-run; applies all 9 revisions)
DATABASE_URL="$DATABASE_URL" .venv/bin/alembic upgrade head

# 2. Seed verified content ONCE (problems, questions, paths). Re-runs are
#    idempotent — existing rows are skipped, never duplicated.
DATABASE_URL="$DATABASE_URL" .venv/bin/python -m app.seed

# 3. Restart the API so the engine binds the pg URL
sudo systemctl restart merit-api   # or: docker compose up -d --force-recreate api
```

### 4.3 Owner verification (prod, after restart)

```bash
API=https://<vps-host>

# 1. Health
curl -s $API/api/v1/health   # expect {"status":"ok",...}

# 2. Register + login (prod JWT cookies)
curl -s -i -X POST $API/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"owner@example.com","display_name":"Owner","password":"VeryStrongPass123"}' \
| head -12   # expect 201 (or 200 if already registered) + cookies

# 3. One judge submit through the UI (Python or JavaScript only) ->
#    expect a verdict (AC/WA/...) on a real submission row.
```

### 4.4 Notes / known behaviour

- Staging cutover happens with the owner — do not point any shared env at
  Neon without them.
- Never commit a `DATABASE_URL` or password. Prod secrets live only in the
  VPS env / `.env` (gitignored).
- Rolling back to SQLite is just unsetting `DATABASE_URL` (default
  `sqlite:///./merit.db`); no code change needed either way.
- Image builds need no extra step: `apps/api/Dockerfile` installs
  `pyproject.toml`, which now includes `psycopg[binary]`.
