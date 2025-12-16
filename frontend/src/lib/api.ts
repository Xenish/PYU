const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export type Project = {
  id: number;
  name: string;
  description?: string | null;
};

export type ProjectUpdate = {
  name?: string;
  description?: string | null;
  planning_detail_level?: string;
  language?: string;
};

export type Sprint = {
  id: number;
  name: string;
  index: number;
  status: string;
};

export type Job = {
  id: number;
  type: string;
  status: string;
  progress_pct?: number | null;
  current_step?: string | null;
  error_message?: string | null;
  created_at?: string;
  finished_at?: string | null;
};

export type Task = {
  id: number;
  title: string;
  status?: string;
  estimate_sp?: number | null;
  epic_id?: number | null;
  epic_name?: string | null;
  dod_focus?: string | null;
  nfr_focus?: string[] | null;
  parent_task_id?: number | null;
};

export type StepStatus = "planned" | "in_progress" | "completed" | "stale" | "failed" | "locked";

export type StepSummary = {
  step_type: string;
  status: StepStatus;
  approval_status?: string;
  last_ai_run_at?: string | null;
  last_approved_at?: string | null;
  summary?: string | null;
  item_count: number;
};

export type WizardSummary = {
  project_id: number;
  steps: StepSummary[];
};

export type ObjectiveDetail = {
  id: number;
  title: string;
  text?: string | null;
  is_selected: boolean;
  priority_score?: number | null;
  impact_level?: string | null;
  recommendation_type?: string | null;
  category_tags?: string[] | null;
  rationale?: string | null;
  advantages?: string[] | null;
  disadvantages?: string[] | null;
  conflicts_with?: number[] | null;
  requires?: number[] | null;
  category_exclusive?: boolean;
};

export type TechStackDetail = {
  id: number;
  frontend?: Record<string, unknown> | null;
  backend?: Record<string, unknown> | null;
  database?: Record<string, unknown> | null;
  infra?: Record<string, unknown> | null;
  analytics?: Record<string, unknown> | null;
  ci_cd?: Record<string, unknown> | null;
  is_selected: boolean;
  priority_score?: number | null;
  impact_level?: string | null;
  recommendation_type?: string | null;
  category_tags?: string[] | null;
  rationale?: string | null;
  advantages?: string[] | null;
  disadvantages?: string[] | null;
  conflicts_with?: number[] | null;
  requires?: number[] | null;
  category_exclusive?: boolean;
};

export type FeatureDetail = {
  id: number;
  name: string;
  description?: string | null;
  is_selected: boolean;
  priority_score?: number | null;
  impact_level?: string | null;
  recommendation_type?: string | null;
  category_tags?: string[] | null;
  rationale?: string | null;
  advantages?: string[] | null;
  disadvantages?: string[] | null;
  conflicts_with?: number[] | null;
  requires?: number[] | null;
  category_exclusive?: boolean;
};

export type ArchitectureDetail = {
  id: number;
  name: string;
  layer: string;
  description?: string | null;
  is_selected: boolean;
  priority_score?: number | null;
  impact_level?: string | null;
  recommendation_type?: string | null;
  category_tags?: string[] | null;
  rationale?: string | null;
  advantages?: string[] | null;
  disadvantages?: string[] | null;
  conflicts_with?: number[] | null;
  requires?: number[] | null;
  category_exclusive?: boolean;
};

export type DoDDetail = {
  id: number;
  description: string;
  category?: string | null;
  is_selected: boolean;
  priority_score?: number | null;
  impact_level?: string | null;
  recommendation_type?: string | null;
  category_tags?: string[] | null;
  rationale?: string | null;
  advantages?: string[] | null;
  disadvantages?: string[] | null;
  conflicts_with?: number[] | null;
  requires?: number[] | null;
  category_exclusive?: boolean;
};

export type NFRDetail = {
  id: number;
  type: string;
  description: string;
  is_selected: boolean;
  priority_score?: number | null;
  impact_level?: string | null;
  recommendation_type?: string | null;
  category_tags?: string[] | null;
  rationale?: string | null;
  advantages?: string[] | null;
  disadvantages?: string[] | null;
  conflicts_with?: number[] | null;
  requires?: number[] | null;
  category_exclusive?: boolean;
};

export type RiskDetail = {
  id: number;
  description: string;
  is_selected: boolean;
  priority_score?: number | null;
  impact_level?: string | null;
  recommendation_type?: string | null;
  category_tags?: string[] | null;
  rationale?: string | null;
  advantages?: string[] | null;
  disadvantages?: string[] | null;
  conflicts_with?: number[] | null;
  requires?: number[] | null;
  category_exclusive?: boolean;
};

