from app.schemas.llm.tasks_split import TaskSplitResponse


def test_task_split_response_parsing():
    data = {
        "tasks": [
            {
                "parent_task_id": 10,
                "title": "Child",
                "description": "Fine task",
                "acceptance_criteria": ["a", "b"],
                "estimate_sp": 3,
            }
        ]
    }
    resp = TaskSplitResponse.model_validate(data)
    item = resp.tasks[0]
    assert item.parent_task_id == 10
    assert item.estimate_sp == 3
