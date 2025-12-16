from typing import List

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ApprovalStatus, StepStatus, StepType
from app.models.planning import Epic, EpicDependency
from app.models.project import ArchitectureComponent, Feature, Project
from app.services.project_steps import change_step_status, get_or_create_step


async def generate_epics_for_project(db: AsyncSession, project: Project) -> List[Epic]:
    """
    Basit heuristik: Feature ve Architecture component'larından Epic üretir.
    Clear & regenerate stratejisi kullanılır: mevcut epics/deps silinir.
    """
    # Clear existing epics/dependencies
    await db.execute(delete(EpicDependency).where(EpicDependency.project_id == project.id))
    await db.execute(delete(Epic).where(Epic.project_id == project.id))

    step = await get_or_create_step(db, project.id, StepType.EPICS)
    if step.status == StepStatus.PLANNED:
        await change_step_status(step, StepStatus.IN_PROGRESS)

    epics: list[Epic] = []

    features = (
        await db.execute(select(Feature).where(Feature.project_id == project.id))
    ).scalars().all()
    components = (
        await db.execute(
            select(ArchitectureComponent).where(ArchitectureComponent.project_id == project.id)
        )
    ).scalars().all()

    # Platform/infra epics from architecture
    for comp in components:
        category = _infer_category_from_component(comp)
        epic = Epic(
            project_id=project.id,
            name=f"Altyapı: {comp.name}" if category == "platform" else comp.name,
            description=comp.description or f"{comp.layer} bileşeni",
            related_component_ids=[comp.id],
            category=category,
            approval_status=ApprovalStatus.PENDING,
            last_approved_at=None,
        )
        db.add(epic)
        epics.append(epic)

    # Feature epics
    for feat in features:
        epic = Epic(
            project_id=project.id,
            name=feat.name,
            description=feat.description or "Özellik epik'i",
            related_feature_ids=[feat.id],
            category="feature",
            approval_status=ApprovalStatus.PENDING,
            last_approved_at=None,
        )
        db.add(epic)
        epics.append(epic)

    await db.flush()

    if step.status != StepStatus.COMPLETED:
        await change_step_status(step, StepStatus.COMPLETED)
    await db.commit()

    return epics


def _infer_category_from_component(comp: ArchitectureComponent) -> str:
    layer = (comp.layer or "").lower()
    name = (comp.name or "").lower()
    if "infra" in layer or "devops" in layer or "platform" in name or layer == "infra":
        return "platform"
    if "logging" in name or "monitor" in name or "observability" in name:
        return "quality"
    return "feature"
