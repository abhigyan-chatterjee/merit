# Merit Platform Launch & Hardening Verification Checklist

**Date of Execution:** 2026-09-09, re-verified 2026-11-24
**Platform Status:** LIVE — `merit.nullbit.in`, judge on Cloud Run (light + heavy)
**Repository Branch:** `scope/extension`
**Commit Level:** Re-verified after the interview portal, placement readiness, expanded content bank, and security-hardening pass

---

## 0. Scope Extension Migrations (run before seed)

```bash
alembic upgrade head   # … → 7c2e9a41f5b0 (user settings) → 8d3f2b17c6a1 (problem sequence)
                       # → 9e4a5c28d7f2 (path summaries) → … → f6b2c3d4e5a8 (problem companies)
                       # → a7c3d4e5f6b9 (placement target settings) → b8d4e5f6a7c0 (interview sessions)
python3 -m app.seed    # backfills problem topics/sequence/companies, question topics, re-syncs the 6 paths
```

- Old learning paths (`foundations`, `pointers`, `structures`, `algorithms`, `placement-dsa`) are deleted; current slugs are `foundation`, `targeted`, `mastery`, `tcs-nqt`, `infosys-sp-dse`, `product-50`. Purge stale `learning_paths` rows if upgrading a dev DB.
- Problem topics use the 18-category taxonomy (`content/taxonomy.py`); old slugs (`arrays`, `strings`, `linked-list`, `dp`) no longer exist.
- Question topics remapped the same way (`arrays`→`arrays-hashing`, `dp`→`dynamic-programming`, etc.); `complexity` folded into `sorting`, CS topics into `data-structures`. New banks: `aptitude`, `core-cs`.
- `users` gains `preferred_language` (default `python`) and `daily_goal_json`.
- `problems` gains `sequence`, `prev_slug`, `next_slug`. `path_steps` gains `summary`, `reading_links_json`.
- Sampler no longer widens empty topics: unknown topics return 404 `NO_QUESTIONS_FOR_TOPICS`.

---

## 1. Executive Summary & Verification Matrix

| Layer | Verification Gate | Status | Evidence / Artifact |
|---|---|---|---|
| **Frontend Codebase** | Vitest unit/component suite & React 19 testing | **PASSED** | 397 tests across 55 files (visualizers, interview portal, review deck, auth, code runner, quiz engine, admin) |
| **Frontend Build** | Vite production bundle & Route chunking | **PASSED** | Code-split into lazy route chunks with Suspense fallbacks |
| **Correctness Defects** | D1–D12 Base Audit defects | **100% RESOLVED** | Verified: node-based BST/Heap, SVG scaling, dedicated visualizers |
| **Security & Auth** | Argon2id + rotating refresh tokens + theft detection | **PASSED** | HttpOnly, SameSite=Strict, Secure cookies; strict sub claim validation |
| **Security Hardening** | CSP, request-size cap, rate limits, prod config refusal | **PASSED** | Enforcing CSP in `apps/web/nginx.conf`; global `BodyLimitMiddleware`; judge + interview rate limits; prod refuses to start without `JUDGE_URL`; BYOK tutor/interview require login |
| **User Data Isolation** | Server-side user_id filtering authz matrix | **PASSED** | `apps/api/tests/test_authz.py` asserts complete cross-user isolation |
| **Sandboxed Judge** | Cloud Run judge service replacing `new Function()` | **PASSED** | Runs in its own container with no secrets/database, zero browser code evaluation |
| **Content Bank** | 574 verified questions & 274 original problems | **PASSED** | `content/validators/run_all.py` (274/274 AC, 574 verified questions; 772 total, 198 drafts quarantined; 181 distinct designs) |
| **Adaptive Quizzes** | 50-exposure no-repeat window & server-side snapshots | **PASSED** | `test_quizzes.py` confirms no answer leakage + 404 on unknown topics; 20s auto-advance |
| **Learning Paths v2** | Server-resolved step completion & next pointer | **PASSED** | 6 paths: Foundation, Targeted, Mastery, TCS NQT, Infosys SP/DSE, Product 50 |
| **Placement Features** | Spaced-repetition queue, readiness score, diagnostic & timed exams | **PASSED** | 11 timed exams (incl. 3h full mock), Retry Wrong drill, 12-question diagnostic, `/review` SM-2 deck |
| **AI Mock Interview Portal** | Multi-round live-judged interviewing | **PASSED** | `/interview` + `/interview/:sessionId`; Easy/Medium/Hard loops, embedded `CodeRunner`, CV PDF ≤ 2 MiB parsed in memory, `interview_sessions` persistence, structured rubrics |
| **Feedback Privacy** | Public issue vs private contact email | **PASSED** | Optional contact email stored in DB only; never included in the public GitHub issue body |
| **User Accounts** | Dropdown + profile/email/password/language | **PASSED** | `PATCH /me`, `POST /email`, `POST /password`, `/profile` page, preferred language |
| **Admin Console** | Review queue, coverage matrix, audit trail | **PASSED** | `role='admin'` guard; students strictly receive 403 Forbidden |
| **Deployment & Ops** | Docker Compose, SPA fallback, SQLite WAL & Postgres | **PASSED** | `docker-compose.yml` (`no-new-privileges:true`), `nginx.conf` (CSP), `backup_drill.sh` |

