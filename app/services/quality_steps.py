from datetime import datetime, timezone
from typing import List, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ApprovalStatus, StepStatus, StepType
from app.models.quality import DoDItem, NFRItem, RiskItem
from app.models.project import Project
from app.schemas.llm.quality import QualityLLMResponse
from app.services.llm_adapter import LLMError, call_llm
from app.services.llm_logs import log_llm_call
from app.services.project_steps import change_step_status, get_or_create_step
from app.services.prompts import build_quality_prompt


async def _load_project(db: AsyncSession, project_id: int) -> Project:
    project = await db.get(Project, project_id)
    if not project:
        raise ValueError("Project not found")
    return project


async def run_quality_steps(
    db: AsyncSession, project_id: int
) -> Tuple[List[DoDItem], List[NFRItem], List[RiskItem]]:
    project = await _load_project(db, project_id)
    step = await get_or_create_step(db, project_id, StepType.DOD)
    await _move_step_to_in_progress(step)

    await _soft_delete_unselected_quality(db, project_id)
    selected_dod, selected_nfr, selected_risk = await _get_selected_quality(db, project_id)

    prompt = build_quality_prompt(
        project,
        selected_dod=selected_dod,
        selected_nfr=selected_nfr,
        selected_risks=selected_risk,
    )
    try:
        response = await call_llm(prompt, QualityLLMResponse, db=db, project_id=project_id, step_type=StepType.DOD.value)
    except LLMError:
        await db.rollback()
        raise

    dod_items: list[DoDItem] = []
    nfr_items: list[NFRItem] = []
    risk_items: list[RiskItem] = []

    for item in response.dod_items:
        d = DoDItem(
            project_id=project_id,
            category=item.category,
            description=item.description,
            test_method=item.test_method,
            done_when=item.done_when,
            priority=item.priority,
            is_selected=False,
        )
        _apply_decision_support(d, item)
        db.add(d)
        dod_items.append(d)

    for item in response.nfr_items:
        n = NFRItem(
            project_id=project_id,
            type=item.type,
            description=item.description,
            measurable_target=item.measurable_target,
            is_selected=False,
        )
        _apply_decision_support(n, item)
        db.add(n)
        nfr_items.append(n)

    for item in response.risks:
        r = RiskItem(
            project_id=project_id,
            description=item.description,
            impact=item.impact,
            likelihood=item.likelihood,
            mitigation=item.mitigation,
            is_selected=False,
        )
        _apply_decision_support(r, item)
        db.add(r)
        risk_items.append(r)

    await db.flush()
    step.last_ai_run_at = datetime.now(timezone.utc)
    step.approval_status = ApprovalStatus.PENDING
    step.last_approved_at = None
    await change_step_status(step, StepStatus.COMPLETED)
    await db.commit()
    return dod_items, nfr_items, risk_items


async def _list_quality(db: AsyncSession, project_id: int):
    dod = (await db.execute(select(DoDItem).where(DoDItem.project_id == project_id, DoDItem.is_deleted == False))).scalars().all()  # noqa: E712
    nfr = (await db.execute(select(NFRItem).where(NFRItem.project_id == project_id, NFRItem.is_deleted == False))).scalars().all()  # noqa: E712
    risk = (await db.execute(select(RiskItem).where(RiskItem.project_id == project_id, RiskItem.is_deleted == False))).scalars().all()  # noqa: E712
    return dod, nfr, risk


async def _soft_delete_unselected_quality(db: AsyncSession, project_id: int):
    dod_unselected = (
        await db.execute(
            select(DoDItem).where(
                DoDItem.project_id == project_id,
                DoDItem.is_selected == False,  # noqa: E712
                DoDItem.is_deleted == False,  # noqa: E712
            )
        )
    ).scalars().all()
    nfr_unselected = (
        await db.execute(
            select(NFRItem).where(
                NFRItem.project_id == project_id,
                NFRItem.is_selected == False,  # noqa: E712
                NFRItem.is_deleted == False,  # noqa: E712
            )
        )
    ).scalars().all()
    risk_unselected = (
        await db.execute(
            select(RiskItem).where(
                RiskItem.project_id == project_id,
                RiskItem.is_selected == False,  # noqa: E712
                RiskItem.is_deleted == False,  # noqa: E712
            )
        )
    ).scalars().all()

    for item in [*dod_unselected, *nfr_unselected, *risk_unselected]:
        item.is_deleted = True
        item.deleted_at = datetime.now(timezone.utc)
    await db.flush()


async def _get_selected_quality(db: AsyncSession, project_id: int):
    dod_selected = (
        await db.execute(
            select(DoDItem).where(
                DoDItem.project_id == project_id,
                DoDItem.is_selected == True,  # noqa: E712
                DoDItem.is_deleted == False,  # noqa: E712
            )
        )
    ).scalars().all()
    nfr_selected = (
        await db.execute(
            select(NFRItem).where(
                NFRItem.project_id == project_id,
                NFRItem.is_selected == True,  # noqa: E712
                NFRItem.is_deleted == False,  # noqa: E712
            )
        )
    ).scalars().all()
    risk_selected = (
        await db.execute(
            select(RiskItem).where(
                RiskItem.project_id == project_id,
                RiskItem.is_selected == True,  # noqa: E712
                RiskItem.is_deleted == False,  # noqa: E712
            )
        )
    ).scalars().all()
    return dod_selected, nfr_selected, risk_selected


def _apply_decision_support(model_obj, item):
    fields = [
        "priority_score",
        "impact_level",
        "recommendation_type",
        "category_tags",
        "rationale",
        "advantages",
        "disadvantages",
        "conflicts_with",
        "requires",
        "category_exclusive",
    ]
    for field in fields:
        if hasattr(model_obj, field):
            setattr(model_obj, field, getattr(item, field, getattr(model_obj, field, None)))


async def _move_step_to_in_progress(step):
    if step.status == StepStatus.PLANNED:
        await change_step_status(step, StepStatus.IN_PROGRESS)
    elif step.status == StepStatus.COMPLETED:
        await change_step_status(step, StepStatus.STALE)
        await change_step_status(step, StepStatus.IN_PROGRESS)
    elif step.status == StepStatus.STALE:
        await change_step_status(step, StepStatus.IN_PROGRESS)
    else:
        return
