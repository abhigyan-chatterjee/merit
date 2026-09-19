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
