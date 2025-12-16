import pytest

from app.core.enums import TaskStatus
from app.models.planning import Task
from app.services.task_state import InvalidTaskTransition, change_task_status


def make_task(status: TaskStatus) -> Task:
    return Task(
        project_id=1,
        title="t",
        status=status,
    )


def test_valid_task_transitions():
    t = make_task(TaskStatus.TODO)
    change_task_status(t, TaskStatus.IN_PROGRESS)
    assert t.status == TaskStatus.IN_PROGRESS
    change_task_status(t, TaskStatus.DONE)
    assert t.status == TaskStatus.DONE
    t2 = make_task(TaskStatus.READY_FOR_DEV)
    change_task_status(t2, TaskStatus.IN_PROGRESS)
    assert t2.status == TaskStatus.IN_PROGRESS
    t3 = make_task(TaskStatus.TODO)
    change_task_status(t3, TaskStatus.STALE)
    assert t3.status == TaskStatus.STALE


def test_invalid_task_transition():
    t = make_task(TaskStatus.DONE)
    with pytest.raises(InvalidTaskTransition):
        change_task_status(t, TaskStatus.TODO)
    stale = make_task(TaskStatus.STALE)
    with pytest.raises(InvalidTaskTransition):
        change_task_status(stale, TaskStatus.IN_PROGRESS)
