"""Content API endpoints for problems, questions, learning paths, and visualizers."""

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models.content import LearningPath, PathStep, Problem, Question
from app.models.progress import ProblemProgress, VisualizerCompletion
from app.models.quiz import PathStepProgress, QuizAttempt
from app.models.user import User, utcnow_iso
from app.security import get_current_user, get_optional_current_user

router = APIRouter(prefix="/api/v1", tags=["content"])


VISUALIZERS_CATALOG = [
    {
        "id": "array",
        "title": "Static & Dynamic Array",
        "category": "Linear Structures",
        "complexity": "O(1) access, O(n) insert/delete",
        "description": "Contiguous memory allocation with index access and dynamic resizing.",
    },
    {
        "id": "sorting",
        "title": "Sorting Algorithms",
        "category": "Fundamental Algorithms",
        "complexity": "O(n log n) - O(n²)",
        "description": (
            "Step-by-step comparisons and swaps for Bubble, Selection, "
            "Insertion, Quick, and Merge sort."
        ),
    },
    {
        "id": "linked-list",
        "title": "Singly Linked List",
        "category": "Linear Structures",
        "complexity": "O(1) head insert, O(n) access",
        "description": "Node pointers, dynamic chaining, traversal, and in-place reversal.",
    },
    {
        "id": "stack",
        "title": "LIFO Stack",
        "category": "Linear Structures",
        "complexity": "O(1) push/pop/peek",
        "description": "Last-In, First-Out stack pointer operations and function call simulation.",
    },
    {
        "id": "queue",
        "title": "FIFO Queue",
        "category": "Linear Structures",
        "complexity": "O(1) enqueue/dequeue",
        "description": "First-In, First-Out buffer with front and rear pointer management.",
    },
    {
        "id": "binary-tree",
        "title": "Binary Tree Traversals",
        "category": "Hierarchical Structures",
        "complexity": "O(n) time, O(h) space",
        "description": "Recursive Preorder, Inorder, Postorder, and Level-Order traversals.",
    },
    {
        "id": "bst",
        "title": "Binary Search Tree (BST)",
        "category": "Hierarchical Structures",
        "complexity": "O(log n) average, O(n) worst",
        "description": "Ordered binary search tree insertion, lookup, and invariant maintenance.",
    },
    {
        "id": "heap",
        "title": "Min / Max Binary Heap",
        "category": "Priority Queues",
        "complexity": "O(log n) push/pop, O(n) build",
        "description": "Complete binary tree with sift-up and sift-down heapify operations.",
    },
    {
        "id": "hashmap",
        "title": "Hash Map (Separate Chaining)",
        "category": "Key-Value Stores",
        "complexity": "O(1) average, O(n) worst",
        "description": "Modulo hashing, bucket arrays, collision resolution via linked chains.",
    },
    {
        "id": "graph",
        "title": "Graph BFS / DFS Explorer",
        "category": "Network Structures",
        "complexity": "O(V + E) time",
        "description": (
            "Breadth-First and Depth-First exploration on directed and undirected graphs."
        ),
    },
    {
        "id": "searching",
        "title": "Linear vs Binary Search",
        "category": "Search Algorithms",
        "complexity": "O(log n) binary vs O(n) linear",
        "description": "Side-by-side search interval reduction and comparison counts.",
    },
    {
        "id": "recursion-tree",
        "title": "Recursion Call Tree",
        "category": "Algorithmic Paradigms",
        "complexity": "Call stack frames & branching",
        "description": "Recursive state branching, subproblem memoization, and base cases.",
    },
]


@router.get("/visualizers")
def list_visualizers() -> list[dict[str, Any]]:
    return VISUALIZERS_CATALOG


