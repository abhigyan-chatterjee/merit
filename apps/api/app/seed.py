import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.content import Problem, ProblemSolution, ProblemTestCase


def seed_problems(db: Session, content_dir: Path | None = None) -> int:
    if content_dir is None:
        # Default content directory relative to this file
        content_dir = Path(__file__).resolve().parent.parent.parent.parent / "content" / "problems"

    if not content_dir.exists():
        return 0

    count = 0
    for file_path in sorted(content_dir.glob("*.json")):
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        slug = data["slug"]
        existing = db.scalar(select(Problem).where(Problem.slug == slug))

        starter_dict = {"javascript": data.get("starterCode", "")}
        # Add a default python starter code template if not present
        fn_name = data.get("functionName", "solution")
        starter_dict["python"] = (
            f"def {fn_name}(*args):\n    # TODO: Implement solution\n    pass\n"
        )

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
                function_name=data["functionName"],
                time_limit_ms=2000,
                review_status="verified",
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

    db.commit()
    return count


if __name__ == "__main__":
    with SessionLocal() as session:
        inserted = seed_problems(session)
        print(f"Seeded {inserted} problems into the database.")
