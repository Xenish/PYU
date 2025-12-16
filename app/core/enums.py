from enum import Enum


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    SPEC_IN_PROGRESS = "spec_in_progress"
    READY_FOR_PLANNING = "ready_for_planning"
    PLANNED = "planned"


class PlanningDetailLevel(str, Enum):
    LOW = "low"
    HIGH = "high"


class StepType(str, Enum):
    OBJECTIVE = "objective"
    TECH_STACK = "tech_stack"
    FEATURES = "features"
    ARCHITECTURE = "architecture"
    DOD = "dod"
    NFR = "nfr"
    RISKS = "risks"
    EPICS = "epics"
    GAP_ANALYSIS = "gap_analysis"
    SPRINT_PLAN = "sprint_plan"


class StepStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    STALE = "stale"
    LOCKED = "locked"
    FAILED = "failed"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"
    READY_FOR_DEV = "ready_for_dev"
    STALE = "stale"


class TaskGranularity(str, Enum):
    COARSE = "coarse"
    MEDIUM = "medium"
    FINE = "fine"


class JobType(str, Enum):
    TASK_PIPELINE_FOR_SPRINT = "task_pipeline_for_sprint"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class LLMIntent(str, Enum):
    OBJECTIVE_STEP = "objective_step"
    SPEC_STEP = "spec_step"
    QUALITY_STEP = "quality_step"
    TASK_PASS1 = "task_pass1"
    TASK_PASS2 = "task_pass2"
    TASK_PASS3 = "task_pass3"
    PROJECT_SUGGESTION = "project_suggestion"
    PROJECT_REVIEW = "project_review"
