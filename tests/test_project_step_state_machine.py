import pytest

from app.core.enums import StepStatus, StepType
from app.services import project_steps
from app.models.project import ProjectStep


def make_step(status: StepStatus):
    step = ProjectStep(project_id=1, step_type=StepType.OBJECTIVE, status=status)
    return step


@pytest.mark.asyncio
async def test_valid_transitions():
    step = make_step(StepStatus.PLANNED)
    await project_steps.change_step_status(step, StepStatus.IN_PROGRESS)
    assert step.status == StepStatus.IN_PROGRESS
    await project_steps.change_step_status(step, StepStatus.COMPLETED)
    await project_steps.change_step_status(step, StepStatus.STALE)
    assert step.status == StepStatus.STALE


@pytest.mark.asyncio
async def test_invalid_transition():
    step = make_step(StepStatus.COMPLETED)
    with pytest.raises(project_steps.InvalidStepTransition):
        await project_steps.change_step_status(step, StepStatus.IN_PROGRESS)
