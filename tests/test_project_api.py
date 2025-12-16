from app.core.enums import StepStatus, StepType


def test_project_crud_via_api(test_app):
    # Create project
    resp = test_app.post(
        "/projects",
        json={"name": "Test Project", "description": "desc", "planning_detail_level": "low"},
    )
    assert resp.status_code == 201
    project_id = resp.json()["id"]

    # List projects
    list_resp = test_app.get("/projects")
    assert list_resp.status_code == 200
    assert any(p["id"] == project_id for p in list_resp.json())

    # Create step
    step_resp = test_app.post(
        f"/projects/{project_id}/steps",
        json={"step_type": StepType.OBJECTIVE.value, "status": StepStatus.PLANNED.value},
    )
    assert step_resp.status_code == 201
    assert step_resp.json()["project_id"] == project_id

    # List steps
    steps_resp = test_app.get(f"/projects/{project_id}/steps")
    assert steps_resp.status_code == 200
    assert len(steps_resp.json()) == 1
