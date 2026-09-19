# MERIT Cleanup & Extension Plan

> **For Hermes / implementing agents:** Execute this plan phase-by-phase. Before starting each phase, expand its tasks into bite-sized TDD tasks per the `writing-plans` skill (failing test → implement → pass → commit). Do not skip verification gates. Do not modify `main` directly — one branch per task.

**Goal:** Turn the current client-only DSA visualizer prototype into a multi-user, placement-grade DSA practice platform with accurate algorithm visualizations, a verified 5,000-question bank, dynamic quizzes, guided + individual problem paths, and per-user progress stored in a database.

**Architecture:** Keep the existing Vite + React 19 + TS + Tailwind frontend (UI is good; `apps/web`). Add a FastAPI + SQLAlchemy 2.0 + Alembic backend (`apps/api`) backed by SQLite (WAL mode), with a self-hosted Piston judge for sandboxed code execution. Content (problems, questions, generators, validators) lives in `content/` and is loaded into the DB only after passing automated verification.

**Tech Stack:** React 19 / TS / Tailwind 4 (existing) · FastAPI · SQLAlchemy 2.0 · Alembic · SQLite (WAL) · argon2id + JWT (httpOnly cookies) · Piston (code judge) · Vitest + Playwright · pytest · GitHub Actions CI

---

## 0. Scope Decisions (contradictions resolved — do not relitigate)

| Topic | Decision | Why |
|---|---|---|
| Auth ("maybe") | **Core.** Email + password only, in Phase 2 | "Each user's data separate" + "no unauthorized access" are impossible without auth |
| OAuth / Google login / payments | **Excluded** | Explicitly out of scope |
| SQLite vs PostgreSQL | **SQLite now** (WAL, single-node). Postgres is a config-level migration later via SQLAlchemy URL; CI runs the test suite against Postgres in a matrix job from Phase 10 | Stated scope says SQLite; PG listed "maybe" |
| Admin dashboard ("maybe") | **Minimal version in scope (Phase 9):** content review queue + aggregate stats only | The question-bank accuracy workflow requires a review surface |
| 5,000 questions | **Staged:** 750 verified → 2,500 → 5,000. Templated generators produce *programmatically verified* items at scale; curated items pass a validation pipeline. Nothing publishes with `review_status != 'verified'` | "No false data" forbids bulk unverified generation |
| Code execution | **Phase 4a:** Web Worker + timeout (interim). **Phase 4b:** self-hosted Piston for JS/Python/C++/Java | Current `new Function()` is same-origin eval — must be removed |
| Guest mode | Visualizers + reading problems work logged-out. Progress/quizzes/submissions require an account. On first login, localStorage progress is imported and merged (max-wins) | Privacy + data separation |
| Problem statements | **Original content only.** No scraped LeetCode/GFG text (licensing). Titles/concepts may be classic; statements are written fresh | Legal accuracy requirement |

**Hard invariants (apply to every phase):**
1. Every user-scoped query is filtered server-side by the authenticated user's id. No client-supplied user ids are ever trusted.
2. No task is "done" without: tests written, tests passing in CI, and the phase's verification command run green.
3. No content (problem, test case, question, answer, explanation) ships unless the content validator passes it. Expected outputs are always *computed by running the reference solution*, never hand-typed.

---

## 1. Current State Audit (verified 2026-09-07 — this is the cleanup backlog)

Verified facts from review + browser testing of the base at commit `8737bf7`:

