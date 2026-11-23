"""Content sync: the fingerprint must be stable, and re-seeding must not undo
moderation.

Both defects were live before these tests:

1. The fingerprint hashed `st_size` and `st_mtime_ns`. `docker build` COPY and
   `git checkout` rewrite mtimes for unchanged files, so a fresh container
   always looked like new content and re-ran the whole seed.
2. The backfill branch set `review_status` from the content file, so that
   re-seed reset a problem an admin had rejected back to "verified" and
   re-published content that had been taken down on purpose.
"""

import json
import os

import pytest
from sqlalchemy import delete, select

from app.models.content import ContentSync, PathStep, Problem, Question
from app.models.quiz import QuizAttempt, QuizAttemptAnswer
from app.models.user import User
from app.seed import (
    content_fingerprint,
    seed_if_changed,
    seed_paths,
    seed_problems,
    seed_questions,
)


@pytest.fixture
def content_tree(tmp_path, monkeypatch):
    """Points the fingerprint at a throwaway content tree."""
    for subfolder in ("problems", "questions", "paths"):
        (tmp_path / subfolder).mkdir(parents=True, exist_ok=True)

    def _resolve(subfolder: str):
        directory = tmp_path / subfolder
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    monkeypatch.setattr("app.seed.resolve_content_dir", _resolve)
    return tmp_path


def test_fingerprint_is_stable_when_only_mtime_changes(content_tree):
    problem = content_tree / "problems" / "two-sum.json"
    problem.write_text('{"slug": "two-sum"}', encoding="utf-8")

    before = content_fingerprint()

    # Bump the mtime without touching the bytes, exactly as a checkout does.
    future = os.stat(problem).st_mtime + 10_000
    os.utime(problem, (future, future))

    assert content_fingerprint() == before


def test_fingerprint_changes_when_bytes_change(content_tree):
    problem = content_tree / "problems" / "two-sum.json"
    problem.write_text('{"slug": "two-sum"}', encoding="utf-8")
    before = content_fingerprint()

    problem.write_text('{"slug": "two-sum", "title": "Two Sum"}', encoding="utf-8")

    assert content_fingerprint() != before


def test_fingerprint_changes_when_companies_change(content_tree):
    problem = content_tree / "problems" / "two-sum.json"
    problem.write_text(
        '{"slug": "two-sum", "companies": ["Google"]}', encoding="utf-8"
    )
    before = content_fingerprint()

    problem.write_text(
        '{"slug": "two-sum", "companies": ["Google", "Amazon"]}',
        encoding="utf-8",
    )

    assert content_fingerprint() != before


def test_fingerprint_distinguishes_identical_bytes_in_different_folders(content_tree):
    """Same content under a different path is a different tree."""
    (content_tree / "problems" / "shared.json").write_text("{}", encoding="utf-8")
    (content_tree / "questions" / "shared.json").write_text("{}", encoding="utf-8")

    problems_only = content_fingerprint()

    (content_tree / "questions" / "shared.json").unlink()

    assert content_fingerprint() != problems_only


def test_reseed_keeps_a_rejected_problem_rejected(db_session):
    """An admin's rejection survives a content sync.

    Drives the real `seed_if_changed` against the seeded test database. The
    re-seed is forced by clearing the recorded fingerprint.
    """
    problem = db_session.scalars(select(Problem).limit(1)).one()
    slug = problem.slug

    problem.review_status = "rejected"
    db_session.execute(delete(ContentSync))
    db_session.commit()

    counts, changed = seed_if_changed(db_session)
    assert changed is True, "clearing the fingerprint must force a re-seed"

    db_session.expire_all()
    refreshed = db_session.get(Problem, slug)
    assert refreshed is not None
    assert refreshed.review_status == "rejected", (
        "re-seeding must not resurrect a problem an admin took down"
    )
    assert counts.get("problems", 0) == 0, "rows already present are not recreated"


def test_second_sync_is_a_no_op(db_session):
    """With a current fingerprint the seed does nothing at all."""
    seed_if_changed(db_session)
    counts, changed = seed_if_changed(db_session)

    assert changed is False
    assert not any(counts.values()), f"expected no work, got {counts}"


