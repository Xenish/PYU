from pydantic import BaseModel, Field


class ProjectSuggestionItem(BaseModel):
    """Single suggestion item from LLM."""
    title: str = Field(..., description="Short title for the suggestion")
    description: str = Field(..., description="Detailed explanation")
    category: str = Field(..., description="Category: strategy, technical, process, quality")
    examples: list[str] = Field(default_factory=list, description="2-3 example use cases")

    # Decision support metadata
    priority_score: int | None = Field(None, ge=1, le=5, description="Priority 1-5")
    impact_level: str | None = Field(None, description="low, medium, high, critical")
    recommendation_type: str | None = Field(None, description="recommended, optional, critical")
    category_tags: list[str] | None = Field(None, description="Tags like security, performance")
    rationale: str | None = Field(None, description="Why this is important")
    advantages: list[str] | None = Field(None, description="Pros")
    disadvantages: list[str] | None = Field(None, description="Cons")


class ProjectSuggestionLLMResponse(BaseModel):
    """LLM response for project suggestions."""
    suggestions: list[ProjectSuggestionItem] = Field(
        ...,
        description="List of project suggestions, max 10 items"
    )


class ProjectReviewItem(BaseModel):
    """Review feedback for existing suggestions."""
    suggestion_title: str = Field(..., description="Title of the suggestion being reviewed")
    is_adequate: bool = Field(..., description="Is the user's answer adequate?")
    feedback: str | None = Field(None, description="Specific feedback if inadequate")
    new_questions: list[str] | None = Field(None, description="Follow-up questions if needed")
    expanded_suggestions: list[ProjectSuggestionItem] | None = Field(
        None,
        description="If inadequate, provide 3 detailed expanded versions of this suggestion"
    )


class ProjectReviewLLMResponse(BaseModel):
    """LLM response for project review."""
    reviews: list[ProjectReviewItem] = Field(..., description="Reviews of existing suggestions")
    new_suggestions: list[ProjectSuggestionItem] = Field(
        default_factory=list,
        description="Additional suggestions based on user input"
    )
    overall_feedback: str = Field(..., description="Overall assessment of project description")