| # | Defect | Evidence |
|---|---|---|
| D1 | 7 of 12 "visualizers" render the same generic array UI | `apps/web/src/pages/VisualizerDetailPage.tsx:27-34` falls through to `LinearVisualizer` for array, linked-list, stack, queue, hashmap, searching, recursion-tree |
| D2 | BST/heap insertion is `next.sort()` rendered as a complete tree — violates BST invariant | `apps/web/src/visualizers/TreeVisualizer.tsx:62-67` |
| D3 | Graph click-to-add uses CSS px against a `0 0 420 350` viewBox; nodes land outside the canvas | `apps/web/src/visualizers/GraphVisualizer.tsx:165-173` |
| D4 | Learning-path visualizer completion derives from single `lastVisited` slot; visiting one un-completes another | `apps/web/src/pages/GuidedPathDetailPage.tsx:51-53` |
| D5 | Invalid dynamic routes silently show fallback content (`/visualizers/x` → sorting header + unknown structure; `/problems/graphs/two-sum` renders) | `VisualizerDetailPage.tsx:16`, `ProblemDetailPage.tsx:21`, `QuizPage.tsx:12-13` |
| D6 | Code runner is `new Function()` on the main thread: full DOM/localStorage access, infinite loop freezes UI | `apps/web/src/components/CodeRunner.tsx:42-44` |
| D7 | New users start with fabricated progress (5-day streak, 4 quiz scores, 4 solved problems) | `apps/web/src/store/ProgressContext.tsx:40-78` |
| D8 | Streak math uses UTC `toISOString()` — wrong day boundary for IST users | `apps/web/src/hooks/useStreak.ts:3-6` |
| D9 | localStorage JSON trusted without schema validation | `apps/web/src/hooks/useLocalStorage.ts:4-11` |
| D10 | `curriculum.ts` advertises operations with no controls (put/get/delete, sift-up/down, fib tree, peek, front, reverse…) | `apps/web/src/data/curriculum.ts` vs `LinearVisualizer.tsx:81-105` |
| D11 | No tests, no lint, no CI | `package.json` has only dev/build/preview |
| D12 | `BrowserRouter` needs SPA fallback on static hosts | `apps/web/src/App.tsx:10` |

---

## 2. Target Repo Layout

```
merit/
├── apps/
│   ├── web/                  # existing frontend, moved as-is then fixed
│   │   ├── src/...
│   │   ├── tests/            # Vitest unit/component tests
│   │   └── e2e/              # Playwright
│   └── api/
│       ├── app/
│       │   ├── main.py
│       │   ├── config.py
│       │   ├── db.py
│       │   ├── models/       # SQLAlchemy models
│       │   ├── schemas/      # pydantic request/response
│       │   ├── routers/      # auth, progress, problems, quizzes, paths, judge, admin
│       │   ├── services/     # auth, sampler, streak, importer
│       │   └── security.py
│       ├── alembic/
│       └── tests/            # pytest, incl. authz matrix
├── content/
│   ├── problems/             # one YAML/JSON per problem
│   ├── questions/            # curated question files
│   ├── generators/           # templated question generators (verified)
│   ├── paths/                # learning path definitions
│   └── validators/           # content pipeline (see Phase 5)
├── docs/plans/               # this plan + phase expansions
├── .github/workflows/ci.yml
└── README.md
```

**Phase 0 task:** `git mv` the current frontend into `apps/web/` (preserves history), create the skeletons above, commit.

---

## 3. Database Schema (target; Alembic-managed)

