from app.core.enums import TaskStatus
from app.models.planning import Task


class InvalidTaskTransition(Exception):
    pass


ALLOWED_TASK_TRANSITIONS = {
    TaskStatus.TODO: {
        TaskStatus.IN_PROGRESS,
        TaskStatus.BLOCKED,
        TaskStatus.READY_FOR_DEV,
        TaskStatus.STALE,
    },
    TaskStatus.IN_PROGRESS: {TaskStatus.DONE, TaskStatus.BLOCKED, TaskStatus.STALE},
    TaskStatus.BLOCKED: {TaskStatus.IN_PROGRESS, TaskStatus.STALE},
    TaskStatus.READY_FOR_DEV: {TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED, TaskStatus.STALE},
    TaskStatus.STALE: set(),
}


def change_task_status(task: Task, new_status: TaskStatus) -> None:
    allowed = ALLOWED_TASK_TRANSITIONS.get(task.status, set())
    if new_status not in allowed:
        raise InvalidTaskTransition(f"{task.status.value} -> {new_status.value} geçişi yasak")
    task.status = new_status
