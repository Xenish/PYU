from app.core.enums import JobStatus, JobType
from app.models.job import Job


def test_job_enums():
    assert JobType.TASK_PIPELINE_FOR_SPRINT.value == "task_pipeline_for_sprint"
    assert JobStatus.QUEUED.value == "queued"
    assert JobStatus.COMPLETED.value == "completed"


def test_job_model_fields():
    job = Job(
        project_id=1,
        sprint_id=2,
        type=JobType.TASK_PIPELINE_FOR_SPRINT.value,
        status=JobStatus.QUEUED.value,
        payload_json="{}",
    )
    assert job.project_id == 1
    assert job.status == JobStatus.QUEUED.value