@router.get("/problems")
def list_problems(
    topic: str | None = Query(None),
    difficulty: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    query = select(Problem).where(Problem.review_status == "verified")
    if topic:
        query = query.where(Problem.topic == topic)
    if difficulty:
        query = query.where(Problem.difficulty == difficulty)

    query = query.order_by(Problem.slug).offset(offset).limit(limit)
    problems = db.scalars(query).all()

    return [
        {
            "slug": p.slug,
            "topic": p.topic,
            "difficulty": p.difficulty,
            "pattern": p.pattern,
            "title": p.title,
            "statement": p.statement,
            "examples": json.loads(p.examples) if p.examples else [],
            "constraints": json.loads(p.constraints_json) if p.constraints_json else [],
            "hints": json.loads(p.hints) if p.hints else [],
            "starter_code": json.loads(p.starter_code) if p.starter_code else {},
            "function_name": p.function_name,
            "time_limit_ms": p.time_limit_ms,
            "sequence": p.sequence,
            "prev_slug": p.prev_slug,
            "next_slug": p.next_slug,
        }
        for p in problems
    ]


@router.get("/problems/{slug}")
def get_problem(
    slug: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    problem = db.scalar(
        select(Problem)
        .options(
            selectinload(Problem.test_cases),
            selectinload(Problem.solutions),
        )
        .where(Problem.slug == slug, Problem.review_status == "verified")
    )
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROBLEM_NOT_FOUND", "message": f"Problem '{slug}' not found"},
        )

    return {
        "slug": problem.slug,
        "topic": problem.topic,
        "difficulty": problem.difficulty,
        "pattern": problem.pattern,
        "title": problem.title,
        "statement": problem.statement,
        "examples": json.loads(problem.examples) if problem.examples else [],
        "constraints": json.loads(problem.constraints_json) if problem.constraints_json else [],
        "hints": json.loads(problem.hints) if problem.hints else [],
        "starter_code": json.loads(problem.starter_code) if problem.starter_code else {},
        "editorial": json.loads(problem.editorial_json) if problem.editorial_json else None,
        "reading_links": json.loads(problem.reading_links_json)
        if problem.reading_links_json
        else [],
        "function_name": problem.function_name,
        "time_limit_ms": problem.time_limit_ms,
        "sequence": problem.sequence,
        "prev_slug": problem.prev_slug,
        "next_slug": problem.next_slug,
        "test_cases": [
            {
                "id": tc.id,
                "label": tc.label,
                "input": json.loads(tc.input_json),
                "expected": json.loads(tc.expected_json),
                "is_sample": bool(tc.is_sample),
            }
            for tc in problem.test_cases
            if tc.is_sample == 1
        ],
        "solutions": [
            {
                "id": sol.id,
                "title": sol.title,
                "complexity": sol.complexity,
                "language": sol.language,
                "code": sol.code,
                "is_reference": bool(sol.is_reference),
            }
            for sol in problem.solutions
        ],
        "learning_paths": [
            {
                "slug": ps.path.slug,
                "title": ps.path.title,
                "track": ps.path.track,
            }
            for ps in db.scalars(
                select(PathStep)
                .options(selectinload(PathStep.path))
                .where(PathStep.step_type == "problem", PathStep.ref_id == slug)
            ).all()
            if ps.path and ps.path.is_published == 1
        ],
    }


@router.get("/questions")
def list_questions(
    topic: str | None = Query(None),
    difficulty: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    query = select(Question).where(Question.review_status == "verified")
    if topic:
        query = query.where(Question.topic == topic)
    if difficulty:
        query = query.where(Question.difficulty == difficulty)

    query = query.order_by(Question.id).offset(offset).limit(limit)
    questions = db.scalars(query).all()

    # Note: Do not leak correct_index or explanation in list to preserve quiz integrity
    return [
        {
            "id": q.id,
            "topic": q.topic,
            "subtopic": q.subtopic,
            "difficulty": q.difficulty,
            "qtype": q.qtype,
            "prompt": q.prompt,
            "options": json.loads(q.options) if q.options else [],
            "source": q.source,
        }
        for q in questions
    ]


@router.get("/questions/{id}")
def get_question(
    id: str,  # noqa: A002 - `id` is the public path-param name
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    question = db.scalar(
        select(Question).where(Question.id == id, Question.review_status == "verified")
    )
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "QUESTION_NOT_FOUND", "message": f"Question '{id}' not found"},
        )

    return {
        "id": question.id,
        "topic": question.topic,
        "subtopic": question.subtopic,
        "difficulty": question.difficulty,
        "qtype": question.qtype,
        "prompt": question.prompt,
        "options": json.loads(question.options) if question.options else [],
        "source": question.source,
    }


@router.get("/paths")
def list_paths(
    track: str | None = Query(None),
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    query = (
        select(LearningPath)
        .options(selectinload(LearningPath.steps))
        .where(LearningPath.is_published == 1)
    )
    if track:
        query = query.where(LearningPath.track == track)

    query = query.order_by(LearningPath.ordinal)
    paths = db.scalars(query).all()

    user_problem_done: set[str] = set()
    user_visualizer_done: set[str] = set()
    user_quiz_passed: set[str] = set()
    user_explicit_steps: set[int] = set()

    if current_user:
        problem_rows = db.scalars(
            select(ProblemProgress.problem_slug).where(
                ProblemProgress.user_id == current_user.id,
                ProblemProgress.status == "Done",
            )
        ).all()
        user_problem_done = set(problem_rows)

        vis_rows = db.scalars(
            select(VisualizerCompletion.visualizer_id).where(
                VisualizerCompletion.user_id == current_user.id,
            )
        ).all()
        user_visualizer_done = set(vis_rows)

        quiz_attempts = db.scalars(
            select(QuizAttempt).where(
                QuizAttempt.user_id == current_user.id,
                QuizAttempt.score_pct >= 70,
            )
        ).all()
        for qa in quiz_attempts:
            try:
                spec = json.loads(qa.topic_spec)
                topics = spec.get("topics", [])
                for t in topics:
                    user_quiz_passed.add(t)
            except Exception:
                pass

        step_progress_rows = db.scalars(
            select(PathStepProgress.step_id).where(
                PathStepProgress.user_id == current_user.id,
            )
        ).all()
        user_explicit_steps = set(step_progress_rows)

    result = []
    for p in paths:
        total = len(p.steps)
        completed = 0
        for s in p.steps:
            is_comp = False
            if current_user:
                if s.id in user_explicit_steps:
                    is_comp = True
                elif s.step_type == "problem":
                    is_comp = s.ref_id in user_problem_done
                elif s.step_type == "visualizer":
                    is_comp = s.ref_id in user_visualizer_done
                elif s.step_type == "quiz":
                    is_comp = s.ref_id in user_quiz_passed
                elif s.step_type == "mock":
                    is_comp = s.id in user_explicit_steps or len(user_quiz_passed) > 0
            if is_comp:
                completed += 1

        pct = round((completed / total) * 100) if total > 0 else 0
        result.append(
            {
                "slug": p.slug,
                "title": p.title,
                "blurb": p.blurb,
                "icon": p.icon,
                "track": p.track,
                "ordinal": p.ordinal,
                "total_steps": total,
                "completed_steps": completed,
                "progress_pct": pct,
                "step_count": total,
                "steps": [
                    {
                        "id": s.id,
                        "ordinal": s.ordinal,
                        "step_type": s.step_type,
                        "ref_id": s.ref_id,
                        "title": s.title,
                        "summary": s.summary,
                        "reading_links": json.loads(s.reading_links_json)
                        if s.reading_links_json
                        else [],
                    }
                    for s in sorted(p.steps, key=lambda st: st.ordinal)
                ],
            }
        )

    return result


@router.get("/paths/{slug}")
def get_path(
    slug: str,
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    path = db.scalar(
        select(LearningPath)
        .options(selectinload(LearningPath.steps))
        .where(LearningPath.slug == slug, LearningPath.is_published == 1)
    )
    if not path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PATH_NOT_FOUND", "message": f"Learning path '{slug}' not found"},
        )

    user_problem_done: set[str] = set()
    user_visualizer_done: set[str] = set()
    user_quiz_passed: set[str] = set()
    user_explicit_steps: set[int] = set()
    total_quiz_attempts = 0

    if current_user:
        problem_rows = db.scalars(
            select(ProblemProgress.problem_slug).where(
                ProblemProgress.user_id == current_user.id,
                ProblemProgress.status == "Done",
            )
        ).all()
        user_problem_done = set(problem_rows)

        vis_rows = db.scalars(
            select(VisualizerCompletion.visualizer_id).where(
                VisualizerCompletion.user_id == current_user.id,
            )
        ).all()
        user_visualizer_done = set(vis_rows)

        quiz_attempts = db.scalars(
            select(QuizAttempt).where(
                QuizAttempt.user_id == current_user.id,
            )
        ).all()
        total_quiz_attempts = len(quiz_attempts)
        for qa in quiz_attempts:
            if qa.score_pct >= 70:
                try:
                    spec = json.loads(qa.topic_spec)
                    topics = spec.get("topics", [])
                    for t in topics:
                        user_quiz_passed.add(t)
                except Exception:
                    pass

        step_progress_rows = db.scalars(
            select(PathStepProgress.step_id).where(
                PathStepProgress.user_id == current_user.id,
            )
        ).all()
        user_explicit_steps = set(step_progress_rows)

    resolved_steps = []
    completed_count = 0
    next_step_id = None

    sorted_steps = sorted(path.steps, key=lambda st: st.ordinal)
    for s in sorted_steps:
        is_completed = False
        if current_user:
            if s.id in user_explicit_steps:
                is_completed = True
            elif s.step_type == "problem":
                is_completed = s.ref_id in user_problem_done
            elif s.step_type == "visualizer":
                is_completed = s.ref_id in user_visualizer_done
            elif s.step_type == "quiz":
                is_completed = s.ref_id in user_quiz_passed
            elif s.step_type == "mock":
                is_completed = s.id in user_explicit_steps or total_quiz_attempts > 0

        if is_completed:
            completed_count += 1
        elif next_step_id is None:
            next_step_id = s.id

        resolved_steps.append(
            {
                "id": s.id,
                "ordinal": s.ordinal,
                "step_type": s.step_type,
                "ref_id": s.ref_id,
                "title": s.title,
                "summary": s.summary,
                "reading_links": json.loads(s.reading_links_json) if s.reading_links_json else [],
                "completed": is_completed,
            }
        )

    total_steps = len(resolved_steps)
    progress_pct = round((completed_count / total_steps) * 100) if total_steps > 0 else 0

    return {
        "slug": path.slug,
        "title": path.title,
        "blurb": path.blurb,
        "icon": path.icon,
        "track": path.track,
        "ordinal": path.ordinal,
        "total_steps": total_steps,
        "completed_steps": completed_count,
        "progress_pct": progress_pct,
        "next_step_id": next_step_id,
        "steps": resolved_steps,
    }


@router.post("/paths/steps/{step_id}/complete")
def complete_path_step(
    step_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    step = db.get(PathStep, step_id)
    if not step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "STEP_NOT_FOUND", "message": f"Path step {step_id} not found"},
        )

    existing = db.scalar(
        select(PathStepProgress).where(
            PathStepProgress.user_id == current_user.id,
            PathStepProgress.step_id == step_id,
        )
    )
    if not existing:
        new_progress = PathStepProgress(
            user_id=current_user.id,
            step_id=step_id,
            completed_at=utcnow_iso(),
        )
        db.add(new_progress)
        db.commit()

    return {"step_id": step_id, "completed": True}