```sql
-- auth
users(id TEXT PK, email TEXT UNIQUE NOT NULL, display_name TEXT NOT NULL,
      password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'student',  -- student|admin
      is_active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL, last_login_at TEXT);
refresh_tokens(id TEXT PK, user_id TEXT NOT NULL REFERENCES users(id),
      token_hash TEXT NOT NULL, expires_at TEXT NOT NULL, created_at TEXT NOT NULL,
      revoked_at TEXT, replaced_by TEXT, user_agent TEXT, ip TEXT);

-- content (shared, not user data)
problems(slug TEXT PK, topic TEXT NOT NULL, difficulty TEXT NOT NULL, pattern TEXT NOT NULL,
      title TEXT NOT NULL, statement TEXT NOT NULL, examples TEXT NOT NULL,      -- json
      constraints_json TEXT NOT NULL, hints TEXT NOT NULL,                        -- json
      starter_code TEXT NOT NULL,       -- json: {language: code}
      function_name TEXT NOT NULL, time_limit_ms INTEGER NOT NULL DEFAULT 2000,
      review_status TEXT NOT NULL DEFAULT 'draft', created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
problem_test_cases(id INTEGER PK, problem_slug TEXT NOT NULL REFERENCES problems(slug),
      ordinal INTEGER NOT NULL, label TEXT NOT NULL, input_json TEXT NOT NULL,
      expected_json TEXT NOT NULL, is_sample INTEGER NOT NULL DEFAULT 0);
problem_solutions(id INTEGER PK, problem_slug TEXT NOT NULL REFERENCES problems(slug),
      title TEXT NOT NULL, complexity TEXT NOT NULL, language TEXT NOT NULL DEFAULT 'javascript',
      code TEXT NOT NULL, is_reference INTEGER NOT NULL DEFAULT 0);
questions(id TEXT PK, topic TEXT NOT NULL, subtopic TEXT, difficulty TEXT NOT NULL,
      qtype TEXT NOT NULL DEFAULT 'mcq', prompt TEXT NOT NULL, options TEXT NOT NULL, -- json
      correct_index INTEGER NOT NULL, explanation TEXT NOT NULL,
      source TEXT NOT NULL,              -- curated|generated
      generator_key TEXT, content_hash TEXT NOT NULL,
      review_status TEXT NOT NULL DEFAULT 'draft', created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
question_reviews(id INTEGER PK, question_id TEXT NOT NULL REFERENCES questions(id),
      reviewer_id TEXT NOT NULL REFERENCES users(id), action TEXT NOT NULL,  -- approved|rejected|edited
      note TEXT, created_at TEXT NOT NULL);
learning_paths(slug TEXT PK, title TEXT NOT NULL, blurb TEXT NOT NULL, icon TEXT NOT NULL,
      track TEXT NOT NULL,               -- foundational|specialised|placement
      ordinal INTEGER NOT NULL, is_published INTEGER NOT NULL DEFAULT 0);
path_steps(id INTEGER PK, path_slug TEXT NOT NULL REFERENCES learning_paths(slug),
      ordinal INTEGER NOT NULL, step_type TEXT NOT NULL,   -- visualizer|problem|quiz|mock
      ref_id TEXT NOT NULL, title TEXT);

-- user data (EVERY table here has user_id; queries MUST filter on it)
problem_progress(user_id TEXT NOT NULL REFERENCES users(id), problem_slug TEXT NOT NULL,
      status TEXT NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY(user_id, problem_slug));
submissions(id TEXT PK, user_id TEXT NOT NULL REFERENCES users(id), problem_slug TEXT NOT NULL,
      language TEXT NOT NULL, code TEXT NOT NULL, verdict TEXT NOT NULL,
      runtime_ms REAL, test_results TEXT NOT NULL, created_at TEXT NOT NULL);
notes(user_id TEXT NOT NULL, problem_slug TEXT NOT NULL, text TEXT NOT NULL,
      updated_at TEXT NOT NULL, PRIMARY KEY(user_id, problem_slug));
bookmarks(user_id TEXT NOT NULL, item_type TEXT NOT NULL, item_id TEXT NOT NULL,
      created_at TEXT NOT NULL, PRIMARY KEY(user_id, item_type, item_id));
activity_days(user_id TEXT NOT NULL, day TEXT NOT NULL,   -- local date YYYY-MM-DD
      action_count INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(user_id, day));
visualizer_completions(user_id TEXT NOT NULL, visualizer_id TEXT NOT NULL,
      visits INTEGER NOT NULL DEFAULT 1, first_completed_at TEXT NOT NULL,
      PRIMARY KEY(user_id, visualizer_id));
quiz_attempts(id TEXT PK, user_id TEXT NOT NULL, topic_spec TEXT NOT NULL,  -- json {topics:[], difficulty}
      question_ids TEXT NOT NULL,     -- json snapshot, enables retry-wrong + review
      total INTEGER NOT NULL, correct INTEGER NOT NULL, score_pct INTEGER NOT NULL,
      duration_sec INTEGER NOT NULL, created_at TEXT NOT NULL);
quiz_attempt_answers(id INTEGER PK, attempt_id TEXT NOT NULL REFERENCES quiz_attempts(id),
      question_id TEXT NOT NULL, selected_index INTEGER, is_correct INTEGER NOT NULL);
user_question_exposure(user_id TEXT NOT NULL, question_id TEXT NOT NULL, shown_at TEXT NOT NULL,
      PRIMARY KEY(user_id, question_id));   -- powers no-repeat sampling
path_step_progress(user_id TEXT NOT NULL, step_id INTEGER NOT NULL, completed_at TEXT NOT NULL,
      PRIMARY KEY(user_id, step_id));
admin_audit_log(id INTEGER PK, admin_id TEXT NOT NULL, action TEXT NOT NULL,
      target TEXT NOT NULL, created_at TEXT NOT NULL);
```

Indexes: `submissions(user_id, problem_slug)`, `quiz_attempts(user_id, created_at)`, `questions(topic, difficulty, review_status)`, `user_question_exposure(user_id, shown_at)`.

SQLite pragmas on connect: `PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;`.

---

## 4. API Surface (v1)

All under `/api/v1`. Errors: `{"error": {"code": "...", "message": "..."}}` with proper HTTP status. Auth via httpOnly cookies (`av_access`, `av_refresh`), never response-body tokens.

