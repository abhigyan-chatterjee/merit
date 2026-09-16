# AGENTS.md — Algovista Engineering & Context Manual

> **Mandatory Read for Autonomous Agents (Codex, Antigravity, Claude Code, Hermes):**
> Read this file completely before touching code or executing commands. It defines repository architecture, hard invariants, completed tickets, active branch topology, and canonical test gates.

---

## 1. Project Overview & Vision

**Algovista** is a multi-user, placement-grade Data Structures & Algorithms (DSA) preparation platform tailored for Indian campus recruitment (MAANG, Tier-1 product firms, and mass recruiters).

- **Frontend (`apps/web`)**: Vite + React 19 + TypeScript + Tailwind CSS 4. Monaco editor runner, algorithm visualizers (Trees, Graphs, Sorting, Dynamic Programming), guided paths, and dynamic quiz engine.
- **Backend (`apps/api`)**: FastAPI + SQLAlchemy 2.0 (declarative) + Alembic + SQLite (WAL mode). Argon2id password hashing + JWT in `httpOnly` secure cookies. User isolation on every query.
- **Content Engine (`content/`)**: Original, verified problem statements, test suites, reference solutions, and MCQ question generators. Unverified or scraped drafts are quarantined and never served.

---

## 2. Active Git State & Remote Forge

- **Remote Forge**: `https://git.nullbit.in/abhi/Algovista.git` (Private self-hosted Gitea).
- **Active Feature Branch**: `scope/extension`.
- **Commit Identity (STRICT)**:
  ```bash
  git config user.name "Abhigyan Chatterjee"
  git config user.email "abhi@nullbit.in"
  ```
- **Credentials & Environment**:
  - Forge auth tokens and secrets live in local configuration / environment (`~/.config/algovista/forge.env`).
  - **NEVER** commit secrets, passwords, or tokens to git.
  - SQLite database files (`*.db*`), caches (`.ruff_cache`, `.pytest_cache`, `node_modules`), and `.env` are gitignored.

---

## 3. Hard Architectural Invariants

1. **Language Scope**:
   - **Python and JavaScript ONLY** in the MVP.
   - **Java and C++ are explicitly OUT of scope.** Do not add Java/C++ runners, boilerplate, or schema stubs.
2. **Quality Over Bloat**:
   - No synthetic template inflation.
   - MCQ generator keys are hard-capped at **4 instances per design**.
   - No question ships without passing QAF quality gates (variance, distractor sanity, uniform option distribution).
3. **No Unverified Content**:
   - Every coding problem must achieve **100% AC** (Accepted) against its reference solution in the execution judge (`content/validators/verify_problems.py`).
   - Draft stubs (`content/problems/scrap-*.json`) have `reviewStatus: "draft"` and **must never be seeded or served**.
4. **Strict User Isolation**:
   - Client-provided user IDs are **never trusted**. All user-scoped database queries filter strictly on `Table.user_id == current_user.id`.
5. **No False Passes / Test Cheating**:
   - Never weaken assertions, widen thresholds, or mock out failures to simulate passes. Fix root causes.

---

## 4. Work Completed (Recent Changelog)

| Commit | Scope | Description |
|---|---|---|
| `8987a7a` | Ticket A | Fixed catalog topic classifier in `content/generators/build_catalog.py`: multi-label `algo_topics`, 3-tier specificity priority, and India-weighted candidate ranking. |
| `8392aca` | Ticket C | Cleared plumbing debt: removed hardcoded JWT secret fallback in `config.py`, dynamic date windows in `test_progress.py`, dynamic problem count in `progress.py`, honest README. |
| `421c2f7` | Ticket B | Deduplicated question bank: capped instances at 4, added 28 new distinct designs (+112 questions) in starved categories, raised Hard questions from 34 to 73, updated `coverage_report.py` gate to `distinct_designs >= 130`. |
| `74f5593` | Ticket E | Fixed `seed_problems` in `apps/api/app/seed.py` to inspect `reviewStatus` / `review_status`, skipping and purging 200 `scrap-*` draft files from the live API. |
| `2e665a4` | Ticket F | Introduced **Question Authoring Framework (QAF)** in `content/generators/qaf/`: declarative specs, random parameter oracles, distractor generators, and 6 quality gates in `verify_questions.py`. |
| `32aa70c` | Fix API | Added local development secret auto-fallback in `apps/api/app/config.py` (strict failure retained for production). |
| `e5fc8cc` | Test API | Added unit test coverage in `tests/test_config.py` for secret fallback and production rejection. |
| `5240cc5` | Fix API | Anchored SQLite `DATABASE_URL` path directly to `apps/api/algovista.db` regardless of invocation CWD; added lifespan startup hook in `app/main.py` to auto-initialize schema and seed content. |

---

## 5. Repository Layout

