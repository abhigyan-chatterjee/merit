"""Database seeder for Algovista content (problems, test cases, solutions, questions, paths)."""

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.content import (
    LearningPath,
    PathStep,
    Problem,
    ProblemSolution,
    ProblemTestCase,
    Question,
)


def _resolve_content_dir(subfolder: str) -> Path:
    candidates = [
        Path(__file__).resolve().parent.parent.parent.parent / "content" / subfolder,
        Path(__file__).resolve().parent.parent.parent / "content" / subfolder,
        Path.cwd() / "content" / subfolder,
        Path.cwd().parent / "content" / subfolder,
        Path.cwd().parent.parent / "content" / subfolder,
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def seed_problems(db: Session, content_dir: Path | None = None) -> int:
    if content_dir is None:
        content_dir = _resolve_content_dir("problems")

    if not content_dir.exists():
        return 0

    # Pass 1: Read problem files, skip drafts entirely, and gather verified problems.
    # Note on field inconsistency: question files use snake_case 'review_status',
    # while problem files use camelCase 'reviewStatus'. We accept both spellings,
    # defaulting to 'verified' when absent (verified problem files carry no status field).
    valid_problems: list[dict] = []
    verified_slugs: set[str] = set()

    for file_path in sorted(content_dir.glob("*.json")):
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        status = data.get("reviewStatus") or data.get("review_status") or "verified"
        if status == "draft":
            continue

        verified_slugs.add(data["slug"])
        valid_problems.append(data)

    # Pass 2: Purge stale draft rows on re-seed.
    # If a Problem row exists in the DB whose content file is a draft (or whose file
    # no longer exists), delete it and its dependent rows (test cases, solutions).
    existing_problems = db.scalars(select(Problem)).all()
    for prob in existing_problems:
        if prob.slug not in verified_slugs:
            for tc in db.scalars(
                select(ProblemTestCase).where(ProblemTestCase.problem_slug == prob.slug)
            ).all():
                db.delete(tc)
            for sol in db.scalars(
                select(ProblemSolution).where(ProblemSolution.problem_slug == prob.slug)
            ).all():
                db.delete(sol)
            db.delete(prob)
    db.flush()

    # Pass 3: Ingest or backfill verified problems.
    count = 0
    for data in valid_problems:
        slug = data["slug"]
        existing = db.scalar(select(Problem).where(Problem.slug == slug))

        starter_dict = data.get("starterCode", {})
        if isinstance(starter_dict, str):
            fn_name = data.get("functionName", "solve")
            starter_dict = {
                "javascript": starter_dict,
                "python": f"def {fn_name}(*args):\n    # TODO: Implement solution\n    pass\n",
            }

        status = data.get("reviewStatus") or data.get("review_status") or "verified"

        if not existing:
            problem = Problem(
                slug=slug,
                topic=data["topic"],
                difficulty=data["difficulty"],
                pattern=data["pattern"],
                title=data["title"],
                statement=data["statement"],
                examples=json.dumps(data.get("examples", [])),
                constraints_json=json.dumps(data.get("constraints", [])),
                hints=json.dumps(data.get("hints", [])),
                starter_code=json.dumps(starter_dict),
                editorial_json=json.dumps(data["editorial"])
                if data.get("editorial") is not None
                else None,
                reading_links_json=json.dumps(data["reading_links"])
                if data.get("reading_links") is not None
                else None,
                function_name=data.get("functionName", "solve"),
                time_limit_ms=data.get("timeLimitMs", 2000),
                sequence=data.get("sequence"),
                prev_slug=data.get("prevSlug"),
                next_slug=data.get("nextSlug"),
                review_status=status,
            )
            db.add(problem)
            db.flush()

            for i, tc in enumerate(data.get("testCases", [])):
                test_case = ProblemTestCase(
                    problem_slug=slug,
                    ordinal=i,
                    label=tc.get("label", f"Case {i + 1}"),
                    input_json=json.dumps(tc["input"]),
                    expected_json=json.dumps(tc["expected"]),
                    is_sample=1 if i < 2 else 0,
                )
                db.add(test_case)

            for sol in data.get("solutions", []):
                solution = ProblemSolution(
                    problem_slug=slug,
                    title=sol.get("title", "Solution"),
                    complexity=sol.get("complexity", "O(n)"),
                    language=sol.get("language", "javascript"),
                    code=sol["code"],
                    is_reference=1,
                )
                db.add(solution)

            count += 1
        else:
            # Backfill sequence links + topic on existing rows (taxonomy migration).
            existing.topic = data["topic"]
            existing.sequence = data.get("sequence")
            existing.prev_slug = data.get("prevSlug")
            existing.next_slug = data.get("nextSlug")
            existing.review_status = status
            if data.get("editorial") is not None:
                existing.editorial_json = json.dumps(data["editorial"])
            if data.get("reading_links") is not None:
                existing.reading_links_json = json.dumps(data["reading_links"])

    db.commit()
    return count


def seed_questions(db: Session, questions_dir: Path | None = None) -> int:
    if questions_dir is None:
        questions_dir = _resolve_content_dir("questions")

    if not questions_dir.exists():
        return 0

    count = 0
    for q_file in sorted(questions_dir.glob("*/*.json")):
        with open(q_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        qid = data["id"]
        existing = db.scalar(select(Question).where(Question.id == qid))

        if not existing:
            question = Question(
                id=qid,
                topic=data["topic"],
                subtopic=data.get("subtopic"),
                difficulty=data["difficulty"],
                qtype=data.get("qtype", "mcq"),
                prompt=data["prompt"],
                options=json.dumps(data["options"]),
                correct_index=data["correct_index"],
                explanation=data["explanation"],
                source=data.get("source", "generated"),
                generator_key=data.get("generator_key"),
                content_hash=data["content_hash"],
                review_status=data.get("review_status", "verified"),
            )
            db.add(question)
            count += 1
        else:
            # Backfill topic on existing rows (taxonomy migration).
            if existing.topic != data["topic"]:
                existing.topic = data["topic"]

    db.commit()
    return count


def seed_paths(db: Session, paths_dir: Path | None = None) -> int:
    if paths_dir is None:
        paths_dir = _resolve_content_dir("paths")

    if not paths_dir.exists():
        return 0

    count = 0
    for p_file in sorted(paths_dir.glob("*.json")):
        with open(p_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        slug = data["slug"]
        existing = db.scalar(select(LearningPath).where(LearningPath.slug == slug))

        if not existing:
            path = LearningPath(
                slug=slug,
                title=data["title"],
                blurb=data["blurb"],
                icon=data["icon"],
                track=data["track"],
                ordinal=data["ordinal"],
                is_published=1 if data.get("is_published", True) else 0,
            )
            db.add(path)
            db.flush()

            for step in data.get("steps", []):
                p_step = PathStep(
                    path_slug=slug,
                    ordinal=step["ordinal"],
                    step_type=step["step_type"],
                    ref_id=step["ref_id"],
                    title=step.get("title"),
                    summary=step.get("summary"),
                    reading_links_json=json.dumps(step.get("reading_links", [])),
                )
                db.add(p_step)

            count += 1
        else:
            # Re-sync steps on re-seed (path replacement across scope changes).
            for old_step in db.scalars(
                select(PathStep).where(PathStep.path_slug == slug)
            ).all():
                db.delete(old_step)
            db.flush()
            existing.title = data["title"]
            existing.blurb = data["blurb"]
            existing.icon = data["icon"]
            existing.track = data["track"]
            existing.ordinal = data["ordinal"]
            existing.is_published = 1 if data.get("is_published", True) else 0
            for step in data.get("steps", []):
                db.add(
                    PathStep(
                        path_slug=slug,
                        ordinal=step["ordinal"],
                        step_type=step["step_type"],
                        ref_id=step["ref_id"],
                        title=step.get("title"),
                        summary=step.get("summary"),
                        reading_links_json=json.dumps(step.get("reading_links", [])),
                    )
                )

    db.commit()
    return count


def seed_admin(db: Session) -> int:
    import os
    from app.models.user import User
    from app.security import hash_password

    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_email or not admin_password:
        return 0

    existing = db.scalar(select(User).where(User.email == admin_email))
    if not existing:
        admin_user = User(
            email=admin_email,
            display_name=os.getenv("ADMIN_NAME", "Administrator"),
            password_hash=hash_password(admin_password),
            role="admin",
            is_active=1,
        )
        db.add(admin_user)
        db.commit()
        return 1
    return 0


def seed_all(db: Session) -> dict[str, int]:
    problems_cnt = seed_problems(db)
    questions_cnt = seed_questions(db)
    paths_cnt = seed_paths(db)
    admin_cnt = seed_admin(db)
    return {
        "problems": problems_cnt,
        "questions": questions_cnt,
        "paths": paths_cnt,
        "admin": admin_cnt,
    }


if __name__ == "__main__":
    with SessionLocal() as session:
        results = seed_all(session)
        print(f"Seed complete: {results}")
