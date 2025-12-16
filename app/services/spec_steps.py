from datetime import datetime, timezone
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ApprovalStatus, StepStatus, StepType
from app.models.project import Feature, Project, TechStackOption, ArchitectureComponent
from app.schemas.llm.architecture import ArchitectureLLMResponse
from app.schemas.llm.features import FeatureLLMResponse
from app.schemas.llm.tech_stack import TechStackLLMResponse
from app.services.llm_adapter import LLMError, call_llm
from app.services.llm_logs import log_llm_call
from app.services.project_steps import change_step_status, get_or_create_step
from app.services.prompts import (
    build_architecture_prompt,
    build_feature_prompt,
    build_tech_stack_prompt,
)


async def _load_project(db: AsyncSession, project_id: int) -> Project:
    project = await db.get(Project, project_id)
    if not project:
        raise ValueError("Project not found")
    return project


async def run_tech_stack_step(db: AsyncSession, project_id: int) -> List[TechStackOption]:
    project = await _load_project(db, project_id)
    step = await get_or_create_step(db, project_id, StepType.TECH_STACK)
    await _move_step_to_in_progress(step)

    await _soft_delete_unselected_options(db, project_id)
    selected_options = await _get_selected_options(db, project_id)

    prompt = build_tech_stack_prompt(project, selected_items=selected_options)
    try:
        response = await call_llm(prompt, TechStackLLMResponse, db=db, project_id=project_id, step_type=StepType.TECH_STACK.value)
    except LLMError:
        await db.rollback()
        raise

    options: list[TechStackOption] = []
    for item in response.items:
        opt = TechStackOption(
            project_id=project_id,
            notes=item.rationale,
            frontend={"name": item.name} if item.category == "frontend" else None,
            backend={"name": item.name} if item.category == "backend" else None,
            database={"name": item.name} if item.category == "db" else None,
            infra={"name": item.name} if item.category == "infra" else None,
            analytics={"name": item.name} if item.category == "analytics" else None,
            ci_cd={"name": item.name} if item.category == "ci_cd" else None,
            is_selected=False,
        )
        _apply_decision_support(opt, item)
        db.add(opt)
        options.append(opt)
    await db.flush()

    step.last_ai_run_at = datetime.now(timezone.utc)
    step.approval_status = ApprovalStatus.PENDING
    step.last_approved_at = None
    await change_step_status(step, StepStatus.COMPLETED)
    await db.commit()
    return options


async def run_feature_step(db: AsyncSession, project_id: int) -> List[Feature]:
    project = await _load_project(db, project_id)
    step = await get_or_create_step(db, project_id, StepType.FEATURES)
    await _move_step_to_in_progress(step)

    await _soft_delete_unselected_features(db, project_id)
    selected_features = await _get_selected_features(db, project_id)

    prompt = build_feature_prompt(project, selected_items=selected_features)
    try:
        response = await call_llm(prompt, FeatureLLMResponse, db=db, project_id=project_id, step_type=StepType.FEATURES.value)
    except LLMError:
        await db.rollback()
        raise

    features: list[Feature] = []
    for item in response.features:
        feat = Feature(
            project_id=project_id,
            name=item.title,
            description=item.description,
            type=item.feature_type,
            group=item.group,
            is_selected=False,
        )
        _apply_decision_support(feat, item)
        db.add(feat)
        features.append(feat)
    await db.flush()

    step.last_ai_run_at = datetime.now(timezone.utc)
    step.approval_status = ApprovalStatus.PENDING
    step.last_approved_at = None
    await change_step_status(step, StepStatus.COMPLETED)
    await db.commit()
    return features