| Group | Endpoint | Notes |
|---|---|---|
| auth | `POST /auth/register` · `POST /auth/login` · `POST /auth/logout` · `POST /auth/refresh` · `GET /auth/me` · `DELETE /auth/account` · `GET /auth/export` | rate-limited; refresh rotation; export/delete = privacy rights |
| content | `GET /problems?topic=&difficulty=&status=` · `GET /problems/{slug}` · `GET /visualizers` · `GET /paths` · `GET /paths/{slug}` | public read; only `review_status='verified'` |
| progress | `GET/PUT /progress/problems/{slug}` · `GET/PUT /progress/notes/{slug}` · `POST /progress/bookmarks/toggle` · `POST /progress/visualizers/{id}/visit` · `GET /progress/summary` · `POST /progress/import-local` | all user-scoped; import-local = one-time localStorage merge |
| quiz | `POST /quizzes/generate` (body: topics[], count, difficulty?) · `POST /quizzes/attempts` (answers) · `GET /quizzes/attempts/{id}` · `POST /quizzes/attempts/{id}/retry-wrong` | server samples from verified questions; snapshot question_ids |
| judge | `POST /judge/run` (sample tests) · `POST /judge/submit` (all tests → submission row) | per-user rate limit; verdicts AC/WA/TLE/RE |
| admin | `GET /admin/review-queue?type=` · `POST /admin/questions/{id}/review` · `POST /admin/problems/{slug}/review` · `GET /admin/stats` | role=admin; every call writes `admin_audit_log` |

---

## 5. Phases

---

### PHASE 0 — Repo & tooling foundation

**Tasks**
1. `git mv` frontend into `apps/web/`; create `apps/api/`, `content/`, `docs/plans/`; commit.
2. Frontend tooling: ESLint (typescript-eslint + react-hooks) + Prettier; add `test` script (Vitest), `e2e` script (Playwright); install deps.
3. Backend tooling: uv/pip-tools; ruff + mypy strict-ish; pytest + httpx TestClient.
4. pre-commit (ruff, prettier, mypy, eslint).
5. CI skeleton `.github/workflows/ci.yml`: jobs `web-lint`, `web-test`, `api-test`, `content-validate` (stub passing). All future phases must keep these green; add jobs as features land.

**Verification:** `cd apps/web && npm run lint && npm test`; `cd apps/api && pytest -q`; CI green on the PR.

---

### PHASE 1 — Correctness cleanup of the current app (fixes D1–D12)

Backend does not exist yet; everything stays localStorage-backed. Each fix = one branch, Vitest coverage, commit.

1. **D5 route validation + 404.** Create `apps/web/src/components/NotFound.tsx`. In `VisualizerDetailPage`/`ProblemDetailPage`/`QuizPage`/`GuidedPathDetailPage`: if the param doesn't resolve, render `<NotFound/>` instead of falling back. Test: unknown id renders 404 UI, not Two Sum.
2. **D3 graph coordinates.** Scale pointer px → viewBox units:
   ```ts
   const rect = e.currentTarget.getBoundingClientRect();
   const [vbW, vbH] = [420, 350];
   const x = Math.round((e.clientX - rect.left) * (vbW / rect.width));
   const y = Math.round((e.clientY - rect.top) * (vbH / rect.height));
   ```
   Test: click at rendered (90%, 84%) → stored node inside `[0,420]×[0,350]` and circle visible.
3. **D2 real trees.** Rewrite `TreeVisualizer` around a node-based model (`{id, value, left, right}`), not a sorted array:
   - `binary-tree`: level-order insertion into first open slot.
   - `bst`: standard BST insert (left if `<`, right if `>=`), animated search path.
   - `heap`: array-backed heap with animated sift-up on insert, sift-down on extract-root; min/max toggle per `curriculum.ts`.
   Property tests (fast-check or hand-rolled): after N random inserts, inorder(BST) is sorted; heap parent-child invariant holds after every operation; traversals produce expected orders on a fixed fixture tree.
