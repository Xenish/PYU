from collections import defaultdict
from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.planning import Epic, Sprint, SprintEpic, SprintPlan
from app.models.quality import DoDItem, NFRItem


async def build_sprint_quality_summaries(
    db: AsyncSession, sprint_plan: SprintPlan
) -> Dict[int, dict]:
    """Basit kalite özeti: DoD sayısı ve NFR kategorileri."""
    sprints = (
        await db.execute(select(Sprint).where(Sprint.sprint_plan_id == sprint_plan.id))
    ).scalars().all()
    sprint_ids = [s.id for s in sprints]
    sprint_epics = (
        await db.execute(select(SprintEpic).where(SprintEpic.sprint_id.in_(sprint_ids)))
    ).scalars().all()
    epic_ids = [se.epic_id for se in sprint_epics]

    epics = (
        await db.execute(select(Epic).where(Epic.id.in_(epic_ids)))
    ).scalars().all()
    epics_by_id = {e.id: e for e in epics}

    dod_items = (
        await db.execute(select(DoDItem).where(DoDItem.project_id == sprint_plan.project_id))
    ).scalars().all()
    nfr_items = (
        await db.execute(select(NFRItem).where(NFRItem.project_id == sprint_plan.project_id))
    ).scalars().all()

    summary: Dict[int, dict] = defaultdict(lambda: {"dod_count": 0, "nfr_categories": set()})
    for se in sprint_epics:
        epic = epics_by_id.get(se.epic_id)
        if not epic:
            continue
        # simplistic: all DoD/NFR apply; count DoD, collect NFR categories
        summary[se.sprint_id]["dod_count"] = len(dod_items)
        summary[se.sprint_id]["nfr_categories"].update([n.type for n in nfr_items])

    # convert sets to lists
    return {
        sprint_id: {"dod_count": data["dod_count"], "nfr_categories": list(data["nfr_categories"])}
        for sprint_id, data in summary.items()
    }
