# AGENTS.md — Merit Engineering Rules

**Merit — Make the merit list.** Placement-grade DSA prep for Indian campus
recruitment: 12 algorithm visualizers, a sandboxed code judge, adaptive
quizzes + timed exams, guided learning paths, spaced revision.

Read this file fully before touching code. Rules only — no history lessons.

---

## 1. What it is

| Layer | Path | Stack |
|---|---|---|
| Web | `apps/web/` | Vite + React 19 + TypeScript + Tailwind CSS 4, Clerk `<SignIn/>`/`<SignUp/>` (only when `VITE_CLERK_PUBLISHABLE_KEY` is set), BYOK AI tutor panel (`AiTutor.tsx`) |
| API | `apps/api/` | FastAPI + SQLAlchemy 2.0 + Alembic; SQLite dev (`apps/api/merit.db`), Neon Postgres prod (`postgresql://` passes through untouched in `app/config.py`); Argon2id + JWT in `httpOnly` cookies; Clerk link/verify in `app/services/clerk_oauth.py` |
| Content | `content/` | 140 verified problems + 539 question items; QAF question generators, PAF problem framework, catalog classifier |
| Judge | `apps/api/app/services/judge.py` | Subprocess-isolated sandbox, **Python and JavaScript only** |

---

## 2. Hard invariants

1. **Language scope: Python + JavaScript ONLY.** No Java/C++ runners, boilerplate, or schema stubs.
2. **100% AC.** Every coding problem must pass its reference solution through the real judge (`content/validators/verify_problems.py`). No exceptions.
3. **Scrap quarantine.** `content/problems/scrap-*.json` (200 drafts, `reviewStatus: "draft"`) are never seeded or served. `apps/api/app/seed.py` skips draft files and purges stale draft rows; both `reviewStatus` and `review_status` spellings are honored.
4. **User isolation.** Never trust client-provided user IDs. Every user-scoped query filters on `Table.user_id == current_user.id`.
5. **No false passes.** Never weaken assertions, widen thresholds, or mock failures to fake green. Fix root causes.
6. **QAF caps.** MCQ generator keys capped at 4 instances per design; no question ships without passing `verify_questions.py` quality gates.
7. **No secrets in git.** Tokens live in env/local config. `*.db*`, `.env`, caches, `node_modules` are gitignored.

---

## 3. Repo layout (real paths)

```text
AGENTS.md / README.md              # the only two human docs at root
apps/api/app/main.py               # FastAPI app, CORS, lifespan (auto schema init + seed)
apps/api/app/config.py             # settings; SQLite path anchored to apps/api/merit.db
apps/api/app/models/               # user, content, progress, quiz, submission
apps/api/app/routers/              # auth, content, judge, progress, quizzes, admin, tutor
apps/api/app/schemas/              # request/response schemas (incl. auth, tutor)
apps/api/app/services/             # judge, sampler, streak, session_cleanup, clerk_oauth
apps/api/alembic/                  # migrations (head: c4f1a2b3d4e5 Clerk OAuth)
apps/api/tests/                    # pytest suite (test_auth[z], content, judge, quizzes,
                                   # progress, admin, tutor, session_cleanup, config, pg_compat)
apps/web/src/components/           # QuizEngine, CodeRunner, AiTutor, ClerkOAuth, visualizers…
apps/web/src/pages/                # Landing, Dashboard, Problems, Quiz, Exams, Paths, Admin, Privacy, Terms
apps/web/src/data/                 # curriculum, quizzes, problems bundle, paths
apps/web/src/store/                # AuthContext, ProgressContext
apps/web/tests/                    # Vitest suite (19 files)
content/problems/                  # 140 verified + 200 scrap-*.json drafts (quarantined)
content/questions/                 # 539 items across ~20 topic dirs (341 verified active)
content/paths/                     # foundation.json, targeted.json, mastery.json
content/catalog/catalog.json       # canonical deduplicated catalog
content/taxonomy.py                # 18-category taxonomy (single source of truth)
content/generators/qaf/            # Question Authoring Framework
content/generators/paf/            # Problem Authoring Framework
content/generators/build_catalog.py# catalog normalizer + topic classifier
content/validators/run_all.py      # master gate: problems + questions + coverage + path refs
content/validators/verify_problems.py / verify_questions.py / coverage_report.py
docs/prod.md                       # Clerk + prod handoff runbook
docs/launch-checklist.md           # launch/hardening verification checklist
docs/backup_drill.sh               # WAL checkpoint + backup drill
```

Owner-only, untracked, never commit content from: `design ideas/` (owner screenshots).

---

## 4. Canonical gates — exact commands, expected counts

```bash
# API: 81 passed
cd apps/api && .venv/bin/python -m pytest -q --no-header

# Web: 102 passed (19 files)
cd apps/web && npx vitest run

# Content: 140 problems 100% AC (200 drafts skipped) + 539 questions
# (341 verified) + 136 distinct designs (>= 130) + path refs resolve
python3 content/validators/run_all.py
```

Supporting commands:

```bash
cd apps/api && .venv/bin/ruff check app tests        # lint, 0 errors
cd apps/api && .venv/bin/alembic upgrade head        # migrations
cd apps/api && .venv/bin/python -m app.seed          # re-seed verified content
cd apps/api && .venv/bin/uvicorn app.main:app --reload --port 8000
cd apps/web && npm run dev                            # http://localhost:5173
cd apps/web && npm run build
```

Zero tolerance: all three gates green before and after every change.

---

## 5. Branch / commit conventions

- Remote: `https://git.nullbit.in/abhi/Algovista.git` (repo slug still Algovista; rename is product-only until owner renames the forge repo). Work on `scope/extension`.
- Identity (strict):
  `git config user.name "Abhigyan Chatterjee"` /
  `git config user.email "abhi@nullbit.in"`
- `git status` must show only intended files. Never stage secrets, `*.db*`, or owner screenshots.
- **No push** unless the ticket explicitly says so.

---

## 6. Ticket discipline

- Touch only the ticket's target files. Docs tickets = docs only, no code.
- Verify, don't trust: run the gate from §4 that covers your change and report
  raw outputs (counts, failures). Re-read edited regions after every edit.
- Root carries exactly two human docs (`AGENTS.md`, `README.md`). Plan traces
  (`prompt.txt`, root date-stamped `.md`, `.hermes/plans/*.md`) are deleted on
  sight; keep the `.hermes/` dir itself. `design ideas/` and `docs/` are kept.
