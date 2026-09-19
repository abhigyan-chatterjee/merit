# Merit Platform Launch & Hardening Verification Checklist

**Date of Execution:** 2026-09-09
**Platform Status:** PRODUCTION READY
**Repository Branch:** `scope/extension`
**Commit Level:** Verified across scope extension P1–P8

---

## 0. Scope Extension Migrations (run before seed)

```bash
alembic upgrade head   # 7c2e9a41f5b0 (user settings) → 8d3f2b17c6a1 (problem sequence) → 9e4a5c28d7f2 (path summaries)
python3 -m app.seed    # backfills problem topics/sequence, question topics, re-syncs the 3 paths
```

- Old learning paths (`foundations`, `pointers`, `structures`, `algorithms`, `placement-dsa`) are deleted; new slugs are `foundation`, `targeted`, `mastery`. Purge stale `learning_paths` rows if upgrading a dev DB.
- Problem topics use the 18-category taxonomy (`content/taxonomy.py`); old slugs (`arrays`, `strings`, `linked-list`, `dp`) no longer exist.
- Question topics remapped the same way (`arrays`→`arrays-hashing`, `dp`→`dynamic-programming`, etc.); `complexity` folded into `sorting`, CS topics into `data-structures`. New banks: `aptitude`, `core-cs`.
- `users` gains `preferred_language` (default `javascript`) and `daily_goal_json`.
- `problems` gains `sequence`, `prev_slug`, `next_slug`. `path_steps` gains `summary`, `reading_links_json`.
- Sampler no longer widens empty topics: unknown topics return 404 `NO_QUESTIONS_FOR_TOPICS`.

---

## 1. Executive Summary & Verification Matrix

| Layer | Verification Gate | Status | Evidence / Artifact |
|---|---|---|---|
| **Frontend Codebase** | Vitest unit/component suite & React 19 testing | **PASSED** | 12 tests across visualizers, auth, code runner, quiz engine, admin |
| **Frontend Build** | Vite production bundle & Route chunking | **PASSED** | Code-split into lazy route chunks with Suspense fallbacks |
| **Correctness Defects** | D1–D12 Base Audit defects | **100% RESOLVED** | Verified: node-based BST/Heap, SVG scaling, dedicated visualizers |
| **Security & Auth** | Argon2id + rotating refresh tokens + theft detection | **PASSED** | HttpOnly, SameSite=Lax, Secure cookies; strict sub claim validation |
| **User Data Isolation** | Server-side user_id filtering authz matrix | **PASSED** | `apps/api/tests/test_authz.py` asserts complete cross-user isolation |
| **Sandboxed Judge** | Piston runner replacing `new Function()` | **PASSED** | Process sandbox, timeout bounds, zero browser code evaluation |
| **Content Bank** | 885 Unique verified questions & 42 original problems | **PASSED** | `python3 content/validators/run_all.py` (42/42 AC, 885 verified) |
| **Adaptive Quizzes** | 50-exposure no-repeat window & server-side snapshots | **PASSED** | `test_quizzes.py` confirms no answer leakage + 404 on unknown topics; 20s auto-advance |
| **Learning Paths v2** | Server-resolved step completion & next pointer | **PASSED** | Foundation, Targeted, Mastery (summaries + reading links per step) |
| **Placement Features** | Spaced-repetition revision queue & Timed mock exam | **PASSED** | 20 MCQ + 2 coding exams (7 types incl. 3h full mock); rolling weak areas |
| **User Accounts** | Dropdown + profile/email/password/language | **PASSED** | `PATCH /me`, `POST /email`, `POST /password`, `/profile` page, preferred language |
| **Admin Console** | Review queue, coverage matrix, audit trail | **PASSED** | `role='admin'` guard; students strictly receive 403 Forbidden |
| **Deployment & Ops** | Docker Compose, SPA fallback, SQLite WAL & Postgres | **PASSED** | `docker-compose.yml`, `nginx.conf`, `vercel.json`, `backup_drill.sh` |

---

## 2. Invariants & Security Guardrails Verification

- [x] **Invariant 1: User Data Isolation.** Every user-scoped database query filters server-side via `Table.user_id == current_user.id`. No client-supplied user ID is trusted or accepted.
- [x] **Invariant 2: Eradication of `new Function()`.** All browser code runner execution has been eliminated. Execution is delegated to the isolated Piston judge service with resource limits and exact JSON output equality.
- [x] **Invariant 3: Zero Hand-Typed Expected Outputs.** Every test case expectation in `content/problems/` was verified by executing reference solutions in Python and JavaScript.
- [x] **Invariant 4: Quiz Answer Secrecy.** `GET /questions` and `POST /quizzes/generate` return question prompts and options only; `correct_index` and `explanation` are withheld until post-submission grading.
- [x] **Invariant 5: Refresh Token Rotation & Theft Detection.** Every refresh rotation issues a new refresh token and invalidates the prior token. Reuse of a revoked token triggers revocation of all active sessions for that account.
- [x] **Invariant 6: Privacy Rights (GDPR/CCPA Compliance).** `GET /api/v1/auth/export` produces a JSON dump of all user notes, problem progress, quiz attempts, and activity history. `DELETE /api/v1/auth/account` cascades and purges all user data.

---

## 3. Deployment & Operational Runbook

### 3.1 Single-Node Compose Launch
```bash
# 1. Start all containers (Piston, API, Web Nginx)
docker compose up -d

# 2. Verify container health
docker compose ps
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
