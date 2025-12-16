from app.core.enums import PlanningDetailLevel
from app.services.prompts import build_task_split_prompt


class Dummy:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_task_split_prompt_contains_instructions():
    tasks = [Dummy(id=1, title="Medium1", description="desc")]
    prompt = build_task_split_prompt(tasks, PlanningDetailLevel.HIGH)
    assert "fine task'lere böl" in prompt
    assert "tek deliverable" in prompt
    assert "estimate_sp" in prompt
    assert "(1)" in prompt
