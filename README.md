# Merit — Make the merit list

Merit is a placement-grade DSA practice platform for Indian campus
recruitment: 12 interactive algorithm visualizers, 140 verified coding
problems with a sandboxed judge (Python + JavaScript), adaptive quizzes and
timed mock exams, 3 guided learning paths, and spaced revision with
weak-area tracking. Multi-user accounts with Argon2id + JWT cookies;
optional Google/GitHub sign-in via Clerk.

By [Abhigyan Chatterjee](https://nullbit.in) — GitHub:
<https://github.com/abhigyan-chatterjee>

---

## 60-second quickstart

Prereqs: Node.js ≥ 20, Python ≥ 3.12.

```bash
# Backend (http://localhost:8000, docs at /api/docs)
cd apps/api
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # then set a real SECRET_KEY in .env
.venv/bin/alembic upgrade head
.venv/bin/python -m app.seed
.venv/bin/uvicorn app.main:app --reload --port 8000

# Frontend (http://localhost:5173) — in a second terminal
cd apps/web
npm install
npm run dev
```

Verify everything is green (run from repo root):

```bash
cd apps/api && .venv/bin/python -m pytest -q --no-header   # 81 passed
cd ../web && npx vitest run                                # 102 passed, 19 files
cd ../.. && python3 content/validators/run_all.py          # 140 problems 100% AC, 539 questions, 136 designs
```

## Where things live

- `apps/web/` — React 19 + Vite + TypeScript + Tailwind 4 frontend.
  Visualizers, `CodeRunner`, `QuizEngine`, BYOK AI tutor panel, Clerk
  sign-in components (active only when `VITE_CLERK_PUBLISHABLE_KEY` is set),
  privacy/terms pages, exam sidebar navigator.
- `apps/api/` — FastAPI + SQLAlchemy 2.0 backend. Routers for auth,
  content, judge, progress, quizzes, admin, tutor; SQLite locally
  (`apps/api/merit.db`), Postgres in prod. Alembic migrations + seeder.
- `content/` — the source of truth: 140 verified problems (+ 200
  quarantined `scrap-*.json` drafts that are never served), 539 question
  items, `foundation` / `targeted` / `mastery` learning paths, the
  deduplicated catalog, and the QAF/PAF authoring frameworks with the
  `run_all.py` verification gate.
- `docs/` — runbooks: `prod.md` (Clerk + production handoff),
  `launch-checklist.md` (hardening/launch verification), `backup_drill.sh`.
- `design ideas/` — your private reference screenshots (untracked, never
  committed).

## Deploy

See `docs/prod.md` for the Clerk + production handoff and
`docs/launch-checklist.md` for the launch verification matrix. Prod target
is `merit.nullbit.in`; the API is Neon-Postgres-ready (any `postgresql://`
`DATABASE_URL` passes through untouched).

## Current state

- **140 verified coding problems**, every reference solution executed to
  100% AC through the real judge; 200 scrap drafts quarantined on disk.
- **539-question bank** (341 verified active) with balanced options and
  136 distinct designs; quizzes sampled server-side with no-repeat windows.
- **BYOK AI tutor**: your API key is sent per-request and never stored;
  the server just proxies to your provider.
- **Clerk OAuth** (Google/GitHub) linked to existing accounts by verified
  email; password login untouched; works keyless in dev (returns 501 until
  configured).
- **Neon-ready**: SQLite for local dev, Postgres for prod, migrations
  current (`c4f1a2b3d4e5`).
