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
5. **Add email + verified claims (REQUIRED):** the backend links accounts by the
    **verified email inside the signed token**. Clerk's default session token
    carries no email, so create a JWT template:
    Configure → **JWT templates** → New template → name it `merit`,
    add claims `{"email": "{{user.primary_email_address}}",
    "email_verified": "{{user.primary_email_address_verified}}",
    "name": "{{user.full_name}}"}`, Save. (`emailVerified` or
    `verified_email` are also accepted as the verified-flag key; what
    matters is the flag is present and true only for a verified email.)
    Then set `VITE_CLERK_JWT_TEMPLATE=merit` on the frontend (see below).
    Without the email claim, login fails with `401 OAUTH_EMAIL_MISSING`;
    with a missing/false verified flag it fails with
    `401 OAUTH_EMAIL_UNVERIFIED` (this blocks takeover via a Clerk
    account holding someone else's unverified email).
6. **Paste keys into env files (never commit — a gitignored env is still a
   secret, so treat the files as sensitive):**

   There are two different `.env` files and they are **not** interchangeable:

   - **`apps/api/.env`** — read by pydantic-settings when the API runs
     *directly* on the host (local dev, `uvicorn app.main:app`). It is **not**
     used by `docker compose`, because compose passes each variable into the
     container explicitly and an explicitly-set (even empty) variable overrides
     anything pydantic would read from `.env` inside the image. Putting a value
     here and deploying with compose looks like it worked and does nothing.
   - **Compose-root `.env`** — a `.env` sitting *next to* `docker-compose.yml`
     (on the VPS: `/home/ubuntu/merit/.env`). This is what
     `${VAR}` interpolation in `docker-compose.yml` reads. **This is the file
     to use for any compose deploy.**

   So for local dev, `apps/api/.env`:
   ```ini
   CLERK_JWKS_URL=https://<frontend-api-domain>/.well-known/jwks.json
   CLERK_AUDIENCE=
   ```
   And for the VPS compose deploy, `/home/ubuntu/merit/.env`:
   ```ini
   SECRET_KEY=<secure random>
   CLERK_JWKS_URL=https://<frontend-api-domain>/.well-known/jwks.json
   CLERK_AUDIENCE=
   VITE_CLERK_PUBLISHABLE_KEY=pk_live_...
   VITE_CLERK_JWT_TEMPLATE=merit
   ```
   `apps/web/.env` (next to `package.json`) applies to the Vite dev server and
   to the web image build, which takes the `VITE_*` values as build args.
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
- Secrets live in `apps/api/.env` for local dev and in the compose-root
  `.env` for VPS deploys (section 1 explains the difference — they are not
  interchangeable). Never commit them, never paste real tokens into tests
  (tests mock JWKS — no network, no real keys).
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
4. On the VPS, set it in the **compose-root** env file
   (`/home/ubuntu/merit/.env`), not `apps/api/.env` — see section 1 for why
   those are not interchangeable:
   ```ini
   # /home/ubuntu/merit/.env (VPS only, never commit)
   ENVIRONMENT=production
   SECRET_KEY=<output of: python3 -c "import secrets; print(secrets.token_urlsafe(48))">
   DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/dbname?sslmode=require
   ```
   `docker-compose.yml` interpolates this file, so `docker compose up -d`
   picks it up. Compose falls back to SQLite when unset — see the
   `DATABASE_URL` comment in `docker-compose.yml`.

   Note `docker compose restart` does **not** re-read `.env`. Use
   `docker compose up -d --force-recreate api` after changing it.

### 4.2 Owner steps: cutover commands (owner executes on the VPS)

```bash
# Migrations run against the DB, not the app, so a host-side venv is fine
# here; the deploy itself lives at /home/ubuntu/merit.
cd /home/ubuntu/merit/apps/api

# 1. Migrate the EMPTY Neon DB to head (safe to re-run; applies all 9 revisions)
DATABASE_URL="$DATABASE_URL" .venv/bin/alembic upgrade head

# 2. Seed verified content ONCE (problems, questions, paths). Re-runs are
#    idempotent — existing rows are skipped, never duplicated.
DATABASE_URL="$DATABASE_URL" .venv/bin/python -m app.seed

# 3. Recreate the API so the engine binds the pg URL. `restart` does not
#    re-read the compose-root .env, so `up -d --force-recreate` is required.
cd /home/ubuntu/merit
docker compose up -d --force-recreate api
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

## 5. 1GB VPS host hardening (shared Oracle VPS, 1 vCPU / 1GB RAM)

No live deploy yet — the owner provisions the VPS later. Everything below
is owner-run on deploy day, ready as written.

### 5.1 Swap: 2GB swapfile (required — the box has only 1GB RAM)

```bash
sudo fallocate -l 2G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h   # expect ~2.0G under Swap
```

### 5.2 `vm.overcommit` sanity

Container limits (`mem_limit` in `docker-compose.yml`) only work if the
kernel is allowed to account that memory. Check before `compose up`:

```bash
sysctl vm.overcommit_memory vm.overcommit_ratio
# expect vm.overcommit_memory = 0 (heuristic) or 1 (always overcommit).
# If it is 2 (strict), either set it back to 0:
#   echo 'vm.overcommit_memory=0' | sudo tee /etc/sysctl.d/99-merit.conf && sudo sysctl --system
# ...or keep 2 and size swap generously, since strict mode counts every
# reservation against RAM+swap.
```

### 5.3 Log rotation (already in compose — do not duplicate elsewhere)

Every service in `docker-compose.yml` carries:

```yaml
logging:
  driver: json-file
  options:
    max-size: "10m"
    max-file: "3"
```

That caps each container at ~30MB of logs. If `docker compose config`
ever shows a service without it, re-add it — unbounded json logs are the
usual way a 1GB disk/RAM box dies quietly.

### 5.4 Judge service (Cloud Run — Python + JavaScript today)

Code execution does **not** run on the VPS. Submissions are sent to a Cloud Run
service that holds no database, no secrets and no user data, and runs under its
own service account with no IAM roles at all.

Set these in the **compose-root** `/home/ubuntu/merit/.env` (see section 1):

```ini
JUDGE_URL=https://merit-judge-light-<hash>-as.a.run.app
GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/judge-sa.json
JUDGE_TIMEOUT_SEC=60
```

`GOOGLE_APPLICATION_CREDENTIALS` is the **in-container** path. Compose mounts
`/home/ubuntu/merit/.judge/` read-only at `/run/secrets/`, so the key lives on
the host at `.judge/judge-sa.json` and appears in the container as
`/run/secrets/judge-sa.json`.

Leaving `JUDGE_URL` empty falls back to the local in-process sandbox — that is
the dev/CI path, not what prod should use.

Full setup, deploy, verification and rollback: `docs/cloud-run-judge.md`.

There is no Piston container. It was removed: nothing called it, it had no
runtimes installed, and it held 300MB of a 951MB host.

### 5.5 Backup drill (pointer — procedure lives in the script)

Do not duplicate the drill here. Run it as documented:

```bash
chmod +x docs/backup_drill.sh
./docs/backup_drill.sh
```

See `docs/launch-checklist.md` §3.3 / §5 for where the drill fits in the
deploy-day sequence.
