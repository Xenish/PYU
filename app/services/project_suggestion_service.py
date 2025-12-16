from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import LLMIntent
from app.models.project import Project, ProjectSuggestion
from app.schemas.llm.project_suggestions import (
    ProjectReviewLLMResponse,
    ProjectSuggestionLLMResponse,
)
from app.services.llm_adapter import call_llm
from app.services.prompts import (
    build_project_review_prompt,
    build_project_suggestion_prompt,
    build_expand_suggestion_prompt,
)


async def generate_initial_suggestions(
    db: AsyncSession,
    project: Project,
) -> list[ProjectSuggestion]:
    """
    Generate initial AI suggestions for project.

    Called when user clicks "Öneri ver" button.
    """
    # Build prompt
    prompt = build_project_suggestion_prompt(
        project_name=project.name,
        project_description=project.description or "",
    )

    # Call LLM
    response = await call_llm(
        prompt,
        ProjectSuggestionLLMResponse,
        db=db,
        project_id=project.id,
        intent=LLMIntent.PROJECT_SUGGESTION,
    )

    # Create suggestion objects
    suggestions = []
    for item in response.suggestions:
        suggestion = ProjectSuggestion(
            project_id=project.id,
            title=item.title,
            description=item.description,
            category=item.category,
            examples=item.examples,
            is_selected=False,
            generation_round=1,
            # Decision support fields
            priority_score=item.priority_score,
            impact_level=item.impact_level,
            recommendation_type=item.recommendation_type,
            category_tags=item.category_tags,
            rationale=item.rationale,
            advantages=item.advantages,
            disadvantages=item.disadvantages,
        )
        db.add(suggestion)
        suggestions.append(suggestion)

    await db.flush()
    return suggestions


async def review_and_expand_suggestions(
    db: AsyncSession,
    project: Project,
) -> dict:
    """
    Review existing suggestions and generate new ones.

    Called when user clicks "Kontrol ve yenilik" button.

    Returns:
        dict with keys: reviews, new_suggestions, overall_feedback
    """
    # Get existing suggestions
    result = await db.execute(
        select(ProjectSuggestion).where(
            ProjectSuggestion.project_id == project.id,
            ProjectSuggestion.is_deleted == False,  # noqa: E712
        )
    )
    existing = result.scalars().all()

    # Filter out suggestions where ALL examples have been added by user
    # Only send suggestions that still have at least one unused example
    suggestions_to_review = []
    for s in existing:
        if not s.examples:
            # No examples, skip this suggestion
            continue

        if not s.user_added_examples:
            # No examples added yet, include all
            suggestions_to_review.append(s)
            continue

        # Check if there are any examples not added yet
        unused_examples = [
            ex for ex in s.examples if ex not in s.user_added_examples
        ]
        if unused_examples:
            suggestions_to_review.append(s)

    # Build prompt with suggestions that still have unused examples
    existing_data = [
        {
            "title": s.title,
            "description": s.description,
            "category": s.category,
            "examples": s.examples,
            "user_added_examples": s.user_added_examples or [],
        }
        for s in suggestions_to_review
    ]

    prompt = build_project_review_prompt(
        project_name=project.name,
        project_description=project.description or "",
        existing_suggestions=existing_data,
    )

    # Call LLM
    response = await call_llm(
        prompt,
        ProjectReviewLLMResponse,
        db=db,
        project_id=project.id,
        intent=LLMIntent.PROJECT_REVIEW,
    )

    # Get max generation round
    max_round = max([s.generation_round for s in existing], default=0)

    # Create new suggestion objects from new_suggestions
    new_suggestions = []
    for item in response.new_suggestions:
        suggestion = ProjectSuggestion(
            project_id=project.id,
            title=item.title,
            description=item.description,
            category=item.category,
            examples=item.examples,
            is_selected=False,
            generation_round=max_round + 1,
            # Decision support fields
            priority_score=item.priority_score,
            impact_level=item.impact_level,
            recommendation_type=item.recommendation_type,
            category_tags=item.category_tags,
            rationale=item.rationale,
            advantages=item.advantages,
            disadvantages=item.disadvantages,
        )
        db.add(suggestion)
        new_suggestions.append(suggestion)

    # Create expanded suggestions from inadequate reviews
    for review in response.reviews:
        if not review.is_adequate and review.expanded_suggestions:
            for expanded in review.expanded_suggestions:
                suggestion = ProjectSuggestion(
                    project_id=project.id,
                    title=expanded.title,
                    description=expanded.description,
                    category=expanded.category,
                    examples=expanded.examples,
                    is_selected=False,
                    generation_round=max_round + 1,
                    # Decision support fields
                    priority_score=expanded.priority_score,
                    impact_level=expanded.impact_level,
                    recommendation_type=expanded.recommendation_type,
                    category_tags=expanded.category_tags,
                    rationale=expanded.rationale,
                    advantages=expanded.advantages,
                    disadvantages=expanded.disadvantages,
                )
                db.add(suggestion)
                new_suggestions.append(suggestion)

    await db.flush()

    return {
        "reviews": [r.model_dump() for r in response.reviews],
        "new_suggestions": new_suggestions,
        "overall_feedback": response.overall_feedback,
    }


async def expand_suggestion(
    db: AsyncSession,
    project: Project,
    suggestion: ProjectSuggestion,
) -> list[ProjectSuggestion]:
    """
    Expand a single suggestion into 3 detailed versions.

    Called when user clicks "Detaylandır" button on a suggestion.
    """
    # Build prompt for expanding this specific suggestion
    prompt = build_expand_suggestion_prompt(
        project_name=project.name,
        project_description=project.description or "",
        suggestion_title=suggestion.title,
        suggestion_description=suggestion.description or "",
    )

    # Call LLM
    response = await call_llm(
        prompt,
        ProjectSuggestionLLMResponse,
        db=db,
        project_id=project.id,
        intent=LLMIntent.PROJECT_SUGGESTION,
    )

    # Get max generation round
    result = await db.execute(
        select(ProjectSuggestion).where(
            ProjectSuggestion.project_id == project.id,
            ProjectSuggestion.is_deleted == False,  # noqa: E712
        )
    )
    existing = result.scalars().all()
    max_round = max([s.generation_round for s in existing], default=0)

    # Create expanded suggestion objects
    expanded_suggestions = []
    for item in response.suggestions[:3]:  # Max 3
        expanded = ProjectSuggestion(
            project_id=project.id,
            title=item.title,
            description=item.description,
            category=item.category,
            examples=item.examples,
            is_selected=False,
            generation_round=max_round + 1,
            # Decision support fields
            priority_score=item.priority_score,
            impact_level=item.impact_level,
            recommendation_type=item.recommendation_type,
            category_tags=item.category_tags,
            rationale=item.rationale,
            advantages=item.advantages,
            disadvantages=item.disadvantages,
        )
        db.add(expanded)
        expanded_suggestions.append(expanded)

    await db.flush()
    return expanded_suggestions
