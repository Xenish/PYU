from app.core.enums import TaskGranularity, TaskStatus
from app.models.planning import Task


def test_task_enums():
    assert TaskStatus.TODO.value == "todo"
    assert TaskStatus.READY_FOR_DEV.value == "ready_for_dev"
    assert TaskStatus.STALE.value == "stale"
    assert TaskGranularity.COARSE.value == "coarse"
    assert TaskGranularity.MEDIUM.value == "medium"
    assert TaskGranularity.FINE.value == "fine"


def test_task_model_fields():
    t = Task(
        project_id=1,
        sprint_id=1,
        epic_id=1,
        title="T",
        description="d",
        status=TaskStatus.TODO,
        granularity=TaskGranularity.COARSE,
        refinement_round=1,
        order_index=1,
        acceptance_criteria=["a"],
        dod_focus="release_ready",
        nfr_focus=["performance"],
        parent_task_id=None,
        estimate_sp=3,
    )
    assert t.title == "T"
