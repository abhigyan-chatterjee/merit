# ALGOVISTA — Interactive Data Structures & Algorithms Practice Platform

ALGOVISTA is a placement-grade, full-stack Data Structures & Algorithms visual practice platform built with a high-performance **React 19 + TypeScript + Tailwind 4** frontend (`apps/web`), a **FastAPI + SQLAlchemy 2.0 + Alembic** backend (`apps/api`) with **SQLite WAL / PostgreSQL** persistence, and a **self-hosted Piston judge** for sandboxed multi-language code execution.

---

## ✨ Features & Architecture

1. **12 Dedicated Interactive Visualizers (`/visualizers/:id`)**:
   - **Sorting**: Bubble, Selection, Insertion, Merge, Quick sort with step-by-step frame recording, comparison/swap counters, array size and speed controls.
   - **Graph Explorer**: BFS and DFS exploration with click-to-add nodes in scaled SVG coordinates (`viewBox 0 0 420 350`) and queue/stack state.
   - **Binary Tree / BST / Heap**: Real node-based BST maintaining BST invariants, binary heap with animated sift-up/sift-down and min/max toggle.
   - **Linear & Hashing Data Structures**: Static/Dynamic Array (two-pointer scans), Singly Linked List, LIFO Stack, FIFO Circular Queue, Separate Chaining HashMap with bucket collision resolution, Searching (Binary vs Linear stepper), and Recursion Tree (branching call stack frames & memoization).

2. **Sandboxed Code Judge (`/problems/:topic/:slug`)**:
   - Replaces in-browser `new Function()` with a sandboxed **Piston** code judge execution service.
   - Multi-language support: JavaScript, Python, C++, and Java.
   - Sample test execution (`POST /api/v1/judge/run`) and comprehensive submission judging (`POST /api/v1/judge/submit`) with verdicts (AC, WA, TLE, RE, CE).
   - Rate-limited, 64KB size bounded, and strict 60s wall clock timeouts.
   - **42 verified coding problems** across 18 categories (arrays-hashing 7, trees 7, graphs 6, dynamic-programming 6, linked-lists 5, two-pointers 4, stack 2, math-matrices 2, sliding-windows/trie/intervals 1 each), each sequenced with prev/next links and JS+Python starters, seeded from `content/problems/` and mirrored to the guest-mode static bundle via `content/generators/sync_problems_ts.py`.

3. **Placement-Grade Verified Question Bank (885 Items)**:
   - Automated mathematical and algorithmic oracles in `content/generators/` generating questions across all core domains.
   - Zero hand-typed expectations: all test case expected outputs are computed and verified by running reference solutions in the sandboxed judge.
   - Coverage across 14 banks: arrays-hashing, binary-search, bit-manipulation, data-structures, dynamic-programming, graphs, heap, linked-lists, sliding-windows, sorting, stack, trees, plus aptitude (quant/logic) and core-cs (OS, DBMS, networks, design).

4. **Adaptive Quiz & Timed Mock Exam Engine (`/quiz/:topic`)**:
   - Compact topic dropdown defaulting to Mixed; topic change reloads questions (no silent fallback to unrelated topics).
   - Server-side question sampling (`POST /api/v1/quizzes/generate`) with a 50-exposure no-repeat window and 40% Easy / 40% Med / 20% Hard difficulty balancing.
   - **Zero Answer Leakage**: Client receives only prompts and options; `correct_index` and `explanation` are sealed until post-submission server grading.
   - **Retry Wrong-Only**: Server creates snapshots to retry only missed questions without client manipulation.
   - **Quiz timing**: 20s hard auto-advance per MCQ; exams use their own countdown instead.
   - **Exams are 20 MCQs + 2 coding**: 7 types (Foundational, Intermediate, Sorting+Searching, DP+Greedy, Trees+Graphs, Aptitude, 3-hour Full Placement Mock) with judge-graded coding sections.

5. **Learning Paths v2 (`/learn`, `/learn/:id`)**:
   - 3 structured tracks: Foundation (beginners, summaries + further reading per topic), Targeted (lean high-ROI placement sequence), Mastery (everything verified).
   - Server-resolved step completion: problems done via Judge AC, quizzes passed at >= 70%, visualizers tracked via visit logs.

6. **Spaced Repetition & Weak-Area Detection**:
   - Rolling per-topic accuracy tracking over recent quiz attempts and submission WA rates.
   - Spaced repetition revision queue (1d / 3d / 7d intervals) surfaced on the user's dashboard.

7. **Multi-User Security & Privacy**:
   - Argon2id password hashing + rotating JWT refresh tokens in `HttpOnly; SameSite=Lax; Secure` cookies.
   - Server-side user data isolation: all queries filter strictly on `Table.user_id == current_user.id`.
   - Compact account menu (profile, email, password, preferred JS/Python language, logout) at `/profile`.
   - Permanent daily goals and language preference persist server-side (`PUT /api/v1/progress/settings`).
   - GDPR/CCPA compliance: `GET /api/v1/auth/export` produces a full data dump; `DELETE /api/v1/auth/account` cascades and purges all records.

