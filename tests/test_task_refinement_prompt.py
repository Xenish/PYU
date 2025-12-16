from app.core.enums import PlanningDetailLevel
from app.services.prompts import build_task_refinement_prompt


class Dummy:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_task_refinement_prompt_detail_level_differs():
    tasks = [
        Dummy(id=1, title="T1", description="desc1"),
        Dummy(id=2, title="T2", description="desc2"),
    ]
    dod_items = [Dummy(category="release_ready", description="Release ready")]
    nfr_items = [Dummy(type="performance")]

    low = build_task_refinement_prompt(tasks, dod_items, nfr_items, PlanningDetailLevel.LOW)
    high = build_task_refinement_prompt(tasks, dod_items, nfr_items, PlanningDetailLevel.HIGH)

    assert "Daha az" in low
    assert "Daha detaylı" in high
    # ensure task ids included
    assert "(1)" in low and "(2)" in high
