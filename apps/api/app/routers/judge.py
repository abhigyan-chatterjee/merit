import json
import logging
import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.http_status import HTTP_422
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
from app.security import get_current_user, require_same_origin
from app.services.judge import JudgeResult
from app.services.judge_backend import execute as execute_code
from app.services.revision import record_submission
from app.services.signatures import get_signature
from app.services.streak import record_activity

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/judge",
    tags=["Judge"],
    dependencies=[Depends(require_same_origin)],
)

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
            status_code=HTTP_422,
            detail={
                "code": "INVALID_FUNCTION_NAME",
                "message": "Problem function name is not a valid identifier.",
            },
        )
    return problem


def _result_models(rows) -> list[TestCaseResult]:
    if not isinstance(rows, list):
        return []
    """Builds response models defensively.

    The rows come from student-visible process output, so a missing or wrong-typed
    field must degrade to a plausible value rather than raise a ValidationError
    into a 500 — and on the submit path that error would fire *after* the
    submission was committed, reporting failure for work that was saved.
    """
    models: list[TestCaseResult] = []
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        try:
            runtime = float(row.get("runtime_ms") or 0.0)
        except (TypeError, ValueError):
            runtime = 0.0
        error = row.get("error")
        models.append(
            TestCaseResult(
                label=str(row.get("label") or "case"),
                # `bool("false")` is True; only a real boolean counts.
                passed=row.get("passed") is True,
                input=row.get("input"),
                expected=row.get("expected"),
                actual=row.get("actual"),
                runtime_ms=runtime,
                error=error if isinstance(error, str) or error is None else str(error),
                hidden=row.get("hidden") is True,
            )
        )
    return models


def _redact_hidden_results(rows: list[dict], tc_rows: list[ProblemTestCase]) -> list[dict]:
    """Hides a non-sample case's data, keeping only its pass/fail.

    Sample cases keep every field so the learner can debug against them; a
    hidden case must not reveal the input or the answer. Rows and cases are
    paired by position, so a mismatch stops at the last complete pair rather
    than inventing a result.
    """
    redacted: list[dict] = []
    hidden_idx = 0
    for row, tc in zip(rows, tc_rows, strict=False):
        if not isinstance(row, dict):
            continue
        if tc.is_sample == 1:
            redacted.append({**row, "hidden": False})
            continue
        hidden_idx += 1
        redacted.append(
            {
                "label": f"Hidden Case {hidden_idx}",
                "passed": row.get("passed") is True,
                "input": None,
                "expected": None,
                "actual": None,
                "runtime_ms": row.get("runtime_ms", 0.0),
                "error": row.get("error"),
                "hidden": True,
            }
        )
    return redacted


async def _execute(
    *, language: str, code: str, function_name: str, test_cases: list[dict],
    time_limit_ms: int, signature: dict | None,
):
    """Calls the judge, turning an internal failure into a graded RE.

    Anything that escapes `execute_code` — a parser bug on hostile output, a
    missing toolchain, an unexpected exception in harness generation — is this
    service's fault, not the student's. It must not surface as a 500 on a route
    whose sibling path just committed a submission row.
    """
    try:
        return await execute_code(
            language=language,
            code=code,
            function_name=function_name,
            test_cases=test_cases,
            time_limit_ms=time_limit_ms,
            signature=signature,
        )
    except Exception:
        logger.exception("Judge execution failed for %s", language)
        return JudgeResult(
            verdict="RE",
            runtime_ms=0,
            test_results=[],
            compile_output=(
                "The grader hit an internal error on this submission. "
                "Nothing was recorded for it — please try again."
            ),
            infrastructure_error=True,
        )


