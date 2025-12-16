import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.db.base import Base
from app.models.planning import Epic
from app.models.project import Project
from app.services.sprint_planning import _allocate_greedy


def test_allocate_greedy_capacity():
    s1 = type("S", (), {"id": 1, "capacity_sp": 10})
    s2 = type("S", (), {"id": 2, "capacity_sp": 10})
    epics = [
        Epic(id=1, project_id=1, name="E1", story_points=3),
        Epic(id=2, project_id=1, name="E2", story_points=5),
        Epic(id=3, project_id=1, name="E3", story_points=8),
        Epic(id=4, project_id=1, name="E4", story_points=3),
    ]
    assignments, backlog = _allocate_greedy(epics, [s1, s2])
    assert len(assignments) == 3  # one epic should not fit
    assert backlog  # at least one epic unscheduled


def test_allocate_greedy_zero_capacity():
    s1 = type("S", (), {"id": 1, "capacity_sp": 0})
    epics = [Epic(id=1, project_id=1, name="E1", story_points=2)]
    assignments, backlog = _allocate_greedy(epics, [s1])
    assert assignments == []
    assert backlog
