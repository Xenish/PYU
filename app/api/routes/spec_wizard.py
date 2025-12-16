from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.enums import ApprovalStatus, StepType, StepStatus
from app.db.session import get_db
from app.deps.spec_lock import ensure_project_unlocked
from app.models.project import Project, ProjectStep, ProjectObjective, TechStackOption, Feature, ArchitectureComponent
from app.models.quality import DoDItem, NFRItem, RiskItem
from app.schemas.spec_wizard import WizardDetail, WizardSummary, StepSummary
from app.services.objective_step import run_objective_step
from app.services.quality_steps import run_quality_steps
from app.services.spec_steps import (
    run_architecture_step,
    run_feature_step,
    run_tech_stack_step,
)

router = APIRouter()


async def _ensure_project(db: AsyncSession, project_id: int) -> Project:
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/projects/{project_id}/steps/objective/run")
async def run_objective(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _lock_guard: None = Depends(ensure_project_unlocked),
):
    await _ensure_project(db, project_id)
    objectives = await run_objective_step(db, project_id)
    return {"step_type": StepType.OBJECTIVE, "count": len(objectives)}


@router.post("/projects/{project_id}/steps/tech-stack/run")
async def run_tech_stack(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _lock_guard: None = Depends(ensure_project_unlocked),
):
    await _ensure_project(db, project_id)
    options = await run_tech_stack_step(db, project_id)
    return {"step_type": StepType.TECH_STACK, "count": len(options)}


@router.post("/projects/{project_id}/steps/features/run")
async def run_features(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _lock_guard: None = Depends(ensure_project_unlocked),
):
    await _ensure_project(db, project_id)
    feats = await run_feature_step(db, project_id)
    return {"step_type": StepType.FEATURES, "count": len(feats)}


@router.post("/projects/{project_id}/steps/architecture/run")
async def run_architecture(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _lock_guard: None = Depends(ensure_project_unlocked),
):
    await _ensure_project(db, project_id)
    comps = await run_architecture_step(db, project_id)
    return {"step_type": StepType.ARCHITECTURE, "count": len(comps)}


@router.post("/projects/{project_id}/steps/quality/run")
async def run_quality(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _lock_guard: None = Depends(ensure_project_unlocked),
):
    await _ensure_project(db, project_id)
    dod, nfr, risks = await run_quality_steps(db, project_id)
    return {"step_type": StepType.DOD, "dod": len(dod), "nfr": len(nfr), "risks": len(risks)}


async def _get_step_summary(db: AsyncSession, project_id: int, step_type: StepType) -> StepSummary:
    step = (
        await db.execute(
            select(ProjectStep).where(
                ProjectStep.project_id == project_id, ProjectStep.step_type == step_type
            )
        )
    ).scalars().first()
    status = step.status if step else StepStatus.PLANNED
    approval_status = step.approval_status if step else None
    last_ai_run_at = step.last_ai_run_at if step else None
    last_approved_at = step.last_approved_at if step else None

    summary = ""
    count = 0
    if step_type == StepType.OBJECTIVE:
        objs = (
            await db.execute(
                select(ProjectObjective).where(ProjectObjective.project_id == project_id, ProjectObjective.is_deleted == False)  # noqa: E712
            )
        ).scalars().all()
        count = len(objs)
        if objs:
            summary = objs[0].title
    elif step_type == StepType.TECH_STACK:
        stacks = (
            await db.execute(
                select(TechStackOption).where(TechStackOption.project_id == project_id, TechStackOption.is_deleted == False)  # noqa: E712
            )
        ).scalars().all()
        count = len(stacks)
        if stacks:
            names = []
            for section in ["frontend", "backend", "database", "infra"]:
                val = (stacks[0].__dict__.get(section) or {}).get("name")
                if val:
                    names.append(val)
            summary = ", ".join(names) if names else "Tech stack generated"
    elif step_type == StepType.FEATURES:
        feats = (
            await db.execute(
                select(Feature).where(Feature.project_id == project_id, Feature.is_deleted == False)  # noqa: E712
            )
        ).scalars().all()
        count = len(feats)
        if feats:
            summary = feats[0].name
    elif step_type == StepType.ARCHITECTURE:
        comps = (
            await db.execute(
                select(ArchitectureComponent).where(ArchitectureComponent.project_id == project_id, ArchitectureComponent.is_deleted == False)  # noqa: E712
            )
        ).scalars().all()
        count = len(comps)
        if comps:
            summary = comps[0].name
    elif step_type in (StepType.DOD, StepType.NFR, StepType.RISKS):
        dods = (
            await db.execute(
                select(DoDItem).where(DoDItem.project_id == project_id, DoDItem.is_deleted == False)  # noqa: E712
            )
        ).scalars().all()
        nfrs = (
            await db.execute(
                select(NFRItem).where(NFRItem.project_id == project_id, NFRItem.is_deleted == False)  # noqa: E712
            )
        ).scalars().all()
        risks = (
            await db.execute(
                select(RiskItem).where(RiskItem.project_id == project_id, RiskItem.is_deleted == False)  # noqa: E712
            )
        ).scalars().all()
        count = len(dods) + len(nfrs) + len(risks)
        if dods:
            summary = dods[0].description
        elif nfrs:
            summary = nfrs[0].description
        elif risks:
            summary = risks[0].description

    return StepSummary(
        step_type=step_type,
        status=status,
        approval_status=approval_status,
        last_ai_run_at=last_ai_run_at,
        last_approved_at=last_approved_at,
        summary=summary,
        item_count=count,
    )