def test_one_malformed_file_does_not_abort_the_sync(db_session, content_tree, monkeypatch):
    """A valid-JSON file missing required keys must skip, not abort the sync.

    The per-file guard only wrapped `json.load`, so a file that parsed but lacked
    `pattern` raised KeyError out of seed_problems and aborted the whole run.
    With the fingerprint forcing a sync at boot, one bad file froze every deploy.
    """
    good = {
        "slug": "probe-good",
        "title": "Probe Good",
        "topic": "Arrays",
        "difficulty": "Easy",
        "pattern": "hash-map",
        "statement": "Return the input.",
        "functionName": "solve",
        "reviewStatus": "verified",
        "constraints": [],
        "examples": [],
        "hints": [],
        "testCases": [{"label": "c1", "input": [1], "expected": [1]}],
        "solutions": [
            {
                "title": "ref",
                "language": "python",
                "code": "def solve(a):\n    return a",
                "isReference": True,
            }
        ],
    }
    (content_tree / "problems" / "good.json").write_text(json.dumps(good), encoding="utf-8")

    # Parses fine, but is missing `pattern`, `topic` and friends.
    (content_tree / "problems" / "hollow.json").write_text(
        json.dumps({"slug": "hollow", "title": "Hollow"}), encoding="utf-8"
    )
    # Not JSON at all.
    (content_tree / "problems" / "broken.json").write_text("{nope", encoding="utf-8")

    counts, changed = seed_if_changed(db_session)

    assert changed is True
    assert counts["problems"] == 1, f"the good file must still seed, got {counts}"
    assert db_session.get(Problem, "probe-good") is not None
    assert db_session.get(Problem, "hollow") is None


def test_empty_verified_set_does_not_purge(db_session, content_tree):
    """A directory with only drafts must not wipe existing problems."""
    (content_tree / "problems" / "draft.json").write_text(
        json.dumps({"slug": "drafty", "reviewStatus": "draft"}), encoding="utf-8"
    )
    before = len(db_session.scalars(select(Problem)).all())
    assert before > 0
    assert seed_problems(db_session, content_tree / "problems") == 0
    assert len(db_session.scalars(select(Problem)).all()) == before


def test_fingerprint_ignores_scrap_files(content_tree):
    problem = content_tree / "problems" / "good.json"
    problem.write_text('{"slug": "good"}', encoding="utf-8")
    before = content_fingerprint()
    (content_tree / "problems" / "scrap-x.json").write_text('{"slug": "x"}', encoding="utf-8")
    assert content_fingerprint() == before


def test_seed_paths_preserves_step_ids(db_session):
    from sqlalchemy import select as _select

    steps_before = {
        s.id: (s.step_type, s.ref_id)
        for s in db_session.scalars(_select(PathStep)).all()
    }
    assert steps_before
    seed_paths(db_session)
    db_session.commit()
    steps_after = {
        s.id: (s.step_type, s.ref_id)
        for s in db_session.scalars(_select(PathStep)).all()
    }
    assert steps_after == steps_before


def test_seed_questions_backfills_without_touching_review_status(db_session, content_tree):
    qdir = content_tree / "questions" / "arrays"
    qdir.mkdir(parents=True, exist_ok=True)
    payload = {
        "id": "q-backfill-1",
        "topic": "arrays-hashing",
        "subtopic": "hashmaps",
        "difficulty": "easy",
        "prompt": "Old prompt?",
        "options": ["a", "b"],
        "correct_index": 0,
        "explanation": "Old explanation.",
        "content_hash": "abc",
        "review_status": "verified",
    }
    (qdir / "q.json").write_text(json.dumps(payload), encoding="utf-8")
    assert seed_questions(db_session, content_tree / "questions") == 1
    row = db_session.get(Question, "q-backfill-1")
    row.review_status = "rejected"
    db_session.commit()

    payload["prompt"] = "New prompt?"
    payload["explanation"] = "New explanation."
    (qdir / "q.json").write_text(json.dumps(payload), encoding="utf-8")
    seed_questions(db_session, content_tree / "questions")
    db_session.commit()
    db_session.refresh(row)
    assert row.prompt == "New prompt?"
    assert row.explanation == "New explanation."
    assert row.review_status == "rejected"