---

## 2. Invariants & Security Guardrails Verification

- [x] **Invariant 1: User Data Isolation.** Every user-scoped database query filters server-side via `Table.user_id == current_user.id`. No client-supplied user ID is trusted or accepted.
- [x] **Invariant 2: Eradication of `new Function()`.** All browser code runner execution has been eliminated. Execution is delegated to the isolated Cloud Run judge service with resource limits and exact JSON output equality. See `docs/cloud-run-judge.md`.
- [x] **Invariant 3: Zero Hand-Typed Expected Outputs.** Every test case expectation in `content/problems/` was verified by executing reference solutions in Python and JavaScript.
- [x] **Invariant 4: Quiz Answer Secrecy.** `GET /questions` and `POST /quizzes/generate` return question prompts and options only; `correct_index` and `explanation` are withheld until post-submission grading.
- [x] **Invariant 5: Refresh Token Rotation & Theft Detection.** Every refresh rotation issues a new refresh token and invalidates the prior token. Reuse of a revoked token triggers revocation of all active sessions for that account.
- [x] **Invariant 6: Privacy Rights (GDPR/CCPA Compliance).** `GET /api/v1/auth/export` produces a JSON dump of all user notes, problem progress, quiz attempts, and activity history. `DELETE /api/v1/auth/account` cascades and purges all user data.

---

## 3. Deployment & Operational Runbook

### 3.1 Single-Node Compose Launch
Use `docker-compose` (standalone v5 at `/usr/local/bin/docker-compose`) or the
plugin form `docker compose`; the commands below work with either.

```bash
# 1. Start all containers (API, Web Nginx)
docker-compose up -d

# 2. Verify container health
docker-compose ps
curl -i http://localhost/api/v1/health
```

### 3.2 Switching to PostgreSQL
The backend is completely database-agnostic through SQLAlchemy 2.0. To switch from SQLite to PostgreSQL:
```env
DATABASE_URL=postgresql://merit_user:secure_password@postgres_host:5432/merit_db
```
Apply migrations:
```bash
alembic upgrade head
python3 -m app.seed
```

### 3.3 Database Backup & Restore Drill
Run the verified automated backup drill:
```bash
chmod +x docs/backup_drill.sh
./docs/backup_drill.sh
```
This performs a safe SQLite WAL checkpoint (`PRAGMA wal_checkpoint(TRUNCATE)`), creates a consistent online snapshot, verifies 0600 file permissions, and simulates restore.

---

## 4. Launch Sign-Off
All automated tests, static checks, and runtime requirements have been satisfied.
Platform is ready for deployment.

---

## 5. Deploy-day runbook (owner executes on the 1GB VPS)

Playwright e2e IS configured in this repo (`apps/web/playwright.config.ts`
+ `apps/web/e2e/*.spec.ts`), so the automated e2e step below stands. If it
were absent, the manual smoke list alone would be the gate — do not build a
new harness either way.

### 5.1 VPS prep

```bash
# Docker + compose (`docker-compose` standalone v5 at /usr/local/bin/docker-compose,
# or the `docker compose` plugin), then host hardening (details: docs/prod.md §5)
free -h                          # after: expect ~2G swap (swapfile)
sysctl vm.overcommit_memory      # expect 0 or 1, never 2 without extra swap
git clone <forge-url> /home/ubuntu/merit && cd /home/ubuntu/merit
git checkout scope/extension
```

### 5.2 Env (never commit — all gitignored / exported)

