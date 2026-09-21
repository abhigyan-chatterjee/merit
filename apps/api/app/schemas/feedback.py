from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


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
    feedback_id: Optional[str] = None
    issue_url: Optional[str] = None
    issue_number: Optional[int] = None


class FeedbackItem(BaseModel):
    id: str
    category: str
    title: str
    description: str
    page_url: Optional[str] = None
    problem_slug: Optional[str] = None
    email: Optional[str] = None
    github_issue_url: Optional[str] = None
    github_issue_number: Optional[int] = None
    status: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)
