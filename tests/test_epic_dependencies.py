import pytest

from app.models.planning import Epic, EpicDependency
from app.services.epic_dependencies import EpicDependencyCycleError, topo_sort_epics


def _epic(eid: int, name: str) -> Epic:
    e = Epic(id=eid, project_id=1, name=name)
    return e


def test_topo_sort_ok():
    epics = [_epic(1, "E1"), _epic(2, "E2"), _epic(3, "E3")]
    deps = [
        EpicDependency(epic_id=2, depends_on_epic_id=1, project_id=1),
        EpicDependency(epic_id=3, depends_on_epic_id=2, project_id=1),
    ]
    ordered = topo_sort_epics(epics, deps)
    ids = [e.id for e in ordered]
    assert ids == [1, 2, 3]


def test_topo_sort_cycle():
    epics = [_epic(1, "E1"), _epic(2, "E2")]
    deps = [
        EpicDependency(epic_id=2, depends_on_epic_id=1, project_id=1),
        EpicDependency(epic_id=1, depends_on_epic_id=2, project_id=1),
    ]
    with pytest.raises(EpicDependencyCycleError):
        topo_sort_epics(epics, deps)