export type WizardDetail = {
  objectives: ObjectiveDetail[];
  tech_stack: TechStackDetail[];
  features: FeatureDetail[];
  architecture: ArchitectureDetail[];
  dod_items: DoDDetail[];
  nfr_items: NFRDetail[];
  risk_items: RiskDetail[];
};

export type LLMInfo = {
  provider: string;
  model: string;
  available_models: string[];
};

export type LLMUpdateRequest = {
  model: string;
  provider?: string | null;
};

export type SelectionSummary = {
  project_id: number;
  item_type: string;
  selected_count: number;
  total_count: number;
};

export type ProjectSuggestion = {
  id: number;
  title: string;
  description?: string | null;
  category: string;
  examples?: string[] | null;
  user_added_examples?: string[] | null;
  is_selected: boolean;
  generation_round: number;

  // Decision support
  priority_score?: number | null;
  impact_level?: string | null;
  recommendation_type?: string | null;
  category_tags?: string[] | null;
  rationale?: string | null;
  advantages?: string[] | null;
  disadvantages?: string[] | null;
};

export type ProjectReviewItem = {
  suggestion_title: string;
  is_adequate: boolean;
  feedback?: string | null;
  new_questions?: string[] | null;
  expanded_suggestions?: ProjectSuggestion[] | null;
};

export type ProjectReviewResponse = {
  reviews: ProjectReviewItem[];
  new_suggestions: ProjectSuggestion[];
  overall_feedback: string;
};

export type PlanningEpicOverview = {
  id: number;
  name: string;
  category?: string | null;
  story_points?: number | null;
  sprint_ids: number[];
  dependencies: (number | null)[];
};

export type PlanningSprintOverview = {
  id: number;
  name: string;
  capacity_sp?: number | null;
  allocated_sp: number;
  epic_ids: number[];
  quality_summary: {
    dod_count: number;
    nfr_categories: string[];
  };
};

export type PlanningOverview = {
  project_id: number;
  epics: PlanningEpicOverview[];
  sprints: PlanningSprintOverview[];
};

export type StatusOverview = {
  projects_count: number;
  jobs: Record<string, number>;
  llm_calls_today: number;
  llm_quota_limit?: number | null;
};

export type ProjectDiagnostics = {
  project_id: number;
  epic_count: number;
  sprint_count: number;
  task_count: Record<string, number>;
  last_wizard_run_at?: string | null;
  last_task_pipeline_job?: {
    job_id: number;
    status: string;
    finished_at?: string | null;
  } | null;
};

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `Request failed: ${res.status}`);
  }
  // Some endpoints (e.g., DELETE) may return no JSON body
  const contentLength = res.headers.get("content-length");
  if (res.status === 204 || contentLength === "0") {
    return undefined as T;
  }
  const text = await res.text();
  if (!text) {
    return undefined as T;
  }
  try {
    return JSON.parse(text) as T;
  } catch (err) {
    throw new Error(`Response parse error: ${err instanceof Error ? err.message : String(err)}`);
  }
}

export const getProjects = () => request<Project[]>("/projects");
export const createProject = (name: string, description?: string) =>
  request<Project>("/projects", {
    method: "POST",
    body: JSON.stringify({ name, description }),
  });
export const deleteProject = (projectId: number) =>
  request<void>(`/projects/${projectId}`, { method: "DELETE" });
export const updateProject = (projectId: number, payload: ProjectUpdate) =>
  request<Project>(`/projects/${projectId}`, { method: "PATCH", body: JSON.stringify(payload) });

export const getLlmInfo = () => request<LLMInfo>("/status/llm");
export const setLlm = (payload: LLMUpdateRequest) =>
  request<LLMInfo>("/status/llm", {
    method: "POST",
    body: JSON.stringify(payload),
  });

// Project Suggestion APIs
export const generateProjectSuggestions = (projectId: number) =>
  request<ProjectSuggestion[]>(`/projects/${projectId}/suggestions/generate`, { method: "POST" });

export const reviewProjectSuggestions = (projectId: number) =>
  request<ProjectReviewResponse>(`/projects/${projectId}/suggestions/review`, { method: "POST" });

export const getProjectSuggestions = (projectId: number) =>
  request<ProjectSuggestion[]>(`/projects/${projectId}/suggestions`);

export const markExampleAsAdded = (projectId: number, suggestionId: number, exampleText: string) =>
  request<ProjectSuggestion>(`/projects/${projectId}/suggestions/${suggestionId}/add-example`, {
    method: "POST",
    body: JSON.stringify({ example_text: exampleText }),
  });

export const expandSuggestion = (projectId: number, suggestionId: number) =>
  request<{ expanded_suggestions: ProjectSuggestion[] }>(`/projects/${projectId}/suggestions/${suggestionId}/expand`, {
    method: "POST",
  });
export const getSprints = (projectId: number) =>
  request<Sprint[]>(`/projects/${projectId}/sprints`);
