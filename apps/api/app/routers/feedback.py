import logging
import os
from typing import Optional

import httpx
from fastapi import APIRouter, status

from app.config import settings
from app.schemas.feedback import FeedbackCreate, FeedbackResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(payload: FeedbackCreate) -> FeedbackResponse:
    """Submit user feedback or bug report.

    Creates an issue on the configured GitHub repository if a GitHub token is
    present, or gracefully logs it locally if running in headless/offline mode.
    """
    token = (
        settings.github_token
        or os.environ.get("GITHUB_TOKEN", "")
        or os.environ.get("GH_TOKEN", "")
    ).strip()

    repo = (settings.github_repo or "abhigyan-chatterjee/merit").strip()

    category_label = payload.category.strip().lower()
    if category_label not in {"bug", "testcase", "feature", "other"}:
        category_label = "feedback"

    body_lines = [
        "### User Feedback Submission",
        f"- **Category:** `{payload.category}`",
        f"- **Reported URL:** {payload.page_url or 'N/A'}",
        f"- **Problem Context:** {payload.problem_slug or 'N/A'}",
        f"- **Contact:** {payload.email or 'Anonymous'}",
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
                    return FeedbackResponse(
                        status="ok",
                        message="Issue created successfully on GitHub!",
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

    # Fallback when token is not present or GitHub API call fails
    logger.info(
        "User feedback recorded locally: [%s] %s | Context: %s | Description: %s",
        payload.category,
        payload.title,
        payload.problem_slug or payload.page_url,
        payload.description[:200],
    )

    return FeedbackResponse(
        status="ok",
        message="Thank you! Your feedback has been recorded.",
        issue_url=None,
        issue_number=None,
    )
