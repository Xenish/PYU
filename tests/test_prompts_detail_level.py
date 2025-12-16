from app.core.enums import PlanningDetailLevel
from app.models.project import Project
from app.services import prompts


def test_detail_level_changes_prompt():
    project_low = Project(id=1, name="Proj", description="D", planning_detail_level=PlanningDetailLevel.LOW)
    project_high = Project(id=1, name="Proj", description="D", planning_detail_level=PlanningDetailLevel.HIGH)

    low_prompt = prompts.build_tech_stack_prompt(project_low)
    high_prompt = prompts.build_tech_stack_prompt(project_high)

    assert "Daha az" in low_prompt or "az" in low_prompt
    assert "Daha detaylı" in high_prompt or "detay" in high_prompt