@router.get("/projects/{project_id}/spec-wizard/summary", response_model=WizardSummary)
async def get_spec_wizard_summary(project_id: int, db: AsyncSession = Depends(get_db)):
    await _ensure_project(db, project_id)
    step_types = [
        StepType.OBJECTIVE,
        StepType.TECH_STACK,
        StepType.FEATURES,
        StepType.ARCHITECTURE,
        StepType.DOD,
    ]
    steps = []
    for st in step_types:
        steps.append(await _get_step_summary(db, project_id, st))
    return WizardSummary(project_id=project_id, steps=steps)


@router.get("/projects/{project_id}/spec-wizard/detail", response_model=WizardDetail)
async def get_spec_wizard_detail(project_id: int, db: AsyncSession = Depends(get_db)):
    await _ensure_project(db, project_id)
    for st in [
        StepType.OBJECTIVE,
        StepType.TECH_STACK,
        StepType.FEATURES,
        StepType.ARCHITECTURE,
        StepType.DOD,
    ]:
        await _ensure_selection_compatibility(db, project_id, st)
    objectives = (
        await db.execute(
            select(ProjectObjective).where(ProjectObjective.project_id == project_id, ProjectObjective.is_deleted == False)  # noqa: E712
        )
    ).scalars().all()
    stacks = (
        await db.execute(
            select(TechStackOption).where(TechStackOption.project_id == project_id, TechStackOption.is_deleted == False)  # noqa: E712
        )
    ).scalars().all()
    feats = (
        await db.execute(
            select(Feature).where(Feature.project_id == project_id, Feature.is_deleted == False)  # noqa: E712
        )
    ).scalars().all()
    comps = (
        await db.execute(
            select(ArchitectureComponent).where(ArchitectureComponent.project_id == project_id, ArchitectureComponent.is_deleted == False)  # noqa: E712
        )
    ).scalars().all()
    dods = (
        await db.execute(
            select(DoDItem).where(DoDItem.project_id == project_id, DoDItem.is_deleted == False)  # noqa: E712
        )
    ).scalars().all()
    nfrs = (
        await db.execute(
            select(NFRItem).where(NFRItem.project_id == project_id, NFRItem.is_deleted == False)  # noqa: E712
        )
    ).scalars().all()
    risks = (
        await db.execute(
            select(RiskItem).where(RiskItem.project_id == project_id, RiskItem.is_deleted == False)  # noqa: E712
        )
    ).scalars().all()
    # convert to dict payloads for UI readability
    obj_payload = [
        {
            "id": o.id,
            "title": o.title,
            "text": o.text,
            "is_selected": o.is_selected,
            "priority_score": o.priority_score,
            "impact_level": o.impact_level,
            "recommendation_type": o.recommendation_type,
            "category_tags": o.category_tags,
            "rationale": o.rationale,
            "advantages": o.advantages,
            "disadvantages": o.disadvantages,
            "conflicts_with": o.conflicts_with,
            "requires": o.requires,
            "category_exclusive": o.category_exclusive,
        }
        for o in objectives
    ]
    stack_payload = [
        {
            "id": s.id,
            "frontend": s.frontend,
            "backend": s.backend,
            "database": s.database,
            "infra": s.infra,
            "analytics": s.analytics,
            "ci_cd": s.ci_cd,
            "is_selected": s.is_selected,
            "priority_score": s.priority_score,
            "impact_level": s.impact_level,
            "recommendation_type": s.recommendation_type,
            "category_tags": s.category_tags,
            "rationale": s.rationale,
            "advantages": s.advantages,
            "disadvantages": s.disadvantages,
            "conflicts_with": s.conflicts_with,
            "requires": s.requires,
            "category_exclusive": s.category_exclusive,
        }
        for s in stacks
    ]
    feat_payload = [
        {
            "id": f.id,
            "name": f.name,
            "description": f.description,
            "is_selected": f.is_selected,
            "priority_score": f.priority_score,
            "impact_level": f.impact_level,
            "recommendation_type": f.recommendation_type,
            "category_tags": f.category_tags,
            "rationale": f.rationale,
            "advantages": f.advantages,
            "disadvantages": f.disadvantages,
            "conflicts_with": f.conflicts_with,
            "requires": f.requires,
            "category_exclusive": f.category_exclusive,
        }
        for f in feats
    ]
    comp_payload = [
        {
            "id": c.id,
            "name": c.name,
            "layer": c.layer,
            "description": c.description,
            "is_selected": c.is_selected,
            "priority_score": c.priority_score,
            "impact_level": c.impact_level,
            "recommendation_type": c.recommendation_type,
            "category_tags": c.category_tags,
            "rationale": c.rationale,
            "advantages": c.advantages,
            "disadvantages": c.disadvantages,
            "conflicts_with": c.conflicts_with,
            "requires": c.requires,
            "category_exclusive": c.category_exclusive,
        }
        for c in comps
    ]
    dod_payload = [
        {
            "id": d.id,
            "description": d.description,
            "category": getattr(d, "category", None),
            "is_selected": d.is_selected,
            "priority_score": d.priority_score,
            "impact_level": d.impact_level,
            "recommendation_type": d.recommendation_type,
            "category_tags": d.category_tags,
            "rationale": d.rationale,
            "advantages": d.advantages,
            "disadvantages": d.disadvantages,
            "conflicts_with": d.conflicts_with,
            "requires": d.requires,
            "category_exclusive": d.category_exclusive,
        }
        for d in dods
    ]
    nfr_payload = [
        {
            "id": n.id,
            "type": n.type,
            "description": n.description,
            "is_selected": n.is_selected,
            "priority_score": n.priority_score,
            "impact_level": n.impact_level,
            "recommendation_type": n.recommendation_type,
            "category_tags": n.category_tags,
            "rationale": n.rationale,
            "advantages": n.advantages,
            "disadvantages": n.disadvantages,
            "conflicts_with": n.conflicts_with,
            "requires": n.requires,
            "category_exclusive": n.category_exclusive,
        }
        for n in nfrs
    ]
    risk_payload = [
        {
            "id": r.id,
            "description": r.description,
            "is_selected": r.is_selected,
            "priority_score": r.priority_score,
            "impact_level": r.impact_level,
            "recommendation_type": r.recommendation_type,
            "category_tags": r.category_tags,
            "rationale": r.rationale,
            "advantages": r.advantages,
            "disadvantages": r.disadvantages,
            "conflicts_with": r.conflicts_with,
            "requires": r.requires,
            "category_exclusive": r.category_exclusive,
        }
        for r in risks
    ]

    return WizardDetail(
        project_id=project_id,
        objectives=obj_payload,
        tech_stack=stack_payload,
        features=feat_payload,
        architecture=comp_payload,
        dod_items=dod_payload,
        nfr_items=nfr_payload,
        risk_items=risk_payload,
    )