```text
Algovista/
├── AGENTS.md                               # This file
├── README.md                               # Project documentation
├── algovista.db                            # Root artifact (use apps/api/algovista.db)
├── apps/
│   ├── api/                                # FastAPI backend
│   │   ├── alembic/                        # Migration versions (184cc17df8ca -> 9e4a5c28d7f2)
│   │   ├── app/
│   │   │   ├── config.py                   # Pydantic BaseSettings, anchored DB URL, JWT secrets
│   │   │   ├── db.py                       # SQLAlchemy engine & Base
│   │   │   ├── main.py                     # FastAPI application, CORS, security headers, lifespan
│   │   │   ├── models/                     # SQLAlchemy models (user, content, progress, quiz, submission)
│   │   │   ├── routers/                    # API endpoints (auth, content, judge, progress, quizzes, admin)
│   │   │   ├── schemas/                    # Pydantic request/response schemas
│   │   │   ├── seed.py                     # Database seeder (problems, questions, paths, admin)
│   │   │   └── services/                   # Business logic (judge, sampler, session_cleanup, streak)
│   │   ├── tests/                          # 46 pytest unit & integration tests
│   │   └── pyproject.toml                  # API Python package config
│   └── web/                                # React 19 + TypeScript frontend
│       ├── src/
│       │   ├── components/                 # UI components, visualizers, CodeRunner
│       │   ├── data/                       # Static curriculums, paths, pseudocode
│       │   ├── pages/                      # Route pages (Landing, ProblemList, Visualizers, Quizzes)
│       │   └── store/                      # React context & state (ProgressContext)
│       └── tests/                          # 73 Vitest component & route tests
└── content/                                # Problem & Question source of truth
    ├── catalog/catalog.json                # 3,997 canonical deduplicated problems
    ├── generators/
    │   ├── qaf/                            # Question Authoring Framework (spec, oracles, distractors, engine)
    │   │   └── specs/                      # Declarative MCQ design specs
    │   ├── arrays_strings.py               # Topic question generators (QAF-driven)
    │   ├── generate_all.py                 # Master generator runner
    │   └── build_catalog.py                # Catalog normalizer & topic classifier
    ├── paths/                              # Learning path definitions (foundation, targeted, mastery)
    ├── problems/                           # 42 verified problems + 200 draft stubs (scrap-*.json)
    ├── questions/                          # 539 JSON questions across 20 topic directories
    └── validators/                         # Gate verification scripts
        ├── coverage_report.py              # Enforces distinct design thresholds (>= 130)
        ├── run_all.py                      # Master test runner (problems + questions + coverage)
        ├── verify_problems.py              # Executes reference solutions via Judge
        └── verify_questions.py             # Enforces 6 QAF quality gates & option balance
```

---

## 6. Standard Execution & Verification Commands

All agents must run and verify these commands before and after proposing changes:

### Python & API Environment
The virtual environment is located at `apps/api/.venv`.

```bash
# 1. Run all API tests (Must be 46 passed)
cd apps/api && .venv/bin/python -m pytest -q --no-header

# 2. Check API linting (Must be 0 errors)
cd apps/api && .venv/bin/ruff check app/config.py app/main.py tests/test_config.py

# 3. Start API dev server (Port 8000)
cd apps/api && .venv/bin/uvicorn app.main:app --reload --port 8000

# 4. Apply database migrations
cd apps/api && .venv/bin/alembic upgrade head

# 5. Re-seed database content
cd apps/api && .venv/bin/python -m app.seed
```

### Web Frontend Environment

```bash
# 1. Run all Web unit/component tests (Must be 73 passed)
cd apps/web && npx vitest run

# 2. Build web bundle
cd apps/web && npm run build

# 3. Start web dev server
cd apps/web && npm run dev
```

### Content Validation Suite (Zero tolerance for failures)

```bash
# Run the complete content verification suite:
# - Checks 42 problems with 100% AC in judge
# - Checks 539 questions against 6 QAF quality gates
# - Checks distinct designs >= 130
python3 content/validators/run_all.py
```

---

## 7. Current Bank & Pipeline Metrics

- **Verified Coding Problems**: Exactly **42 problems** (100% AC against reference solutions).
- **Draft Problems**: 200 `scrap-*.json` stubs (quarantined on disk; skipped by seed).
- **Verified Questions**: **341 active placement questions** (+ 198 draft items = 539 total).
- **Distinct MCQ Designs**: **136 distinct designs** (86 generator templates + 50 curated items).
- **Option Index Balance**: Bank-wide uniformity: A: 31.7%, B: 24.3%, C: 22.6%, D: 21.4%.
- **Hard Questions**: 73 Hard questions (zero topic categories starved of Hard difficulty).

---

## 8. Next Immediate Focus: Ticket G (PAF)

The next priority task is implementing **Ticket G: Problem Authoring Framework (PAF)**:
- Create `content/generators/paf/` mirroring `content/generators/qaf/`.
- Allow problem authors to write only: function signature, Markdown statement, Brute-Force algorithm, and Optimal algorithm.
- PAF automatically generates random edge & stress test inputs, validates both solutions against each other, profiles execution time, and outputs production-grade problem JSON files with 100% verified test cases.
- Following PAF, align learning paths (`content/paths/foundation.json`, `targeted.json`, `mastery.json`) to the verified problem set.