8. **Admin Control Console (`/admin`)**:
   - Role-based authorization (`role='admin'`); students receive HTTP 403 Forbidden.
   - Content review queue for drafts, topic x difficulty coverage matrix, aggregate metrics, and audit trail (`admin_audit_log`).

---

## 🗂 Repository Layout

```
algovista/
├── apps/
│   ├── web/                     # React 19 + Vite + TypeScript frontend
│   │   ├── src/
│   │   │   ├── components/      # UI components, QuizEngine, CodeRunner, Navbar
│   │   │   ├── visualizers/     # 12 dedicated visualizer engines
│   │   │   ├── pages/           # Dashboard, Visualizers, Problems, Quizzes, Paths, Admin
│   │   │   ├── store/           # AuthContext, ProgressContext (API + local fallback)
│   │   │   └── utils/           # api.ts client SDK
│   │   ├── tests/               # Vitest component & unit tests
│   │   └── nginx.conf           # SPA fallback & API reverse proxy configuration
│   └── api/                     # FastAPI + SQLAlchemy 2.0 backend
│       ├── app/
│       │   ├── models/          # User, Problem, Question, QuizAttempt, Submission
│       │   ├── schemas/         # Pydantic request/response schemas
│       │   ├── routers/         # auth, progress, judge, content, quizzes, admin
│       │   ├── services/        # judge, sampler, streak, session_cleanup
│       │   ├── security.py      # Argon2id, JWT cookies, get_current_user
│       │   └── seed.py          # Database seeder
│       ├── alembic/             # Database migrations
│       └── tests/               # Pytest test suite, authz isolation matrix
├── content/
│   ├── problems/                # 42 verified problem specs with reference solutions
│   ├── questions/               # Curated question items
│   ├── paths/                   # Learning path definitions
│   ├── catalog/                 # Canonical DSA catalog built from scraped CSVs (metadata only)
│   ├── generators/              # build_catalog, sync_problems_ts + programmatic question generators with oracles
│   └── validators/              # verify_problems, verify_questions, coverage_report
├── docs/
│   ├── launch-checklist.md      # Launch readiness audit & verification gates
│   └── backup_drill.sh          # WAL checkpoint & encrypted backup drill
├── docker-compose.yml           # Single-node deployment: Piston + API + Web
└── .github/workflows/ci.yml     # GitHub Actions CI matrix (SQLite + PostgreSQL)
```

---

## 🚀 Running Locally

### 1. Prerequisites
- Node.js >= 20
- Python >= 3.12 (with `uv` or standard venv)
- Docker (optional, for Piston judge)

### 2. Frontend (`apps/web`)
```bash
cd apps/web
npm install
npm run dev
```
Runs at `http://localhost:5173`.

### 3. Backend (`apps/api`)
```bash
cd apps/api
uv venv && uv pip install -e ".[dev]"
# Or: python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"

# Apply migrations and seed verified content
alembic upgrade head
python3 -m app.seed

# Run API server
uvicorn app.main:app --reload --port 8000
```
API runs at `http://localhost:8000` with Swagger docs at `http://localhost:8000/api/docs`.

### 4. Sandboxed Judge (Piston)
```bash
docker run -d --name piston -p 2000:2000 ghcr.io/engineer-man/piston:latest
```

---

## 🐳 Production Deployment with Docker Compose

A complete turn-key stack (Web Nginx + FastAPI + Piston Judge) can be started with a single command:

```bash
docker compose up -d
```

- **Frontend with SPA Fallback**: Port `80`
- **FastAPI API**: Port `8000` (proxied under `/api/`)
- **Piston Sandbox**: Port `2000` (internal network)

---

## 📚 DSA Catalog & Content Pipeline

Scraped title/company/topic metadata lives outside the repo at `/mnt/code/dsa_database/final/`
and is canonicalized (never imported verbatim) into `content/catalog/`:

```bash
# 1. Rebuild canonical catalog (3,997 entries from 4,418 scraped rows)
python3 content/generators/build_catalog.py

# 2. Verify all problems through the real judge + questions + coverage
python3 content/validators/run_all.py

# 3. Re-sync guest-mode static bundle after adding/editing problems
python3 content/generators/sync_problems_ts.py
```

Rules: scraped rows supply titles, company frequency, topics and difficulty only.
Statements, hints, starter code, test cases and solutions are always authored fresh
(original content only) and every reference solution must reach AC in the judge
before the problem ships. `content/catalog/BUILD_REPORT.txt` lists the top
company-weighted candidates for the next authoring batch.

---

## 🔒 Data Privacy & Retention Policy

1. **Guest Mode**: All visualizers and problem reading are accessible without an account. Unauthenticated progress is stored locally in the browser's `localStorage` and validated against a strict Zod schema (`algovista_store_v1`).
2. **Account Sync & Merge**: Upon first registration or login, local progress is imported and merged using a **max-wins** strategy (Done > Doing > Todo; union of active streak days).
3. **Multi-User Isolation**: User IDs are never trusted from client inputs. All database operations filter strictly by the authenticated JWT session cookie.
4. **Account Purge & Export**: Users retain full control over their data via `GET /api/v1/auth/export` and `DELETE /api/v1/auth/account`.
5. **Session Cleanup**: Expired refresh tokens and revoked sessions are automatically pruned.
