from app.schemas.llm.tasks_refine import TaskRefinementResponse


def test_task_refinement_response_parsing():
    data = {
        "tasks": [
            {
                "task_id": 1,
                "title": "Refined Task",
                "description": "Detailed desc",
                "acceptance_criteria": ["criterion 1", "criterion 2"],
                "dod_focus": "release_ready",
                "nfr_focus": ["performance", "security"],
                "depends_on_task_ids": [2, 2, 3],
            }
        ]
    }
    resp = TaskRefinementResponse.model_validate(data)
    item = resp.tasks[0]
    assert item.task_id == 1
    assert item.acceptance_criteria == ["criterion 1", "criterion 2"]
    # duplicates removed but order preserved
    assert item.depends_on_task_ids == [2, 3]
