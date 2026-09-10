# ALGOVISTA — Interactive Data Structures & Algorithms Practice Platform

ALGOVISTA is a placement-grade, full-stack Data Structures & Algorithms visual practice platform built with a **React 19 + TypeScript + Tailwind 4** frontend (`apps/web`) and a **FastAPI + SQLAlchemy 2.0 + Alembic** backend (`apps/api`) with **SQLite / PostgreSQL** persistence and sandboxed code execution.

**Author**: [Abhigyan Chatterjee](https://nullbit.in) — GitHub: [https://github.com/abhigyan-chatterjee](https://github.com/abhigyan-chatterjee)

---

## Features & Architecture

1. **12 Dedicated Interactive Visualizers (`/visualizers/:id`)**:
   - **Sorting**: Bubble, Selection, Insertion, Merge, Quick sort with step-by-step frame recording, comparison/swap counters, and array size / animation speed controls.
   - **Graph Explorer**: BFS and DFS exploration with click-to-add nodes in scaled SVG coordinates (`viewBox 0 0 420 350`) and queue/stack state tracking.
   - **Binary Tree / BST / Heap**: Node-based BST maintaining binary search tree invariants; binary heap with animated sift-up/sift-down and min/max heap toggle.
   - **Linear & Hashing Data Structures**: Static/Dynamic Array (two-pointer scans), Singly Linked List, LIFO Stack, FIFO Circular Queue, Separate Chaining HashMap with bucket collision resolution, Searching (Binary vs Linear stepper), and Recursion Tree (branching call stack frames & memoization).

2. **Sandboxed Code Judge (`/problems/:topic/:slug`)**:
   - Subprocess-isolated sandbox executing JavaScript (`node`) and Python (`python3`) against test suites in temporary directories.
   - Sample test execution (`POST /api/v1/judge/run`) and submission judging (`POST /api/v1/judge/submit`) returning standard verdicts (`AC`, `WA`, `TLE`, `RE`, `CE`).
   - Rate-limited, 64 KB code size limit, and per-problem execution timeouts.
   - **42 verified coding problems** across 18 canonical categories (arrays-hashing 7, trees 7, graphs 6, dynamic-programming 6, linked-lists 5, two-pointers 4, stack 2, math-matrices 2, sliding-windows 1, trie 1, intervals 1), each sequenced with prev/next navigation links and JavaScript + Python starter code. (200 draft problems remain staged in `content/problems/` awaiting verification).

3. **Verified Question Bank & Coverage**:
   - Programmatic generators and algorithmic oracles in `content/generators/` producing question items with verified schemas, unique hashes, and correct answer options.
   - `python3 content/validators/run_all.py` verifies **42 problems** (100% AC against reference solutions) and **539 questions** across all topic directories.
   - Placement corpus coverage matrix reports **341 verified questions** across 20 banks (101 Easy, 167 Medium, 73 Hard): aptitude (27), arrays-hashing (36), backtracking (12), binary-search (12), bit-manipulation (12), core-cs (20), data-structures (20), dynamic-programming (26), graphs (18), greedy (12), heap (12), intervals (12), linked-lists (12), math-matrices (12), sliding-windows (12), sorting (24), stack (12), trees (26), trie (12), two-pointers (12).

4. **Adaptive Quiz & Timed Mock Exam Engine (`/quiz/:topic`, `/exams`)**:
   - Compact topic selector defaulting to Mixed; switching topics triggers fresh question loading.
   - Server-side question sampling (`POST /api/v1/quizzes/generate`) with a 50-exposure no-repeat window and 40% Easy / 40% Medium / 20% Hard difficulty balancing.
   - Zero client answer leakage: client receives only prompts and options; `correct_index` and `explanation` remain sealed until post-submission server grading.
   - Retry wrong-only: server creates question snapshots enabling users to retry missed questions without client state tampering.
   - Timed exams: 7 targeted exam presets (Foundational DSA, Intermediate DSA, Sorting & Searching, DP & Greedy, Trees & Graphs, Aptitude, and Full Placement Mock) with countdown timers, MCQ sections, and judge-evaluated coding sections.

5. **Learning Paths (`/learn`, `/learn/:id`)**:
   - 3 structured tracks: Foundation (beginner data structures with visualizers, summaries, and further reading), Targeted (curated placement sequence), and Mastery (comprehensive curriculum).
   - Step completion tracking: problems completed via Judge AC, quizzes passed at >= 70%, and visualizers tracked through visit logs.

6. **Spaced Repetition & Weak-Area Detection**:
   - Rolling per-topic accuracy tracking across quiz attempts and problem submissions.
   - Spaced repetition revision queue (1-day, 3-day, and 7-day intervals) surfaced on the user dashboard.

7. **Multi-User Security & Privacy**:
   - Argon2id password hashing and rotating JWT tokens in `HttpOnly; SameSite=Lax; Secure` cookies.
   - Server-enforced data isolation: all user queries filter strictly by authenticated `user_id`.
   - User account export via `GET /api/v1/auth/export` and cascading account deletion via `DELETE /api/v1/auth/account`.
   - User preferences: preferred language (JavaScript / Python) and daily goal configurations persisted via `PUT /api/v1/progress/settings`.
   - Automated session cleanup for expired refresh tokens and revoked sessions.

8. **Admin Console (`/admin`)**:
   - Role-based access control (`role == "admin"`); unprivileged requests receive HTTP 403 Forbidden.
   - Draft content review queue for problems and questions, topic-by-difficulty coverage matrix, aggregate platform metrics, and admin audit logging (`admin_audit_log`).

---

## Repository Layout

```
algovista/
├── apps/
│   ├── web/                     # React 19 + Vite + TypeScript frontend
│   │   ├── src/
│   │   │   ├── components/      # UI components, QuizEngine, CodeRunner, Navbar
│   │   │   ├── visualizers/     # 12 dedicated interactive visualizer engines
│   │   │   ├── pages/           # Dashboard, Visualizers, Problems, Quizzes, Exams, Paths, Admin
│   │   │   ├── store/           # AuthContext, ProgressContext (API + local fallback)
│   │   │   └── utils/           # api.ts client SDK
│   │   └── tests/               # Vitest component & unit tests
│   └── api/                     # FastAPI + SQLAlchemy 2.0 backend
│       ├── app/
│       │   ├── models/          # User, Problem, Question, QuizAttempt, Submission
│       │   ├── schemas/         # Pydantic request/response schemas
│       │   ├── routers/         # auth, progress, judge, content, quizzes, admin
│       │   ├── services/        # judge, sampler, streak, session_cleanup
│       │   ├── security.py      # Argon2id, JWT cookies, get_current_user
│       │   ├── config.py        # Environment settings & SECRET_KEY enforcement
│       │   └── seed.py          # Database seeder
│       ├── alembic/             # Database migrations
│       └── tests/               # Pytest test suite and authz isolation matrix
├── content/
│   ├── problems/                # 42 verified problem specs with reference solutions (+ 200 drafts)
│   ├── questions/               # 1,083 question items across 16 topic directories
│   ├── paths/                   # Learning path definitions (Foundation, Targeted, Mastery)
│   ├── catalog/                 # Canonical DSA catalog (3,997 entries) with companies & topic map
│   ├── generators/              # build_catalog, sync_problems_ts, question generators
│   └── validators/              # verify_problems, verify_questions, coverage_report, run_all
└── docs/
    ├── launch-checklist.md      # Launch readiness audit & verification gates
    └── backup_drill.sh          # WAL checkpoint & encrypted backup drill
```

---

## Running Locally

### Prerequisites
- Node.js >= 20
- Python >= 3.12 (with `uv` or standard virtual environment)

### Frontend (`apps/web`)
```bash
cd apps/web
npm install
npm run dev
```
Development server runs at `http://localhost:5173`.

### Backend (`apps/api`)
```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Configure environment variables
cp .env.example .env
# Set a secure SECRET_KEY in .env:
# python3 -c "import secrets; print(secrets.token_urlsafe(48))"

# Apply migrations and seed verified content
alembic upgrade head
python3 -m app.seed

# Run API server
uvicorn app.main:app --reload --port 8000
```
API runs at `http://localhost:8000` with OpenAPI documentation at `http://localhost:8000/api/docs`.

---

## DSA Catalog & Content Pipeline

The canonical DSA catalog (`content/catalog/catalog.json`) contains **3,997 canonical problem entries** deduplicated and normalized from 4,418 scraped dataset rows:

- **Catalog Fields**: Each catalog entry includes `title`, `slug`, `difficulty` (Easy, Medium, Hard, Unknown), normalized `companies` frequency list, `pattern`, a primary `algo_topic` (mapped to one of 18 canonical categories), and a multi-label **`algo_topics`** array capturing all relevant categories for cross-domain problems.
- **Content Pipeline Rules**: Scraped datasets supply only titles, companies, topic tags, and difficulty metadata. Statements, hints, starter code, test suites, and solutions are authored entirely as original content. Every reference solution must achieve `AC` (Accepted) through the judge validator before shipping.

```bash
# Rebuild canonical catalog
python3 content/generators/build_catalog.py

# Run full verification suite (problem judge execution + question integrity + coverage)
python3 content/validators/run_all.py

# Synchronize verified problems into web static bundle
python3 content/generators/sync_problems_ts.py
```

---

## Data Privacy & Retention Policy

1. **Guest Mode**: All visualizers and problem reading are accessible without an account. Unauthenticated progress is stored locally in the browser's `localStorage` and validated against a strict Zod schema (`algovista_store_v1`).
2. **Account Sync & Merge**: Upon first registration or login, local progress is imported and merged using a **max-wins** strategy (`Done` > `Doing` > `Todo`; union of active streak days).
3. **Multi-User Isolation**: User IDs are never trusted from client inputs. All database operations filter strictly by the authenticated JWT session cookie (`Table.user_id == current_user.id`).
4. **Account Purge & Export**: Users retain full control over their data via `GET /api/v1/auth/export` (full JSON archive) and `DELETE /api/v1/auth/account` (complete cascading purge).
5. **Session Pruning**: Expired refresh tokens and revoked sessions are automatically cleaned up.
