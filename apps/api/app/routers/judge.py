import json
import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.content import Problem, ProblemTestCase
from app.models.progress import ProblemProgress
from app.models.submission import Submission
from app.models.user import User, utcnow_iso
from app.schemas.judge import (
    JudgeRunRequest,
    JudgeRunResponse,
    SubmissionResponse,
    TestCaseResult,
)
from app.security import get_current_user, get_optional_current_user
from app.services.judge import execute_code
from app.services.streak import record_activity

router = APIRouter(prefix="/api/v1/judge", tags=["Judge"])

# Content files supply function names, but the harness interpolates them into
# generated code — enforce a plain identifier before anything reaches it.
FUNCTION_NAME_RE = re.compile(r"^[A-Za-z_$][\w$]*\Z")
DUNDER_NAME_RE = re.compile(r"^__.*__\Z")


def _get_verified_problem(db: Session, slug: str) -> Problem:
    problem = db.scalar(
        select(Problem).where(
            Problem.slug == slug,
            Problem.review_status == "verified",
        )
    )
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PROBLEM_NOT_FOUND",
                "message": f"Problem '{slug}' not found",
            },
        )
    if (
        not FUNCTION_NAME_RE.match(problem.function_name)
        or DUNDER_NAME_RE.match(problem.function_name)
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "INVALID_FUNCTION_NAME",
                "message": "Problem function name is not a valid identifier.",
            },
        )
    return problem


@router.post("/run", response_model=JudgeRunResponse)
async def run_samples(
    req: JudgeRunRequest,
    user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    problem = _get_verified_problem(db, req.problem_slug)

    if not req.code.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "EMPTY_CODE",
                "message": "Code must not be empty.",
            },
        )

    # Load sample test cases
    tc_rows = db.scalars(
        select(ProblemTestCase)
        .where(ProblemTestCase.problem_slug == req.problem_slug, ProblemTestCase.is_sample == 1)
        .order_by(ProblemTestCase.ordinal)
    ).all()

    # Fallback to first two if none marked sample
    if not tc_rows:
        tc_rows = db.scalars(
            select(ProblemTestCase)
            .where(ProblemTestCase.problem_slug == req.problem_slug)
            .order_by(ProblemTestCase.ordinal)
            .limit(2)
        ).all()

    cases = []
    for tc in tc_rows:
        cases.append(
            {
                "label": tc.label,
                "input": json.loads(tc.input_json),
                "expected": json.loads(tc.expected_json),
            }
        )

    res = await execute_code(
        language=req.language,
        code=req.code,
        function_name=problem.function_name,
        test_cases=cases,
        time_limit_ms=problem.time_limit_ms,
    )

    return JudgeRunResponse(
        verdict=res.verdict,
        runtime_ms=res.runtime_ms,
        test_results=[TestCaseResult(**t) for t in res.test_results],
        compile_output=res.compile_output,
    )


@router.post("/submit", response_model=SubmissionResponse)
async def submit_solution(
    req: JudgeRunRequest,
    user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    problem = _get_verified_problem(db, req.problem_slug)

    if not req.code.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "EMPTY_CODE",
                "message": "Submitted code must not be empty.",
            },
        )

    # Load all test cases
    tc_rows = db.scalars(
        select(ProblemTestCase)
        .where(ProblemTestCase.problem_slug == req.problem_slug)
        .order_by(ProblemTestCase.ordinal)
    ).all()

    cases = []
    for tc in tc_rows:
        cases.append(
            {
                "label": tc.label,
                "input": json.loads(tc.input_json),
                "expected": json.loads(tc.expected_json),
            }
        )

    res = await execute_code(
        language=req.language,
        code=req.code,
        function_name=problem.function_name,
        test_cases=cases,
        time_limit_ms=problem.time_limit_ms,
    )

    now_str = utcnow_iso()

    if user is not None:
        test_results_json = json.dumps(res.test_results)
        submission = Submission(
            user_id=user.id,
            problem_slug=req.problem_slug,
            language=req.language,
            code=req.code,
            verdict=res.verdict,
            runtime_ms=res.runtime_ms,
            test_results=test_results_json,
            created_at=now_str,
        )
        db.add(submission)

        # If AC, flip problem_progress to Done
        if res.verdict == "AC":
            prog = db.scalar(
                select(ProblemProgress).where(
                    ProblemProgress.user_id == user.id,
                    ProblemProgress.problem_slug == req.problem_slug,
                )
            )
            if prog:
                prog.status = "Done"
                prog.updated_at = now_str
            else:
                prog = ProblemProgress(
                    user_id=user.id,
                    problem_slug=req.problem_slug,
                    status="Done",
                    updated_at=now_str,
                )
                db.add(prog)

        record_activity(db, user.id)
        db.commit()
        db.refresh(submission)
        sub_id = submission.id
        created_at = submission.created_at
    else:
        sub_id = "guest"
        created_at = now_str

    return SubmissionResponse(
        id=sub_id,
        problem_slug=req.problem_slug,
        language=req.language,
        verdict=res.verdict,
        runtime_ms=res.runtime_ms,
        test_results=[TestCaseResult(**t) for t in res.test_results],
        created_at=created_at,
    )


@router.get("/submissions/{problem_slug}", response_model=list[SubmissionResponse])
def get_submissions(
    problem_slug: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(Submission)
        .where(
            Submission.user_id == user.id,
            Submission.problem_slug == problem_slug,
        )
        .order_by(Submission.created_at.desc())
    ).all()

    resp = []
    for s in rows:
        results_data = json.loads(s.test_results) if s.test_results else []
        resp.append(
            SubmissionResponse(
                id=s.id,
                problem_slug=s.problem_slug,
                language=s.language,
                verdict=s.verdict,
                runtime_ms=s.runtime_ms,
                test_results=[TestCaseResult(**t) for t in results_data],
                created_at=s.created_at,
            )
        )
    return resp
