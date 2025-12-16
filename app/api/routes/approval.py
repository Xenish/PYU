from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ApprovalStatus, StepStatus, StepType
from app.db.session import get_db
from app.models.imports import Comment
from app.models.project import (
    ArchitectureComponent,
    Feature,
    Project,
    ProjectObjective,
    ProjectStep,
    TechStackOption,
)
from app.models.quality import DoDItem, NFRItem, RiskItem
from app.repositories.project_repo import get_project_by_id
from app.services.objective_step import run_objective_step
from app.services.quality_steps import run_quality_steps
from app.services.spec_steps import (
    run_architecture_step,
    run_feature_step,
    run_tech_stack_step,
)

router = APIRouter()


class RejectPayload(BaseModel):
    feedback: str


class RegeneratePayload(BaseModel):
    feedback: Optional[str] = None


class ApprovalResponse(BaseModel):
    project_id: int
    step_type: str
    approval_status: str
    last_approved_at: Optional[datetime] = None
    message: str


async def _get_step(
    db: AsyncSession, project_id: int, step_type: StepType
) -> ProjectStep:
    """Get ProjectStep or raise 404"""
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(
        select(ProjectStep).where(
            ProjectStep.project_id == project_id, ProjectStep.step_type == step_type
        )
    )
    step = result.scalars().first()
    if not step:
        raise HTTPException(
            status_code=404, detail=f"Step {step_type} not found for this project"
        )
    return step


async def _count_selected_items(
    db: AsyncSession, project_id: int, step_type: StepType
) -> int:
    """Count selected items for a step type."""
    # DOD step generates 3 item types (DoD, NFR, Risk), so count all of them
    if step_type == StepType.DOD:
        dod_result = await db.execute(
            select(func.count())
            .select_from(DoDItem)
            .where(
                DoDItem.project_id == project_id,
                DoDItem.is_selected == True,  # noqa: E712
                DoDItem.is_deleted == False,  # noqa: E712
            )
        )
        nfr_result = await db.execute(
            select(func.count())
            .select_from(NFRItem)
            .where(
                NFRItem.project_id == project_id,
                NFRItem.is_selected == True,  # noqa: E712
                NFRItem.is_deleted == False,  # noqa: E712
            )
        )
        risk_result = await db.execute(
            select(func.count())
            .select_from(RiskItem)
            .where(
                RiskItem.project_id == project_id,
                RiskItem.is_selected == True,  # noqa: E712
                RiskItem.is_deleted == False,  # noqa: E712
            )
        )
        return (
            int(dod_result.scalar_one() or 0)
            + int(nfr_result.scalar_one() or 0)
            + int(risk_result.scalar_one() or 0)
        )

    step_to_model = {
        StepType.OBJECTIVE: ProjectObjective,
        StepType.TECH_STACK: TechStackOption,
        StepType.FEATURES: Feature,
        StepType.ARCHITECTURE: ArchitectureComponent,
        StepType.NFR: NFRItem,
        StepType.RISKS: RiskItem,
    }
    model = step_to_model.get(step_type)
    if not model:
        return 0

    result = await db.execute(
        select(func.count())
        .select_from(model)
        .where(
            model.project_id == project_id,
            model.is_selected == True,  # noqa: E712
            model.is_deleted == False,  # noqa: E712
        )
    )
    return int(result.scalar_one() or 0)


@router.post("/projects/{project_id}/steps/{step_type}/approve")
async def approve_step(
    project_id: int,
    step_type: StepType,
    db: AsyncSession = Depends(get_db),
) -> ApprovalResponse:
    """
    Approve a completed spec wizard step.
    Only items with is_selected=True are considered approved and at least one must be selected.
    """
    step = await _get_step(db, project_id, step_type)

    # Preconditions
    if step.status != StepStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Step must be COMPLETED to approve (current: {step.status})",
        )
    if step.approval_status == ApprovalStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Step is already approved")

    selected_count = await _count_selected_items(db, project_id, step_type)
    if selected_count == 0:
        raise HTTPException(
            status_code=400,
            detail="At least one item must be selected to approve this step",
        )

    # Approve
    step.approval_status = ApprovalStatus.APPROVED
    step.last_approved_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(step)

    return ApprovalResponse(
        project_id=project_id,
        step_type=step_type.value,
        approval_status=step.approval_status.value,
        last_approved_at=step.last_approved_at,
        message=f"Step {step_type.value} approved successfully",
    )


@router.post("/projects/{project_id}/steps/{step_type}/reject")
async def reject_step(
    project_id: int,
    step_type: StepType,
    payload: RejectPayload,
    db: AsyncSession = Depends(get_db),
) -> ApprovalResponse:
    """
    Reject a spec wizard step with feedback.
    Sets approval_status to REJECTED and stores feedback as a Comment.
    """
    step = await _get_step(db, project_id, step_type)

    # Preconditions
    if step.status != StepStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Step must be COMPLETED to reject (current: {step.status})",
        )

    # Reject
    step.approval_status = ApprovalStatus.REJECTED
    step.last_approved_at = None

    # Save feedback as Comment
    comment = Comment(
        project_id=project_id,
        entity_type=f"project_step_{step_type.value}",
        entity_id=step.id,
        author="user",  # V1: hardcoded, can be extended with auth later
        text=payload.feedback,
    )
    db.add(comment)

    await db.commit()
    await db.refresh(step)

    return ApprovalResponse(
        project_id=project_id,
        step_type=step_type.value,
        approval_status=step.approval_status.value,
        last_approved_at=None,
        message=f"Step {step_type.value} rejected with feedback",
    )


@router.post("/projects/{project_id}/steps/{step_type}/regenerate")
async def regenerate_step(
    project_id: int,
    step_type: StepType,
    payload: Optional[RegeneratePayload] = None,
    db: AsyncSession = Depends(get_db),
) -> ApprovalResponse:
    """
    Regenerate a rejected (or any) step by re-running the LLM.
    Optionally includes user feedback in the regeneration.
    """
    step = await _get_step(db, project_id, step_type)

    # Optional: save regeneration feedback as Comment if provided
    if payload and payload.feedback:
        comment = Comment(
            project_id=project_id,
            entity_type=f"project_step_{step_type.value}_regen",
            entity_id=step.id,
            author="user",
            text=payload.feedback,
        )
        db.add(comment)
        await db.flush()

    # Re-run the LLM step
    # Note: feedback integration into prompt is a future enhancement (V2)
    # For now, we just re-run the same prompt

    try:
        if step_type == StepType.OBJECTIVE:
            await run_objective_step(db, project_id)
        elif step_type == StepType.TECH_STACK:
            await run_tech_stack_step(db, project_id)
        elif step_type == StepType.FEATURES:
            await run_feature_step(db, project_id)
        elif step_type == StepType.ARCHITECTURE:
            await run_architecture_step(db, project_id)
        elif step_type in (StepType.DOD, StepType.NFR, StepType.RISKS):
            await run_quality_steps(db, project_id)
        else:
            raise HTTPException(
                status_code=400, detail=f"Regeneration not supported for {step_type}"
            )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {str(e)}")

    await db.refresh(step)

    return ApprovalResponse(
        project_id=project_id,
        step_type=step_type.value,
        approval_status=step.approval_status.value,
        last_approved_at=step.last_approved_at,
        message=f"Step {step_type.value} regenerated successfully (now PENDING approval)",
    )
