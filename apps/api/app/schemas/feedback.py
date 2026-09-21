from typing import Optional
from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=150)
    description: str = Field(..., min_length=5, max_length=5000)
    category: str = Field("bug", description="bug, testcase, feature, other")
    page_url: Optional[str] = Field(None, max_length=500)
    problem_slug: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=200)


class FeedbackResponse(BaseModel):
    status: str
    message: str
    issue_url: Optional[str] = None
    issue_number: Optional[int] = None
