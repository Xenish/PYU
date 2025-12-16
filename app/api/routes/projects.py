from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import project as project_crud
from app.db.session import get_db
from app.schemas.project import (
    ProjectCreate,
    ProjectRead,
    ProjectReviewResponse,
    ProjectStepCreate,
    ProjectStepRead,
    ProjectSuggestionRead,
    ProjectUpdate,
)
from app.repositories.project_repo import get_project_by_id
from app.schemas.planning import SprintRead
from sqlalchemy import select
from app.models.planning import Sprint, SprintPlan

router = APIRouter()


@router.post("/projects", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate, db: AsyncSession = Depends(get_db)
) -> ProjectRead:
    project = await project_crud.create_project(db, payload)
    await db.commit()
    return project


@router.get("/projects", response_model=list[ProjectRead])
async def list_projects(db: AsyncSession = Depends(get_db)) -> list[ProjectRead]:
    projects = await project_crud.list_projects(db)
    return list(projects)


@router.get("/projects/{project_id}/sprints", response_model=list[SprintRead])
async def list_project_sprints(project_id: int, db: AsyncSession = Depends(get_db)) -> list[SprintRead]:
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    result = await db.execute(
        select(Sprint).join(SprintPlan, Sprint.sprint_plan_id == SprintPlan.id).where(SprintPlan.project_id == project_id)
    )
    return list(result.scalars().all())


@router.post(
    "/projects/{project_id}/steps",
    response_model=ProjectStepRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_project_step(
    project_id: int,
    payload: ProjectStepCreate,
    db: AsyncSession = Depends(get_db),
) -> ProjectStepRead:
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    step = await project_crud.create_project_step(db, project_id, payload)
    await db.commit()
    return step


@router.get("/projects/{project_id}/steps", response_model=list[ProjectStepRead])
async def list_project_steps(
    project_id: int, db: AsyncSession = Depends(get_db)
) -> list[ProjectStepRead]:
    steps = await project_crud.list_project_steps(db, project_id)
    return list(steps)


@router.patch("/projects/{project_id}", response_model=ProjectRead)
async def patch_project(
    project_id: int,
    payload: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    project = await project_crud.update_project(db, project_id, payload)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.commit()
    return project


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db)) -> Response:
    project = await project_crud.soft_delete_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Project Suggestion Endpoints
from app.services.project_suggestion_service import (
    generate_initial_suggestions,
    review_and_expand_suggestions,
)
from app.models.project import Project, ProjectSuggestion


@router.post(
    "/projects/{project_id}/suggestions/generate",
    response_model=list[ProjectSuggestionRead],
)
async def generate_project_suggestions(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate initial AI suggestions for project creation.

    Called when user clicks "Öneri ver" button.
    """
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.description or len(project.description.strip()) < 20:
        raise HTTPException(
            status_code=400,
            detail="Proje amacı en az 20 karakter olmalıdır"
        )

    try:
        suggestions = await generate_initial_suggestions(db, project)
        await db.commit()
        return [ProjectSuggestionRead.model_validate(s) for s in suggestions]
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Öneri üretilirken hata oluştu: {str(e)}"
        )


@router.post(
    "/projects/{project_id}/suggestions/review",
    response_model=ProjectReviewResponse,
)
async def review_project_suggestions(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Review existing suggestions and generate new ones.

    Called when user clicks "Kontrol ve yenilik" button.
    """
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        result = await review_and_expand_suggestions(db, project)
        await db.commit()

        return ProjectReviewResponse(
            reviews=result["reviews"],
            new_suggestions=[
                ProjectSuggestionRead.model_validate(s)
                for s in result["new_suggestions"]
            ],
            overall_feedback=result["overall_feedback"],
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Kontrol sırasında hata oluştu: {str(e)}"
        )


@router.get(
    "/projects/{project_id}/suggestions",
    response_model=list[ProjectSuggestionRead],
)
async def get_project_suggestions(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all suggestions for a project."""
    result = await db.execute(
        select(ProjectSuggestion).where(
            ProjectSuggestion.project_id == project_id,
            ProjectSuggestion.is_deleted == False,  # noqa: E712
        )
    )
    suggestions = result.scalars().all()
    return [ProjectSuggestionRead.model_validate(s) for s in suggestions]


class AddExampleRequest(BaseModel):
    example_text: str


@router.post("/projects/{project_id}/suggestions/{suggestion_id}/add-example")
async def mark_example_as_added(
    project_id: int,
    suggestion_id: int,
    body: AddExampleRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Mark an example from a suggestion as added to the project description.
    This prevents the same suggestion from appearing again in review.
    """
    suggestion = await db.get(ProjectSuggestion, suggestion_id)
    if not suggestion or suggestion.project_id != project_id:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    # Add to user_added_examples list
    if suggestion.user_added_examples is None:
        suggestion.user_added_examples = []

    if body.example_text not in suggestion.user_added_examples:
        suggestion.user_added_examples.append(body.example_text)

    await db.commit()
    await db.refresh(suggestion)

    return ProjectSuggestionRead.model_validate(suggestion)


@router.post("/projects/{project_id}/suggestions/{suggestion_id}/expand")
async def expand_single_suggestion(
    project_id: int,
    suggestion_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Expand a single suggestion into 3 detailed versions.
    Returns the original suggestion with expanded_suggestions populated.
    """
    from app.services.project_suggestion_service import expand_suggestion

    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    suggestion = await db.get(ProjectSuggestion, suggestion_id)
    if not suggestion or suggestion.project_id != project_id:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    try:
        expanded = await expand_suggestion(db, project, suggestion)
        await db.commit()
        return {"expanded_suggestions": [ProjectSuggestionRead.model_validate(s) for s in expanded]}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Detaylandırma hatası: {str(e)}")