def _cases_from_rows(tc_rows: list[ProblemTestCase]) -> list[dict]:
    """Materialises test-case rows, failing closed on an empty set.

    An empty case list reached the harness, where `all([])` graded it AC and the
    submit handler flipped the problem to "Done". Refusing here means a missing
    seed row is a loud error instead of free completion.
    """
    if not tc_rows:
        raise HTTPException(
            status_code=HTTP_422,
            detail={
                "code": "NO_TEST_CASES",
                "message": (
                    "This problem has no test cases on this deployment, so nothing "
                    "can be graded. Please report it."
                ),
            },
        )
    cases = []
    for tc in tc_rows:
        try:
            input_data = json.loads(tc.input_json)
            expected_data = json.loads(tc.expected_json)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=HTTP_422,
                detail={
                    "code": "INVALID_TEST_CASE",
                    "message": "Problem test case data is malformed.",
                },
            ) from None
        cases.append({"label": tc.label, "input": input_data, "expected": expected_data})
    return cases


@router.post("/run", response_model=JudgeRunResponse)
async def run_samples(
    req: JudgeRunRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    problem = _get_verified_problem(db, req.problem_slug)

    if not req.code.strip():
        raise HTTPException(
            status_code=HTTP_422,
            detail={
                "code": "EMPTY_CODE",
                "message": "Code must not be empty.",
            },
        )

    signature = get_signature(problem.slug)

    if req.custom_input is not None:
        if len(json.dumps(req.custom_input).encode("utf-8")) > 32_768:
            raise HTTPException(
                status_code=HTTP_422,
                detail={
                    "code": "INVALID_CUSTOM_INPUT",
                    "message": "Custom input must be at most 32 KB of JSON.",
                },
            )
        expected_arity = None
        if isinstance(signature, dict) and isinstance(signature.get("params"), list):
            expected_arity = len(signature["params"])
        else:
            first_tc = db.scalars(
                select(ProblemTestCase)
                .where(ProblemTestCase.problem_slug == req.problem_slug)
                .order_by(ProblemTestCase.ordinal)
                .limit(1)
            ).first()
            if first_tc is not None:
                try:
                    parsed_input = json.loads(first_tc.input_json)
                except (TypeError, ValueError):
                    parsed_input = None
                if isinstance(parsed_input, list):
                    expected_arity = len(parsed_input)
        if expected_arity is not None and len(req.custom_input) != expected_arity:
            raise HTTPException(
                status_code=HTTP_422,
                detail={
                    "code": "INVALID_CUSTOM_INPUT",
                    "message": (
                        f"Expected {expected_arity} argument(s) as a JSON array, "
                        f"got {len(req.custom_input)}."
                    ),
                },
            )
        res = await _execute(
            language=req.language,
            code=req.code,
            function_name=problem.function_name,
            test_cases=[
                {"label": "Custom Input", "input": req.custom_input, "expected": None}
            ],
            time_limit_ms=problem.time_limit_ms,
            signature=signature,
        )
        if (
            res.infrastructure_error
            or res.verdict in {"CE", "TLE", "RE"}
            or not res.test_results
        ):
            return JudgeRunResponse(
                verdict=res.verdict,
                runtime_ms=res.runtime_ms,
                test_results=_result_models(res.test_results),
                compile_output=res.compile_output,
                infrastructure_error=res.infrastructure_error,
                passed_count=0,
                total_count=1,
                custom_run=True,
            )
        row = dict(res.test_results[0])
        if row.get("error"):
            verdict = "RE"
            row["passed"] = False
            passed_count = 0
        else:
            verdict = "CUSTOM"
            row["passed"] = True
            row["expected"] = None
            row["hidden"] = False
            passed_count = 1
        return JudgeRunResponse(
            verdict=verdict,
            runtime_ms=res.runtime_ms,
            test_results=_result_models([row]),
            compile_output=res.compile_output,
            infrastructure_error=False,
            passed_count=passed_count,
            total_count=1,
            custom_run=True,
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

    cases = _cases_from_rows(tc_rows)

    res = await _execute(
        language=req.language,
        code=req.code,
        function_name=problem.function_name,
        test_cases=cases,
        time_limit_ms=problem.time_limit_ms,
        # Compiled languages need the recorded types to generate their
        # harness; the interpreted languages ignore it.
        signature=signature,
    )

    models = _result_models(res.test_results)

    return JudgeRunResponse(
        verdict=res.verdict,
        runtime_ms=res.runtime_ms,
        test_results=models,
        compile_output=res.compile_output,
        infrastructure_error=res.infrastructure_error,
        passed_count=sum(1 for m in models if m.passed),
        total_count=len(models),
        custom_run=False,
    )


@router.post("/submit", response_model=SubmissionResponse)
async def submit_solution(
    req: JudgeRunRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    problem = _get_verified_problem(db, req.problem_slug)

    if not req.code.strip():
        raise HTTPException(
            status_code=HTTP_422,
            detail={
                "code": "EMPTY_CODE",
                "message": "Submitted code must not be empty.",
            },
        )

    if req.custom_input is not None:
        raise HTTPException(
            status_code=HTTP_422,
            detail={
                "code": "INVALID_SUBMIT_REQUEST",
                "message": "Custom input is only supported on Run, not Submit.",
            },
        )

    # Load all test cases
    tc_rows = db.scalars(
        select(ProblemTestCase)
        .where(ProblemTestCase.problem_slug == req.problem_slug)
        .order_by(ProblemTestCase.ordinal)
    ).all()

    cases = _cases_from_rows(tc_rows)

    res = await _execute(
        language=req.language,
        code=req.code,
        function_name=problem.function_name,
        test_cases=cases,
        time_limit_ms=problem.time_limit_ms,
        # Compiled languages need the recorded types to generate their
        # harness; the interpreted languages ignore it.
        signature=get_signature(problem.slug),
    )

    now_str = utcnow_iso()

    if res.infrastructure_error:
        # Nothing was graded, so nothing is recorded: no Submission row, and no
        # streak movement. The handler's own message tells the user that, and
        # writing history anyway made the message a lie.
        return SubmissionResponse(
            id="",
            problem_slug=req.problem_slug,
            language=req.language,
            code=req.code,
            verdict=res.verdict,
            runtime_ms=res.runtime_ms,
            test_results=[],
            created_at=now_str,
            compile_output=res.compile_output,
            infrastructure_error=res.infrastructure_error,
            passed_count=0,
            total_count=0,
        )

    redacted_rows = _redact_hidden_results(res.test_results, tc_rows)
    test_results_json = json.dumps(redacted_rows)
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
    # Feed the spaced-repetition schedule. Deliberately after the commit and
    # inside a guard: the attempt is already saved and graded, and a scheduling
    # error must not turn a successful submission into a 500 for the student.
    try:
        record_submission(db, user.id, req.problem_slug, res.verdict)
    except Exception:
        logger.exception("Could not schedule a revision item for %s", req.problem_slug)
        db.rollback()
    db.refresh(submission)
    sub_id = submission.id
    created_at = submission.created_at

    models = _result_models(redacted_rows)

    return SubmissionResponse(
        id=sub_id,
        problem_slug=req.problem_slug,
        language=req.language,
        code=req.code,
        verdict=res.verdict,
        runtime_ms=res.runtime_ms,
        test_results=models,
        created_at=created_at,
        compile_output=res.compile_output,
        infrastructure_error=res.infrastructure_error,
        passed_count=sum(1 for m in models if m.passed),
        total_count=len(models),
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
        try:
            results_data = json.loads(s.test_results) if s.test_results else []
        except (TypeError, ValueError):
            results_data = []
        models = _result_models(results_data)
        resp.append(
            SubmissionResponse(
                id=s.id,
                problem_slug=s.problem_slug,
                language=s.language,
                code=s.code,
                verdict=s.verdict,
                runtime_ms=s.runtime_ms,
                test_results=models,
                created_at=s.created_at,
                passed_count=sum(1 for m in models if m.passed),
                total_count=len(models),
            )
        )
    return resp