4. **D1/D10 split placeholder visualizers.** One dedicated component per id under `apps/web/src/visualizers/`: `ArrayVisualizer` (index access/insert-at/delete-at + two-pointer scan), `LinkedListVisualizer` (head/tail insert, delete, reverse with pointer rewiring frames), `StackVisualizer` (push/pop/peek/clear), `QueueVisualizer` (enqueue/dequeue/front; circular buffer), `HashMapVisualizer` (buckets + separate chaining: put/get/delete, collision demonstration), `SearchingVisualizer` (linear vs binary side-by-side stepper), `RecursionTreeVisualizer` (fib(n) call tree with memoized-node highlighting; factorial call stack). Reuse the existing frame-recorder pattern from `SortingVisualizer` (compute all frames up front, scrub/play via `ControlBar`). Then update `curriculum.ts` `keyOperations` to match implemented controls exactly, and fix the README feature list. Test: every id in `VISUALIZERS` renders its own component (registry map, no fallthrough), and each generator's frames validate (e.g., stack LIFO order invariant).
5. **D4 visualizer completion tracking.** Add `visitedVisualizers: string[]` to the store (replacing the `lastVisited`-derived rule in `GuidedPathDetailPage.tsx:51-53`: `done = state.visitedVisualizers.includes(step.id)`). Record a visit on mount of `VisualizerDetailPage`. Test: visiting array then returning to path keeps sorting done.
6. **D7 honest initial state.** Empty `INITIAL_STATE` (no fake streak/scores/solved). Add empty-state UI to Dashboard (heat map empty, "start your first problem" CTA). Test: fresh storage → 0s everywhere.
7. **D8 local-date streaks.** Replace `toISOString().split('T')[0]` with a local `yyyy-mm-dd` formatter (`getFullYear/getMonth/getDate`) in `useStreak.ts` and anywhere else dates are derived. Test with a mocked Date at 02:00 IST → today is the local date.
8. **D9 storage schema validation.** Add zod schema for `merit_store_v1`; on parse failure or version mismatch, back up the raw value to `merit_store_v1.backup` and reset to defaults (never crash). Test: corrupted JSON and wrong-shape JSON both recover.
9. **D6 interim (until Phase 4):** move `new Function` execution into a Web Worker (`apps/web/src/workers/runner.worker.ts`) with `postMessage` + `setTimeout` kill at 3s; Worker scope has no DOM/localStorage. This is the *interim* — Phase 4 replaces with server judge.
10. **D12 SPA fallback:** document + provide `vercel.json`/`_redirects`/nginx snippet in README deploy section.

**Phase gate (run all):** `npm run lint && npm test && npm run build`; Playwright smoke: all 12 visualizer routes load, invalid route → 404, sorting step advances, BST insert keeps invariant highlighted correctly.

---

### PHASE 2 — Backend foundation + email/password auth

