from pydantic import BaseModel, ConfigDict, Field


class FeedbackCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=150)
    description: str = Field(..., min_length=5, max_length=5000)
    category: str = Field("bug", description="bug, testcase, feature, other")
    page_url: str | None = Field(None, max_length=500)
    problem_slug: str | None = Field(None, max_length=100)
    email: str | None = Field(None, max_length=200)


class FeedbackResponse(BaseModel):
    status: str
    message: str
    feedback_id: str | None = None
    issue_url: str | None = None
    issue_number: int | None = None


class FeedbackItem(BaseModel):
    id: str
    category: str
    title: str
    description: str
    page_url: str | None = None
    problem_slug: str | None = None
    email: str | None = None
    github_issue_url: str | None = None
    github_issue_number: int | None = None
    status: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)