def test_seed_problems_companies_backfill_without_touching_review_status(
    db_session, content_tree
):
    problem_dir = content_tree / "problems"
    payload = {
        "slug": "company-probe",
        "title": "Company Probe",
        "topic": "arrays-hashing",
        "difficulty": "Easy",
        "pattern": "hash-map",
        "statement": "Return the input.",
        "functionName": "solve",
        "reviewStatus": "verified",
        "companies": ["Google", "Amazon"],
        "constraints": [],
        "examples": [],
        "hints": [],
        "testCases": [{"label": "c1", "input": [1], "expected": [1]}],
        "solutions": [
            {
                "title": "ref",
                "language": "python",
                "code": "def solve(a):\n    return a",
                "isReference": True,
            }
        ],
    }
    (problem_dir / "company-probe.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )

    assert seed_problems(db_session, problem_dir) == 1
    row = db_session.get(Problem, "company-probe")
    assert row is not None
    assert json.loads(row.companies_json) == ["Google", "Amazon"]

    row.review_status = "rejected"
    db_session.commit()

    payload["companies"] = ["Meta", "Google"]
    (problem_dir / "company-probe.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    seed_problems(db_session, problem_dir)
    db_session.refresh(row)

    assert json.loads(row.companies_json) == ["Meta", "Google"]
    assert row.review_status == "rejected"


def test_seed_questions_purges_unreferenced_and_retires_referenced_stale_rows(
    db_session, content_tree
):
    qdir = content_tree / "questions" / "aptitude"
    qdir.mkdir(parents=True, exist_ok=True)
    (qdir / "live.json").write_text(
        json.dumps(
            {
                "id": "live-q-1",
                "topic": "aptitude",
                "subtopic": "percentages",
                "difficulty": "Easy",
                "prompt": "What is 10% of 50?",
                "options": ["4", "5", "6", "7"],
                "correct_index": 1,
                "explanation": "10% of 50 is 5.",
                "content_hash": "hash-live-q-1",
                "review_status": "verified",
            }
        ),
        encoding="utf-8",
    )

    user = User(
        id="user-q-purge-test",
        email="q_purge@merit.org",
        display_name="Q Purge",
        password_hash="x",
    )
    stale_unref = Question(
        id="stale-unref-q",
        topic="aptitude",
        difficulty="Easy",
        prompt="Deleted unreferenced?",
        options='["a","b","c","d"]',
        correct_index=0,
        explanation="Deleted.",
        source="generated",
        content_hash="hash-stale-unref",
        review_status="verified",
    )
    stale_ref = Question(
        id="stale-ref-q",
        topic="aptitude",
        difficulty="Easy",
        prompt="Deleted referenced?",
        options='["a","b","c","d"]',
        correct_index=0,
        explanation="Retired.",
        source="generated",
        content_hash="hash-stale-ref",
        review_status="verified",
    )
    attempt = QuizAttempt(
        id="att-q-purge-1",
        user_id=user.id,
        topic_spec='{"topics":["aptitude"]}',
        question_ids='["stale-ref-q"]',
        total=1,
        correct=0,
        score_pct=0,
        duration_sec=10,
    )
    answer = QuizAttemptAnswer(
        attempt_id=attempt.id,
        question_id="stale-ref-q",
        selected_index=1,
        is_correct=0,
    )
    db_session.add_all([user, stale_unref, stale_ref, attempt, answer])
    db_session.commit()

    seed_questions(db_session, content_tree / "questions")
    db_session.expire_all()

    assert db_session.get(Question, "live-q-1") is not None
    assert db_session.get(Question, "stale-unref-q") is None
    retired_row = db_session.get(Question, "stale-ref-q")
    assert retired_row is not None
    assert retired_row.review_status == "retired"