async def _ensure_selection_compatibility(
    db: AsyncSession, project_id: int, step_type: StepType
) -> None:
    """
    For approved steps with no selections, mark all items as selected.
    Ensures backward compatibility with pre-item-selection projects.
    """
    step_result = await db.execute(
        select(ProjectStep).where(
            ProjectStep.project_id == project_id, ProjectStep.step_type == step_type
        )
    )
    step = step_result.scalars().first()
    if not step or step.approval_status != ApprovalStatus.APPROVED:
        return

    step_to_models = {
        StepType.OBJECTIVE: [ProjectObjective],
        StepType.TECH_STACK: [TechStackOption],
        StepType.FEATURES: [Feature],
        StepType.ARCHITECTURE: [ArchitectureComponent],
        StepType.DOD: [DoDItem, NFRItem, RiskItem],
        StepType.NFR: [NFRItem],
        StepType.RISKS: [RiskItem],
    }
    models = step_to_models.get(step_type, [])
    if not models:
        return

    items_to_select = []
    selected_exists = False
    for model in models:
        result = await db.execute(
            select(model).where(
                model.project_id == project_id,
                model.is_deleted == False,  # noqa: E712
            )
        )
        items = result.scalars().all()
        for item in items:
            if item.is_selected:
                selected_exists = True
            else:
                items_to_select.append(item)

    if selected_exists or not items_to_select:
        return

    for item in items_to_select:
        item.is_selected = True

    await db.commit()