```bash
export SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
export DATABASE_URL='postgresql+psycopg://USER:PASSWORD@HOST/dbname?sslmode=require'  # Neon pooled
# Clerk (see docs/prod.md §1): CLERK_JWKS_URL (+ CLERK_AUDIENCE if used) in
# apps/api/.env; VITE_CLERK_PUBLISHABLE_KEY + VITE_CLERK_JWT_TEMPLATE=merit
# in apps/web/.env, then rebuild web.
```

### 5.3 Compose up (1GB budget: api 350m / web 64m)

```bash
docker-compose config   # must parse clean
docker-compose up -d --build
docker-compose ps
# Judge runs on Cloud Run and needs no container here. Wire it up first:
#   ./apps/judge/deploy.sh bootstrap
#   ./apps/judge/deploy.sh deploy && TIER=heavy ./apps/judge/deploy.sh deploy
#   then set JUDGE_URL + JUDGE_HEAVY_URL + GOOGLE_APPLICATION_CREDENTIALS in the
#   repo-root .env (compose reads that file, not apps/api/.env).
# See docs/cloud-run-judge.md.
# The deployed tiers must accept the languages the editor offers: an out-of-date
# light service rejects Java outright with "Unsupported language 'java'".
curl -s -o /dev/null -w "judge %{http_code}\n" "$JUDGE_URL/health"   # 403 = up, unauthenticated
```

### 5.4 Migrate + seed (Neon is empty at cutover; idempotent re-runs)

```bash
cd /home/ubuntu/merit/apps/api
DATABASE_URL="$DATABASE_URL" .venv/bin/alembic upgrade head
DATABASE_URL="$DATABASE_URL" .venv/bin/python -m app.seed
```

### 5.5 Smoke (manual gate — every item must pass)

- [ ] `curl -s https://<vps-host>/api/v1/health` → `{"status":"ok",...}`
- [ ] Register via UI (or `POST /api/v1/auth/register`) → 201 + cookies
- [ ] Clerk login (Google/GitHub) → linked/created, cookies issued
- [ ] Solve one problem in Python, JavaScript, Java and C++ → real verdict rows
      (Java/C++ require `JUDGE_HEAVY_URL`; a wrong return type must come back as a
      Compile Error, never a Wrong Answer)
- [ ] Generate + submit a quiz → graded, no answer leakage pre-submit
- [ ] Start + submit a timed mock exam → score recorded
- [ ] `/review` → due SM-2 cards render; rating a card advances its interval
- [ ] Signed-out visit to tutor/interview → sign-in prompt only, no BYOK key accepted
- [ ] Tutor panel signed in WITHOUT a key → mocked/offline path, no crash; with a
      pasted key → all 4 modes (Socratic, Step Hint, Code Review, Mock Interview) and
      preset selector show OpenAI (default) + Gemini
- [ ] `/interview` → start an Easy/Medium/Hard loop, solve a coding round in the
      embedded runner, end and score a rubric; session survives reload/another device
- [ ] Logout → cookies cleared, protected routes redirect to login

### 5.6 Automated e2e (configured — run it)

```bash
cd /home/ubuntu/merit/apps/web && npx playwright test
# expects: clerk-setup + chromium projects green across smoke.spec.ts,
# browse.spec.ts and judge.spec.ts. Neither the judge nor the browser specs need
# Clerk; auth.spec.ts skips itself unless CLERK_TEST_EMAIL/PASSWORD are exported.
```

### 5.7 Backup drill

```bash
chmod +x docs/backup_drill.sh && ./docs/backup_drill.sh
# expect WAL checkpoint + snapshot + 0600 perms + restore verify
```

### 5.8 Reverse proxy: `merit.nullbit.in` (subdomain + TLS)

- DNS: `merit.nullbit.in` → A record → VPS public IP (proxy host, not the
  compose `web:80` directly if other apps share port 80/443).
- Proxy (host nginx/Caddy) forwards `merit.nullbit.in` → `127.0.0.1:80`
  (compose `web`), preserving `Host` + `X-Forwarded-*`; API same-origin
  under `/api` so no extra CORS entry is needed.
- TLS: terminate at the proxy (certbot/Caddy auto-TLS); `Secure` cookies
  require HTTPS — plain-HTTP smoke is for localhost only.
- If port 80 is taken by existing apps, bind compose web to
  `127.0.0.1:<free-port>:80` and point the vhost at that port.
