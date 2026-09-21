import logging
import os
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackCreate, FeedbackResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
) -> FeedbackResponse:
    """Submit user feedback or bug report.

    Persists report to the database table first, then creates an issue on the
    configured GitHub repository if GITHUB_TOKEN is present.
    """
    category_label = payload.category.strip().lower()
    if category_label not in {"bug", "testcase", "feature", "other"}:
        category_label = "bug"

    feedback_record = Feedback(
        category=category_label,
        title=payload.title.strip(),
        description=payload.description.strip(),
        page_url=payload.page_url.strip() if payload.page_url else None,
        problem_slug=payload.problem_slug.strip() if payload.problem_slug else None,
        email=payload.email.strip() if payload.email else None,
        status="open",
    )
    db.add(feedback_record)
    db.commit()
    db.refresh(feedback_record)

    token = (
        settings.github_token
        or os.environ.get("GITHUB_TOKEN", "")
        or os.environ.get("GH_TOKEN", "")
    ).strip()

    repo = (settings.github_repo or "abhigyan-chatterjee/merit").strip()

    body_lines = [
        "### User Feedback Submission",
        f"- **Category:** `{payload.category}`",
        f"- **Reported URL:** {payload.page_url or 'N/A'}",
        f"- **Problem Context:** {payload.problem_slug or 'N/A'}",
        f"- **Contact:** {payload.email or 'Anonymous'}",
        f"- **Internal Ref:** `{feedback_record.id}`",
        "",
        "### Details",
        payload.description.strip(),
        "",
        "---",
        "*Submitted via Merit in-app feedback dialog*",
    ]
    issue_body = "\n".join(body_lines)

    if token and repo:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(
                    f"https://api.github.com/repos/{repo}/issues",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github+json",
                        "User-Agent": "Merit-App",
                    },
                    json={
                        "title": f"[{payload.category.upper()}] {payload.title.strip()}",
                        "body": issue_body,
                        "labels": ["user-feedback", category_label],
                    },
                )
                if res.status_code in {200, 201}:
                    data = res.json()
                    feedback_record.github_issue_url = data.get("html_url")
                    feedback_record.github_issue_number = data.get("number")
                    db.commit()
                    return FeedbackResponse(
                        status="ok",
                        message="Issue created successfully on GitHub!",
                        feedback_id=feedback_record.id,
                        issue_url=data.get("html_url"),
                        issue_number=data.get("number"),
                    )
                else:
                    logger.warning(
                        "GitHub issue creation failed with status %d: %s",
                        res.status_code,
                        res.text[:200],
                    )
        except Exception as exc:
            logger.warning("Error forwarding feedback to GitHub: %s", exc)

    logger.info(
        "User feedback recorded in DB: [%s] %s (id: %s)",
        feedback_record.category,
        feedback_record.title,
        feedback_record.id,
    )

    return FeedbackResponse(
        status="ok",
        message="Thank you! Your feedback has been recorded.",
        feedback_id=feedback_record.id,
        issue_url=None,
        issue_number=None,
    )