**Tasks**
1. `apps/api` skeleton: FastAPI app, `config.py` (pydantic-settings, env-driven), structured logging, `db.py` engine/session with the pragmas above. Alembic init; first migration: `users`, `refresh_tokens`.
2. `security.py`: argon2id hashing (`pwdlib[argon2]`), JWT encode/decode (`pyjwt`), cookie set/clear helpers. Access token 15 min; refresh 30 days, **rotating**: every `/auth/refresh` issues a new refresh token, stores only its hash, revokes the old; reuse of a revoked token revokes the whole chain (theft detection).
3. Auth routes: register (validate email format, password ≥ 10 chars, generic "email already registered" handling that doesn't enumerate), login (constant-time compare path; rate limit 5/min/IP + exponential backoff per account), logout, refresh, `GET /auth/me`. Set cookies: `HttpOnly; Secure; SameSite=Lax; Path=/`.
4. Ownership dependency used by every user-scoped route:
   ```python
   # app/security.py
   def current_user(request: Request, db: Session = Depends(get_db)) -> User:
       token = request.cookies.get("av_access")
       payload = decode_access(token)  # raises 401
       user = db.get(User, payload["sub"])
       if not user or not user.is_active: raise HTTPException(401)
       return user
   ```
   Rule for all queries: `.where(Table.user_id == user.id)` — the client never sends a user id.
5. **Authz test matrix** (`apps/api/tests/test_authz.py`): two registered users A and B; for every user-data endpoint added in Phase 3+, assert B gets 404/403 on A's resources and sees none of A's rows in list endpoints. This file is the privacy MUST made executable; every later phase extends it.
6. Security headers middleware (CSP `default-src 'self'`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Permissions-Policy`), CORS allowlist = web origin only.
7. Frontend: `/login` + `/register` pages (match existing design tokens), `api.ts` fetch wrapper (`credentials: 'include'`, on 401 → try refresh once → else redirect login), route guards: visualizers/problems readable by guests; dashboard/quiz-submit/judge require auth. Guest progress stays local until login.
8. `DELETE /auth/account` (hard-delete user + cascade all user tables) and `GET /auth/export` (JSON dump of everything the user owns) — privacy rights, implemented now not later.

**Phase gate:** `pytest -q` green incl. authz matrix; Playwright: register → login → logout → login; two browsers can't see each other's seeded progress; CI adds `api-test` job.

---

### PHASE 3 — Progress migration & sync

**Tasks**
1. Alembic migration: all user-data tables from §3.
2. Routers implementing the `progress` endpoints (upsert semantics; `status ∈ Todo|Doing|Done`; activity day increment on any write, using the **client-supplied local date** validated as `YYYY-MM-DD ± 1 day` — fixes D8 server-side too).
3. `GET /progress/summary`: solved/in-progress counts, per-topic rollup, streak (computed from `activity_days`, local dates), heatmap series, weakest quiz topics, resume pointer. Frontend Dashboard switches to it.
4. Frontend: replace `ProgressContext`'s localStorage persistence with API-backed store when authenticated (keep localStorage for guests; zod-validated). Debounced writes for notes; optimistic status toggles.
5. `POST /progress/import-local`: on first login, if local store has data, send it once; server merges max-wins (`Done` > `Doing` > `Todo`; streak days unioned; quiz max score), marks import done on the user row, frontend clears local keys. Test both directions and the idempotency (second import is a no-op).
6. Extend authz matrix + Playwright two-user isolation e2e for every new endpoint.

**Phase gate:** full stack runs locally (`uvicorn` + `vite` with proxy); e2e golden path: register → solve-status toggle → reload on another browser profile → same state; guest → login → local progress merged.

---

### PHASE 4 — Judge (replaces the browser runner)

**Tasks**
1. Remove the Phase-1 worker runner. `judge/` service in `apps/api` that shells to a **self-hosted Piston** container (`docker run -d --name piston -p 2000:2000 ghcr.io/engineer-man/piston`; install packages: javascript, python, c++, java). Piston provides the process sandbox + time/memory limits. Document that Piston must run with no network access from job containers and on an isolated docker network.
2. `POST /judge/run`: body `{problem_slug, language, code}`; server loads the problem's sample test cases, executes via Piston, compares with **exact JSON equality** (same semantics as today's runner), returns per-case pass/fail + runtime. Enforce: 60s wall timeout, per-user rate limit (e.g., 30 runs/min), code ≤ 64 KB, no stdin.
3. `POST /judge/submit`: runs **all** test cases (including hidden), writes a `submissions` row, returns verdict; on `AC` sets `problem_progress.status='Done'` (max-wins, never downgrades).
4. Frontend `CodeRunner` rework: language selector (JavaScript/Python/C++/Java), starter code from `problems.starter_code[language]`, "Run samples" and "Submit" buttons, verdict display, submission history list per problem.
5. Tests: API tests with a mocked Piston client (deterministic verdicts: AC, WA, TLE, RE, CE); integration test against real Piston in CI service container for one problem per language; authz: submissions are per-user.

**Phase gate:** e2e: submit a correct JS + Python solution to Two Sum → status becomes Done on dashboard; wrong solution → WA shown, status unchanged; `new Function` and the worker file are gone from the repo (grep CI check).

---

### PHASE 5 — Content pipeline & the 5,000-question bank (accuracy core)

**Directory contract:** `content/problems/<slug>.yaml`, `content/questions/<topic>/<id>.yaml`, `content/generators/*.py`, `content/paths/*.yaml`. YAML schema enforced by pydantic models in `content/validators/schema.py`.

**Tasks**
1. **Schema + seed.** Port the existing 30 problems and 50 questions from `apps/web/src/data/*.ts` into content files (statements are already original). Loader script: content files → DB with `review_status='draft'`.
2. **Problem verifier** (`content/validators/verify_problems.py`): for every problem, for every reference solution, run it through the real judge against all test cases — must be 100% AC. Additionally recompute `expected_json` from the reference solution and fail if the file's stored expectation differs (kills hand-typed false data). Also validate: ≥3 test cases incl. one edge case, hints ≥ 2, both brute-force and optimal solutions present, constraints present.
3. **Question verifier** (`content/validators/verify_questions.py`): schema valid; `correct_index` in range; options unique; explanation non-empty; for generator-produced questions, recompute the answer from the generator's own oracle and require equality; duplicate detection via normalized-text `content_hash` + near-dup check.
4. **Generators** (`content/generators/`): templated families with programmatic oracles — e.g., "time complexity of this nested-loop snippet" (oracle = loop-depth analysis), "output of this traversal on tree T" (oracle = actual traversal), "which data structure satisfies these operation complexities", "result of this stack/queue op sequence", "Kadane/prefix-sum trace value at step k". Each generator emits questions + the computed correct answer + explanation template. Target mix per topic so the sampler (Phase 6) has depth in every cell of the topic×difficulty matrix.
5. **Review workflow:** loader sets `review_status='verified'` **only if** all validators pass; curated items additionally require one human approve action via the admin queue (Phase 9) before publishing; generator items need oracle verification + spot-check sampling (5% human review). `GET /problems|questions` endpoints filter to `verified` only.
6. **Corpus growth plan (placement-grade):** topic matrix = arrays, strings, linked lists, stacks/queues, trees, BST, heaps, tries, graphs, DP, greedy, bit manipulation, recursion/backtracking, sorting/searching, complexity theory, DBMS/OS/CS-fundamentals-lite (common in placement MCQs). Staged targets: **750 verified (MVP) → 2,500 → 5,000**; track per-cell counts with `content/validators/coverage_report.py` (CI prints the matrix).
7. Problems corpus: grow 30 → ~300 original problems across the matrix with a published difficulty curve (60% easy/med emphasis for placements); each passes the problem verifier before `verified`.

**Phase gate:** `python content/validators/run_all.py` green; coverage report shows staged target met; API serves only verified content; CI `content-validate` job blocks merges on validator failure.

---

### PHASE 6 — Dynamic quiz engine

**Tasks**
1. Sampler service (`apps/api/app/services/sampler.py`):
   ```python
   def sample_questions(db, user_id, topics, count, difficulty=None):
       # verified only; weighted by difficulty (default 40% easy/40% med/20% hard)
       # exclude questions in user_question_exposure shown in the last 50 exposures
       # if pool < count after exclusion, relax oldest exposures first (never silently repeat recent)
   ```
   On serve: insert exposures + return the attempt shell with a server-side snapshot of `question_ids` (enables retry-wrong and attempt review without trusting the client).
2. Endpoints: `POST /quizzes/generate` → `{attempt_id, questions:[{id, prompt, options}]}` (no `correct_index` in payload — ever). `POST /quizzes/attempts/{id}` with `{selected: {question_id: index}}` → server grades against stored snapshot, writes `quiz_attempts` + `quiz_attempt_answers`, returns score + per-question explanations. `POST /quizzes/attempts/{id}/retry-wrong` → new attempt over the wrong subset (server-side, from snapshot).
3. Frontend `QuizPage` → fetches generated quiz; timer stays client-side (cosmetic), submission is authoritative server-side; results screen shows explanations + per-topic accuracy delta.
4. Analytics: `GET /progress/summary` gains per-topic accuracy from `quiz_attempt_answers` join `questions`.

**Phase gate:** API tests: verified-only sampling, no-repeat window behavior, grading correctness, retry-wrong subset; e2e: take a 10-question mixed quiz twice → no overlap in recent window; wrong-only retry contains exactly the missed questions.

---

### PHASE 7 — Learning paths v2 (foundational + specialised + placement)

**Tasks**
1. Alembic: `learning_paths`, `path_steps`, `path_step_progress`. Seed: 4 existing paths (become `track='foundational'`/`specialised'`) + new specialised tracks (per-topic deep dives) + **placement track** (timed sets + company-pattern sheets, e.g., "service-company aptitude+DSA", "product-company DSA", built from the verified corpus).
2. Path completion rules server-side: problem step done ⇔ `problem_progress.status='Done'`; quiz step done ⇔ best attempt ≥ 70%; visualizer step done ⇔ `visualizer_completions` row; mock step done ⇔ attempt exists. `GET /paths/{slug}` returns resolved steps with per-user status + next-step pointer.
3. Frontend path pages → API; keep existing lock-step UI; fix D4 by construction (server rule, not `lastVisited`). Problems remain individually accessible from `/problems/:topic` and also surface their path memberships on the detail page ("part of: Foundations, Placement DSA").
4. `POST /progress/visualizers/{id}/visit` wired into `VisualizerDetailPage` mount (idempotent upsert).

**Phase gate:** e2e: complete a problem via judge submit → path step flips to done on reload; visualizer visit persists across sessions; next-step CTA always points at the first incomplete step.

---

### PHASE 8 — Placement features

**Tasks**
1. **Mock tests:** `mock_tests` content (spec: topics, count, duration) + timed attempt flow reusing the quiz sampler + a hard server-side `expires_at`; auto-submit on expiry. Frontend timed UI with sticky countdown.
2. **Weak-area detection:** rolling per-topic accuracy over last 5 attempts + submission WA rate → "weakest topics" panel (already stubbed in Dashboard UI; now real).
3. **Revision queue:** wrong quiz answers and WA submissions enter a per-user spaced-repetition queue (intervals 1d/3d/7d); dashboard "Due today" card; completing due items bumps streak.
4. **Streaks:** server-computed from `activity_days` (any write action counts), surfaced in navbar; keep the existing heatmap component, fed by `/progress/summary`.

**Phase gate:** e2e mock test start → expiry auto-submits; revision item appears next day after a wrong answer (clock-mocked); streak increments once per local day regardless of action count.

---

### PHASE 9 — Admin (minimal)

**Tasks**
1. `role='admin'` users (seeded via env-provided bootstrap admin, not the register endpoint).
2. Admin UI at `/admin` (separate guard): content review queue (diff view, approve/reject/edit → `question_reviews` row), coverage matrix from Phase 5, aggregate stats (users count, attempts/day, AC rate).
3. **Privacy rule baked in:** no per-user notes/submissions/progress browsing in admin. Any endpoint that touches an individual user's data requires an explicit reason string and writes `admin_audit_log`. Authz tests assert admin endpoints reject students.

**Phase gate:** admin can move a question draft→verified only through review action; audit log rows exist; student token → 403 on all `/admin/*`.

---

### PHASE 10 — Hardening & launch

**Tasks**
1. Privacy pass: verify export/delete completeness (cascades), set SQLite file perms `0600`, nightly encrypted backup job (restic/gpg to external dir), data-retention note in README, session table cleanup job for expired refresh tokens.
2. Postgres readiness: CI matrix job running `api-test` against `postgresql:16` service; document `DATABASE_URL` switch. No app code changes should be needed — if any are, that's a bug in the SQLAlchemy layer.
3. Performance: verify indexes from §3 with `EXPLAIN QUERY PLAN` on hot queries (sampler, summary); paginate list endpoints (cursor, default 50); web bundle split (visualizers lazy-loaded per route).
4. Accessibility + responsive pass (keyboard through visualizer controls, focus states, mobile tab bar).
5. Deploy docs: single-node compose (web static + api + piston), SPA fallback (D12), env var list, backup restore drill.

**Phase gate (release candidate):** full CI matrix green; `docs/launch-checklist.md` every box ticked with evidence links (test run, coverage report, authz matrix output, backup restore log).

---

## 6. Verification System (the "verified and reverified" MUST)

| Layer | Tool | Gate |
|---|---|---|
| Web unit/component | Vitest + Testing Library | runs in CI; visualizer generators property-tested |
| Web e2e | Playwright | golden paths per phase gate; two-user isolation suite mandatory |
| API | pytest + httpx | ≥90% diff coverage on changed files; authz matrix must grow with every user-data endpoint |
| Content | `content/validators/run_all.py` | blocks merge; nothing serves below `verified` |
| Security | authz matrix + manual checklist per phase | cookies flags asserted in tests; no tokens in localStorage (grep CI) |
| Smoke | after any phase: `npm run build`, `pytest -q`, validator, e2e suite | recorded in the phase PR |

---

## 7. Execution Order & Parallelization

- **Sequential spine:** 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10.
- **Safe parallel lanes:** Phase 1 (web cleanup) can run parallel with Phase 2 tasks 1–5 (api skeleton+auth) by two agents; content schema design (5.1) can start once Phase 2 lands its DB conventions; Phase 9 needs Phase 5's review statuses.
- Do not start Phase 5 corpus growth before the judge (Phase 4) exists — the problem verifier depends on it.

## 8. Risks / Open Questions

1. **5,000 verified questions is the long pole.** Generators carry scale; curated depth needs human review. If review bandwidth is limited, ship at 750 and grow — the platform works at any corpus size.
2. **Piston ops burden.** It's a second stateful service; if deployment simplicity wins later, swap to a per-language subprocess sandbox (nsjail) behind the same judge interface.
3. **Classic problem titles are fine; statements must stay original.** Assign one reviewer to licensing spot-checks in the content workflow.
4. **Guest → account merge conflicts** are handled max-wins; if finer merging is wanted later, that's a product decision, not this plan.
5. **Admin dashboard scope creep** — keep Phase 9 minimal; analytics dashboards beyond that are post-launch.
