from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ApprovalStatus
from app.db.session import get_db
from app.models.imports import Comment
from app.models.planning import Epic, SprintPlan
from app.models.project import Project
from app.repositories.project_repo import get_project_by_id

router = APIRouter()


class RejectPayload(BaseModel):
    feedback: str


class ApprovalResponse(BaseModel):
    project_id: int
    entity_type: str
    entity_id: int
    approval_status: str
    last_approved_at: Optional[datetime] = None
    message: str


class SprintPlanApprovalResponse(BaseModel):
    project_id: int
    sprint_plan_id: int
    approval_status: str
    spec_locked: bool
    last_approved_at: Optional[datetime] = None
    message: str


async def _get_epic(
    db: AsyncSession, project_id: int, epic_id: int
) -> Epic:
    """Get Epic or raise 404"""
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(
        select(Epic).where(
            Epic.id == epic_id,
            Epic.project_id == project_id
        )
    )
    epic = result.scalars().first()
    if not epic:
        raise HTTPException(
            status_code=404, detail=f"Epic {epic_id} not found for this project"
        )
    return epic


async def _get_active_sprint_plan(
    db: AsyncSession, project_id: int
) -> SprintPlan:
    """Get active SprintPlan or raise 404"""
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(
        select(SprintPlan).where(
            SprintPlan.project_id == project_id,
            SprintPlan.is_active == True
        ).order_by(SprintPlan.created_at.desc())
    )
    sprint_plan = result.scalars().first()
    if not sprint_plan:
        raise HTTPException(
            status_code=404, detail="No active sprint plan found for this project"
        )
    return sprint_plan


@router.post("/projects/{project_id}/epics/{epic_id}/approve")
async def approve_epic(
    project_id: int,
    epic_id: int,
    db: AsyncSession = Depends(get_db),
) -> ApprovalResponse:
    """
    Approve an epic.
    Sets approval_status to APPROVED and records approval timestamp.
    """
    epic = await _get_epic(db, project_id, epic_id)

    # Approve
    epic.approval_status = ApprovalStatus.APPROVED
    epic.last_approved_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(epic)

    return ApprovalResponse(
        project_id=project_id,
        entity_type="epic",
        entity_id=epic_id,
        approval_status=epic.approval_status.value,
        last_approved_at=epic.last_approved_at,
        message=f"Epic '{epic.name}' approved successfully",
    )


@router.post("/projects/{project_id}/epics/{epic_id}/reject")
async def reject_epic(
    project_id: int,
    epic_id: int,
    payload: RejectPayload,
    db: AsyncSession = Depends(get_db),
) -> ApprovalResponse:
    """
    Reject an epic with feedback.
    Sets approval_status to REJECTED and stores feedback as a Comment.
    """
    epic = await _get_epic(db, project_id, epic_id)

    # Reject
    epic.approval_status = ApprovalStatus.REJECTED
    epic.last_approved_at = None

    # Save feedback as Comment
    comment = Comment(
        project_id=project_id,
        entity_type=f"epic",
        entity_id=epic_id,
        author="user",
        text=payload.feedback,
    )
    db.add(comment)

    await db.commit()
    await db.refresh(epic)

    return ApprovalResponse(
        project_id=project_id,
        entity_type="epic",
        entity_id=epic_id,
        approval_status=epic.approval_status.value,
        last_approved_at=None,
        message=f"Epic '{epic.name}' rejected with feedback",
    )


@router.post("/projects/{project_id}/sprint-plan/approve")
async def approve_sprint_plan(
    project_id: int,
    db: AsyncSession = Depends(get_db),
) -> SprintPlanApprovalResponse:
    """
    Approve the active sprint plan.
    Sets approval_status to APPROVED and LOCKS the project spec.
    """
    sprint_plan = await _get_active_sprint_plan(db, project_id)
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Approve sprint plan
    sprint_plan.approval_status = ApprovalStatus.APPROVED
    sprint_plan.last_approved_at = datetime.now(timezone.utc)

    # Lock project spec
    project.spec_locked = True
    project.spec_locked_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(sprint_plan)
    await db.refresh(project)

    return SprintPlanApprovalResponse(
        project_id=project_id,
        sprint_plan_id=sprint_plan.id,
        approval_status=sprint_plan.approval_status.value,
        spec_locked=project.spec_locked,
        last_approved_at=sprint_plan.last_approved_at,
        message=f"Sprint plan '{sprint_plan.name}' approved and project spec locked",
    )


@router.post("/projects/{project_id}/sprint-plan/reject")
async def reject_sprint_plan(
    project_id: int,
    payload: RejectPayload,
    db: AsyncSession = Depends(get_db),
) -> SprintPlanApprovalResponse:
    """
    Reject the active sprint plan with feedback.
    Sets approval_status to REJECTED and stores feedback as a Comment.
    """
    sprint_plan = await _get_active_sprint_plan(db, project_id)

    # Reject
    sprint_plan.approval_status = ApprovalStatus.REJECTED
    sprint_plan.last_approved_at = None

    # Save feedback as Comment
    comment = Comment(
        project_id=project_id,
        entity_type="sprint_plan",
        entity_id=sprint_plan.id,
        author="user",
        text=payload.feedback,
    )
    db.add(comment)

    await db.commit()
    await db.refresh(sprint_plan)

    return SprintPlanApprovalResponse(
        project_id=project_id,
        sprint_plan_id=sprint_plan.id,
        approval_status=sprint_plan.approval_status.value,
        spec_locked=False,
        last_approved_at=None,
        message=f"Sprint plan '{sprint_plan.name}' rejected with feedback",
    )
