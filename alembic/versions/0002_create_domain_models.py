"""create domain models

Revision ID: 0002_create_domain_models
Revises: 0001_initial
Create Date: 2025-02-16

"""
from alembic import op
import sqlalchemy as sa

revision = "0002_create_domain_models"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # projects
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=True, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "status",
            sa.Enum("draft", "spec_in_progress", "ready_for_planning", "planned", name="projectstatus"),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("language", sa.String(length=5), nullable=False, server_default="tr"),
        sa.Column(
            "planning_detail_level",
            sa.Enum("low", "high", name="planningdetaillevel"),
            nullable=False,
            server_default="low",
        ),
        sa.Column("current_snapshot_id", sa.Integer, nullable=True),
        sa.Column("origin_project_id", sa.Integer, nullable=True),
    )

    op.create_table(
        "project_objectives",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=True, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer, nullable=True, server_default="1"),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("text", sa.Text, nullable=True),
        sa.Column("target_audience", sa.Text, nullable=True),
        sa.Column("v1_scope", sa.JSON, nullable=True),
        sa.Column("is_selected", sa.Boolean, nullable=True, server_default=sa.false()),
    )

    op.create_table(
        "tech_stack_options",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=True, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer, nullable=True, server_default="1"),
        sa.Column("is_selected", sa.Boolean, nullable=True, server_default=sa.false()),
        sa.Column("frontend", sa.JSON, nullable=True),
        sa.Column("backend", sa.JSON, nullable=True),
        sa.Column("database", sa.JSON, nullable=True),
        sa.Column("infra", sa.JSON, nullable=True),
        sa.Column("analytics", sa.JSON, nullable=True),
        sa.Column("ci_cd", sa.JSON, nullable=True),
        sa.Column("pros", sa.JSON, nullable=True),
        sa.Column("cons", sa.JSON, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
    )

    op.create_table(
        "features",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=True, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("type", sa.String(length=20), nullable=True, server_default="must"),
        sa.Column("origin", sa.String(length=20), nullable=True, server_default="user"),
        sa.Column("is_selected", sa.Boolean, nullable=True, server_default=sa.false()),
        sa.Column("group", sa.String(length=100), nullable=True),
        sa.Column("iteration_index", sa.Integer, nullable=True),
    )

    op.create_table(
        "architecture_components",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=True, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("layer", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("responsibilities", sa.JSON, nullable=True),
        sa.Column("related_feature_ids", sa.JSON, nullable=True),
    )

    op.create_table(
        "dod_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=True, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("test_method", sa.String(length=20), nullable=True),
        sa.Column("done_when", sa.Text, nullable=True),
        sa.Column("related_feature_ids", sa.JSON, nullable=True),
        sa.Column("related_component_ids", sa.JSON, nullable=True),
        sa.Column("priority", sa.Integer, nullable=True),
        sa.Column("implementation_status", sa.String(length=20), nullable=False, server_default="not_started"),
    )

    op.create_table(
        "nfr_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=True, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("measurable_target", sa.String(length=255), nullable=True),
        sa.Column("related_component_ids", sa.JSON, nullable=True),
        sa.Column("implementation_status", sa.String(length=20), nullable=False, server_default="not_started"),
    )

    op.create_table(
        "risk_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=True, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("impact", sa.Integer, nullable=False),
        sa.Column("likelihood", sa.Integer, nullable=False),
        sa.Column("mitigation", sa.Text, nullable=True),
    )

    op.create_table(
        "epics",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=True, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("related_component_ids", sa.JSON, nullable=True),
        sa.Column("related_feature_ids", sa.JSON, nullable=True),
        sa.Column("business_value", sa.Integer, nullable=True),
        sa.Column("urgency", sa.Integer, nullable=True),
        sa.Column("risk_reduction", sa.Integer, nullable=True),
        sa.Column("priority_score", sa.Float, nullable=True),
        sa.Column("implementation_status", sa.String(length=20), nullable=False, server_default="not_started"),
        sa.Column("estimated_total_points", sa.Integer, nullable=True),
        sa.Column("completed_points", sa.Integer, nullable=False, server_default="0"),
    )

    op.create_table(
        "epic_dependencies",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=True, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("epic_id", sa.Integer, sa.ForeignKey("epics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("depends_on_epic_id", sa.Integer, sa.ForeignKey("epics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
    )

    op.create_table(
        "sprint_plans",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=True, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer, nullable=True, server_default="1"),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=True, server_default=sa.true()),
    )

    op.create_table(
        "sprints",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=True, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sprint_plan_id", sa.Integer, sa.ForeignKey("sprint_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("index", sa.Integer, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("duration_weeks", sa.Integer, nullable=True),
        sa.Column("goals", sa.JSON, nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="planned"),
        sa.Column("capacity_hint", sa.Integer, nullable=True),
    )

    op.create_table(
        "sprint_epics",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=True, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sprint_id", sa.Integer, sa.ForeignKey("sprints.id", ondelete="CASCADE"), nullable=False),
        sa.Column("epic_id", sa.Integer, sa.ForeignKey("epics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scope_note", sa.Text, nullable=True),
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=True, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sprint_id", sa.Integer, sa.ForeignKey("sprints.id", ondelete="CASCADE"), nullable=True),
        sa.Column("epic_id", sa.Integer, sa.ForeignKey("epics.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "status",
            sa.Enum("todo", "in_progress", "done", name="taskstatus"),
            nullable=False,
            server_default="todo",
        ),
        sa.Column(
            "granularity",
            sa.Enum("coarse", "atomic", name="taskgranularity"),
            nullable=True,
        ),
        sa.Column("refinement_round", sa.Integer, nullable=True),
        sa.Column("acceptance_criteria", sa.JSON, nullable=True),
        sa.Column("depends_on_task_ids", sa.JSON, nullable=True),
        sa.Column("related_dod_ids", sa.JSON, nullable=True),
        sa.Column("related_nfr_ids", sa.JSON, nullable=True),
        sa.Column("estimate_points", sa.Integer, nullable=True),
    )

    op.create_table(
        "import_sessions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=True, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="created"),
        sa.Column("source_metadata", sa.JSON, nullable=True),
    )

    op.create_table(
        "imported_assets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=True, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("import_session_id", sa.Integer, sa.ForeignKey("import_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("path", sa.String(length=500), nullable=True),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("raw_content", sa.Text, nullable=True),
        sa.Column("processing_status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text, nullable=True),
    )

    op.create_table(
        "imported_summaries",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=True, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("import_session_id", sa.Integer, sa.ForeignKey("import_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("raw_summary", sa.Text, nullable=True),
        sa.Column("related_asset_id", sa.Integer, sa.ForeignKey("imported_assets.id", ondelete="SET NULL"), nullable=True),
    )

    op.create_table(
        "project_spec_snapshots",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=True, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("spec_version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("spec_payload", sa.JSON, nullable=True),
    )

    op.create_table(
        "gap_analysis_results",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=True, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("import_session_id", sa.Integer, sa.ForeignKey("import_sessions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("snapshot_id", sa.Integer, sa.ForeignKey("project_spec_snapshots.id", ondelete="SET NULL"), nullable=True),
        sa.Column("result_payload", sa.JSON, nullable=True),
    )

    op.create_table(
        "comments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=True, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.Integer, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("author", sa.String(length=100), nullable=True),
    )

    op.create_table(
        "llm_call_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=True, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("step_type", sa.String(length=50), nullable=True),
        sa.Column("request_payload", sa.JSON, nullable=True),
        sa.Column("response_payload", sa.JSON, nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("tokens", sa.Integer, nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),
    )

    op.create_table(
        "project_steps",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=True, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "step_type",
            sa.Enum(
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
                name="steptype",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "not_started",
                "draft",
                "awaiting_approval",
                "approved",
                "stale",
                name="stepstatus",
            ),
            nullable=False,
            server_default="not_started",
        ),
        sa.Column("last_input_hash", sa.String(length=128), nullable=True),
        sa.Column("last_output_json", sa.JSON, nullable=True),
        sa.Column("last_ai_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("depends_on_step_types", sa.JSON, nullable=True),
        sa.UniqueConstraint("project_id", "step_type", name="uq_project_step_type"),
    )


def downgrade() -> None:
    for table in [
        "project_steps",
        "llm_call_logs",
        "comments",
        "gap_analysis_results",
        "project_spec_snapshots",
        "imported_summaries",
        "imported_assets",
        "import_sessions",
        "tasks",
        "sprint_epics",
        "sprints",
        "sprint_plans",
        "epic_dependencies",
        "epics",
        "risk_items",
        "nfr_items",
        "dod_items",
        "architecture_components",
        "features",
        "tech_stack_options",
        "project_objectives",
        "projects",
    ]:
        op.drop_table(table)

    for enum_name in [
        "projectstatus",
        "planningdetaillevel",
        "steptype",
        "stepstatus",
        "taskstatus",
        "taskgranularity",
    ]:
        op.execute(sa.text(f"DROP TYPE IF EXISTS {enum_name}"))
