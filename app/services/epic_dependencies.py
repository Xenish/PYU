from collections import defaultdict, deque
from typing import List

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.planning import Epic, EpicDependency


class EpicDependencyCycleError(Exception):
    pass


async def generate_epic_dependencies_for_project(
    db: AsyncSession, project_id: int
) -> List[EpicDependency]:
    """
    Basit heuristik: platform epik'leri diğerlerine bağımlılık olarak eklenir.
    Quality epikleri, platform ve feature'lara bağımlı olur.
    """
    await db.execute(delete(EpicDependency).where(EpicDependency.project_id == project_id))
    epics = (
        await db.execute(select(Epic).where(Epic.project_id == project_id))
    ).scalars().all()

    platform_epics = [e for e in epics if (e.category or "").lower() == "platform"]
    quality_epics = [e for e in epics if (e.category or "").lower() == "quality"]
    feature_epics = [e for e in epics if (e.category or "").lower() not in {"platform", "quality"}]

    deps: list[EpicDependency] = []

    # All non-platform epics depend on platform epics
    for feat in feature_epics + quality_epics:
        for plat in platform_epics:
            dep = EpicDependency(
                project_id=project_id, epic_id=feat.id, depends_on_epic_id=plat.id
            )
            db.add(dep)
            deps.append(dep)

    # Quality epics depend on all feature epics
    for qual in quality_epics:
        for feat in feature_epics:
            dep = EpicDependency(
                project_id=project_id, epic_id=qual.id, depends_on_epic_id=feat.id
            )
            db.add(dep)
            deps.append(dep)

    await db.flush()
    await db.commit()
    return deps


def topo_sort_epics(epics: list[Epic], deps: list[EpicDependency]) -> list[Epic]:
    graph = defaultdict(list)
    indegree = {e.id: 0 for e in epics}
    epic_map = {e.id: e for e in epics}

    for dep in deps:
        graph[dep.depends_on_epic_id].append(dep.epic_id)
        indegree[dep.epic_id] = indegree.get(dep.epic_id, 0) + 1

    queue = deque([eid for eid, deg in indegree.items() if deg == 0])
    ordered: list[Epic] = []

    while queue:
        eid = queue.popleft()
        if eid in epic_map:
            ordered.append(epic_map[eid])
        for nxt in graph[eid]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)

    if len(ordered) != len(epics):
        raise EpicDependencyCycleError("Cycle detected in epic dependencies")

    return ordered
