from app.core.enums import StepStatus, StepType


def test_step_status_values_consistent():
    expected = {"planned", "in_progress", "completed", "stale", "locked", "failed"}
    assert set([s.value for s in StepStatus]) == expected


def test_step_type_values_consistent():
    expected = {
        "objective",
        "tech_stack",
        "features",
        "architecture",
        "dod",
        "nfr",
        "risks",
        "epics",
        "gap_analysis",
        "sprint_plan",
    }
    assert set([s.value for s in StepType]) == expected