async def run_architecture_step(db: AsyncSession, project_id: int) -> List[ArchitectureComponent]:
    project = await _load_project(db, project_id)
    step = await get_or_create_step(db, project_id, StepType.ARCHITECTURE)
    await _move_step_to_in_progress(step)

    await _soft_delete_unselected_architecture(db, project_id)
    selected_arch = await _get_selected_architecture(db, project_id)

    prompt = build_architecture_prompt(project, selected_items=selected_arch)
    try:
        response = await call_llm(prompt, ArchitectureLLMResponse, db=db, project_id=project_id, step_type=StepType.ARCHITECTURE.value)
    except LLMError:
        await db.rollback()
        raise

    comps: list[ArchitectureComponent] = []
    for item in response.components:
        comp = ArchitectureComponent(
            project_id=project_id,
            name=item.name,
            layer=item.layer,
            description=item.description,
            responsibilities=item.responsibilities,
            is_selected=False,
        )
        _apply_decision_support(comp, item)
        db.add(comp)
        comps.append(comp)
    await db.flush()

    step.last_ai_run_at = datetime.now(timezone.utc)
    step.approval_status = ApprovalStatus.PENDING
    step.last_approved_at = None
    await change_step_status(step, StepStatus.COMPLETED)
    await db.commit()
    return comps


async def _list_options(db: AsyncSession, project_id: int):
    result = await db.execute(
        select(TechStackOption).where(
            TechStackOption.project_id == project_id,
            TechStackOption.is_deleted == False,  # noqa: E712
        )
    )
    return result.scalars().all()


async def _list_features(db: AsyncSession, project_id: int):
    result = await db.execute(
        select(Feature).where(
            Feature.project_id == project_id,
            Feature.is_deleted == False,  # noqa: E712
        )
    )
    return result.scalars().all()


async def _list_architecture(db: AsyncSession, project_id: int):
    result = await db.execute(
        select(ArchitectureComponent).where(
            ArchitectureComponent.project_id == project_id,
            ArchitectureComponent.is_deleted == False,  # noqa: E712
        )
    )
    return result.scalars().all()


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


async def _soft_delete_unselected_options(db: AsyncSession, project_id: int):
    result = await db.execute(
        select(TechStackOption).where(
            TechStackOption.project_id == project_id,
            TechStackOption.is_selected == False,  # noqa: E712
            TechStackOption.is_deleted == False,  # noqa: E712
        )
    )
    for item in result.scalars().all():
        item.is_deleted = True
        item.deleted_at = datetime.now(timezone.utc)
    await db.flush()


async def _get_selected_options(db: AsyncSession, project_id: int):
    result = await db.execute(
        select(TechStackOption).where(
            TechStackOption.project_id == project_id,
            TechStackOption.is_selected == True,  # noqa: E712
            TechStackOption.is_deleted == False,  # noqa: E712
        )
    )
    return result.scalars().all()


async def _soft_delete_unselected_features(db: AsyncSession, project_id: int):
    result = await db.execute(
        select(Feature).where(
            Feature.project_id == project_id,
            Feature.is_selected == False,  # noqa: E712
            Feature.is_deleted == False,  # noqa: E712
        )
    )
    for item in result.scalars().all():
        item.is_deleted = True
        item.deleted_at = datetime.now(timezone.utc)
    await db.flush()


async def _get_selected_features(db: AsyncSession, project_id: int):
    result = await db.execute(
        select(Feature).where(
            Feature.project_id == project_id,
            Feature.is_selected == True,  # noqa: E712
            Feature.is_deleted == False,  # noqa: E712
        )
    )
    return result.scalars().all()


async def _soft_delete_unselected_architecture(db: AsyncSession, project_id: int):
    result = await db.execute(
        select(ArchitectureComponent).where(
            ArchitectureComponent.project_id == project_id,
            ArchitectureComponent.is_selected == False,  # noqa: E712
            ArchitectureComponent.is_deleted == False,  # noqa: E712
        )
    )
    for item in result.scalars().all():
        item.is_deleted = True
        item.deleted_at = datetime.now(timezone.utc)
    await db.flush()


async def _get_selected_architecture(db: AsyncSession, project_id: int):
    result = await db.execute(
        select(ArchitectureComponent).where(
            ArchitectureComponent.project_id == project_id,
            ArchitectureComponent.is_selected == True,  # noqa: E712
            ArchitectureComponent.is_deleted == False,  # noqa: E712
        )
    )
    return result.scalars().all()


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