export const getJobs = (projectId: number) =>
  request<Job[]>(`/projects/${projectId}/jobs`);
export const getJob = (jobId: number) => request<Job>(`/jobs/${jobId}`);
export const createTaskPipelineJob = (projectId: number, sprintId: number) =>
  request<Job>("/jobs/task-pipeline-for-sprint", {
    method: "POST",
    body: JSON.stringify({ project_id: projectId, sprint_id: sprintId }),
  });
export const cancelJob = (jobId: number) =>
  request<Job>(`/jobs/${jobId}/cancel`, { method: "POST" });
export const runNextJob = () => request<Job | null>("/jobs/run-next", { method: "POST" });
export const getReadyForDevTasks = (sprintId: number) =>
  request<Task[]>(`/sprints/${sprintId}/tasks?ready_for_dev_only=true`);
export const getTasksForBoard = (sprintId: number) =>
  request<Task[]>(`/sprints/${sprintId}/tasks?for_board=true`);
export const updateTaskStatus = (taskId: number, status: string) =>
  request<Task>(`/tasks/${taskId}/status`, { method: "PATCH", body: JSON.stringify({ status }) });
export const getWizardSummary = (projectId: number) =>
  request<WizardSummary>(`/projects/${projectId}/spec-wizard/summary`);
export const getWizardDetail = (projectId: number) =>
  request<WizardDetail>(`/projects/${projectId}/spec-wizard/detail`);
export const runObjective = (projectId: number) =>
  request(`/projects/${projectId}/steps/objective/run`, { method: "POST" });
export const runTechStack = (projectId: number) =>
  request(`/projects/${projectId}/steps/tech-stack/run`, { method: "POST" });
export const runFeatures = (projectId: number) =>
  request(`/projects/${projectId}/steps/features/run`, { method: "POST" });
export const runArchitecture = (projectId: number) =>
  request(`/projects/${projectId}/steps/architecture/run`, { method: "POST" });
export const runQuality = (projectId: number) =>
  request(`/projects/${projectId}/steps/quality/run`, { method: "POST" });

// Approval endpoints
export const approveStep = (projectId: number, stepType: string) =>
  request(`/projects/${projectId}/steps/${stepType}/approve`, { method: "POST" });

export const rejectStep = (projectId: number, stepType: string, feedback: string) =>
  request(`/projects/${projectId}/steps/${stepType}/reject`, {
    method: "POST",
    body: JSON.stringify({ feedback }),
    headers: { "Content-Type": "application/json" },
  });

export const regenerateStep = (projectId: number, stepType: string, feedback?: string) =>
  request(`/projects/${projectId}/steps/${stepType}/regenerate`, {
    method: "POST",
    body: JSON.stringify({ feedback }),
    headers: { "Content-Type": "application/json" },
  });

export const toggleItemSelection = (projectId: number, itemType: string, itemId: number) =>
  request(`/items/${itemType}/${itemId}/toggle-select`, {
    method: "POST",
    body: JSON.stringify({ project_id: projectId }),
  });

export const selectAllItems = (projectId: number, itemType: string) =>
  request(`/projects/${projectId}/items/${itemType}/select-all`, { method: "POST" });

export const deselectAllItems = (projectId: number, itemType: string) =>
  request(`/projects/${projectId}/items/${itemType}/deselect-all`, { method: "POST" });

export const getSelectionSummary = (projectId: number, itemType: string) =>
  request<SelectionSummary>(`/projects/${projectId}/items/${itemType}/selection-summary`);

export const getPlanningOverview = (projectId: number) =>
  request<PlanningOverview>(`/projects/${projectId}/planning/overview`);
export const getStatusOverview = () => request<StatusOverview>("/status/overview");
export const getProjectDiagnostics = (projectId: number) =>
  request<ProjectDiagnostics>(`/projects/${projectId}/diagnostics`);

// Planning generation endpoints
export const generateEpics = (projectId: number) =>
  request(`/projects/${projectId}/planning/generate-epics`, { method: "POST" });
export const estimateStoryPoints = (projectId: number) =>
  request(`/projects/${projectId}/planning/estimate-epic-story-points`, { method: "POST" });
export const generateSprintPlan = (projectId: number, numSprints: number = 3) =>
  request(
    `/projects/${projectId}/planning/generate-sprint-plan?num_sprints=${numSprints}`,
    { method: "POST" }
  );
export const generateCapacityPlan = (
  projectId: number,
  numSprints: number = 3,
  capacitySp?: number
) =>
  request(
    `/projects/${projectId}/planning/generate-capacity-plan?num_sprints=${numSprints}${
      capacitySp ? `&default_capacity_sp=${capacitySp}` : ""
    }`,
    { method: "POST" }
  );
