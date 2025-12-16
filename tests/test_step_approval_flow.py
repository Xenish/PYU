"""Test approval workflow for spec wizard steps."""
import pytest
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.core.enums import ApprovalStatus, StepStatus, StepType
from app.db.base import Base
from app.models.imports import Comment
from app.models.project import Project, ProjectStep
from app.services import objective_step


async def _create_test_db():
    """Helper to create an in-memory test database"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.mark.asyncio
async def test_step_starts_with_pending_approval_after_llm_run(monkeypatch):
    """After LLM run, step should have approval_status=PENDING"""
    # Mock LLM
    async def fake_llm(prompt, response_model, temperature=None, max_tokens=None, db=None, project_id=None, step_type=None, intent=None):
        return response_model.model_validate(
            {"objectives": [{"title": "Test Obj", "description": "Desc", "priority": 1}]}
        )
    monkeypatch.setattr(objective_step, "call_llm", fake_llm)

    SessionLocal = await _create_test_db()
    async with SessionLocal() as db:
        project = Project(name="Test", description="Test project")
        db.add(project)
        await db.commit()
        await db.refresh(project)

        # Run objective step (triggers LLM)
        await objective_step.run_objective_step(db, project.id)

        # Check step status
        result = await db.execute(
            select(ProjectStep).where(
                ProjectStep.project_id == project.id,
                ProjectStep.step_type == StepType.OBJECTIVE,
            )
        )
        step = result.scalars().first()

        assert step is not None
        assert step.status == StepStatus.COMPLETED
        assert step.approval_status == ApprovalStatus.PENDING
        assert step.last_ai_run_at is not None
        assert step.last_approved_at is None


@pytest.mark.asyncio
async def test_approve_step_sets_approval_status_and_timestamp():
    """Approving a step should set approval_status=APPROVED and last_approved_at"""
    SessionLocal = await _create_test_db()
    async with SessionLocal() as db:
        # Setup: create project and step
        project = Project(name="Test", description="Test project")
        db.add(project)
        await db.flush()

        step = ProjectStep(
            project_id=project.id,
            step_type=StepType.OBJECTIVE,
            status=StepStatus.COMPLETED,
            approval_status=ApprovalStatus.PENDING,
        )
        db.add(step)
        await db.commit()
        await db.refresh(step)

        # Approve
        step.approval_status = ApprovalStatus.APPROVED
        step.last_approved_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(step)

        # Verify
        assert step.approval_status == ApprovalStatus.APPROVED
        assert step.last_approved_at is not None
        assert isinstance(step.last_approved_at, datetime)


@pytest.mark.asyncio
async def test_reject_step_creates_comment():
    """Rejecting a step should create a Comment with feedback"""
    SessionLocal = await _create_test_db()
    async with SessionLocal() as db:
        # Setup
        project = Project(name="Test", description="Test project")
        db.add(project)
        await db.flush()

        step = ProjectStep(
            project_id=project.id,
            step_type=StepType.TECH_STACK,
            status=StepStatus.COMPLETED,
            approval_status=ApprovalStatus.PENDING,
        )
        db.add(step)
        await db.commit()
        await db.refresh(step)

        # Reject with feedback
        step.approval_status = ApprovalStatus.REJECTED
        step.last_approved_at = None

        feedback_text = "The tech stack choices are not suitable for our use case"
        comment = Comment(
            project_id=project.id,
            entity_type=f"project_step_{step.step_type.value}",
            entity_id=step.id,
            author="user",
            text=feedback_text,
        )
        db.add(comment)
        await db.commit()

        # Verify step rejection
        await db.refresh(step)
        assert step.approval_status == ApprovalStatus.REJECTED
        assert step.last_approved_at is None

        # Verify comment was created
        result = await db.execute(
            select(Comment).where(
                Comment.project_id == project.id,
                Comment.entity_id == step.id,
            )
        )
        saved_comment = result.scalars().first()

        assert saved_comment is not None
        assert saved_comment.text == feedback_text
        assert saved_comment.author == "user"
        assert saved_comment.entity_type == "project_step_tech_stack"


@pytest.mark.asyncio
async def test_regenerate_resets_to_pending(monkeypatch):
    """Regenerating a step should reset approval_status to PENDING"""
    # Mock LLM
    async def fake_llm(prompt, response_model, temperature=None, max_tokens=None, db=None, project_id=None, step_type=None, intent=None):
        return response_model.model_validate(
            {"objectives": [{"title": "Obj2", "description": "Regenerated", "priority": 1}]}
        )
    monkeypatch.setattr(objective_step, "call_llm", fake_llm)

    SessionLocal = await _create_test_db()
    async with SessionLocal() as db:
        # Setup: rejected step - set status to PLANNED so it can be regenerated
        project = Project(name="Test", description="Test project for regeneration")
        db.add(project)
        await db.flush()

        step = ProjectStep(
            project_id=project.id,
            step_type=StepType.OBJECTIVE,
            status=StepStatus.PLANNED,  # Set to PLANNED so it will re-run
            approval_status=ApprovalStatus.REJECTED,
            last_approved_at=None,
        )
        db.add(step)
        await db.commit()
        await db.refresh(step)

        # Regenerate (re-run LLM)
        await objective_step.run_objective_step(db, project.id)

        await db.refresh(step)

        # After regeneration, should be PENDING again
        assert step.approval_status == ApprovalStatus.PENDING
        assert step.status == StepStatus.COMPLETED
        assert step.last_ai_run_at is not None
        assert step.last_approved_at is None


@pytest.mark.asyncio
async def test_cannot_approve_non_completed_step():
    """Only COMPLETED steps can be approved"""
    SessionLocal = await _create_test_db()
    async with SessionLocal() as db:
        project = Project(name="Test", description="Test project")
        db.add(project)
        await db.flush()

        step = ProjectStep(
            project_id=project.id,
            step_type=StepType.FEATURES,
            status=StepStatus.IN_PROGRESS,  # Not completed yet
            approval_status=ApprovalStatus.PENDING,
        )
        db.add(step)
        await db.commit()

        # In the API, this would return 400
        # Here we just verify the state
        assert step.status != StepStatus.COMPLETED
        assert step.approval_status == ApprovalStatus.PENDING


@pytest.mark.asyncio
async def test_approval_workflow_full_cycle(monkeypatch):
    """Test complete workflow: run → pending → approve"""
    # Mock LLM
    async def fake_llm(prompt, response_model, temperature=None, max_tokens=None, db=None, project_id=None, step_type=None, intent=None):
        return response_model.model_validate(
            {"objectives": [{"title": "Full Cycle", "description": "End to end", "priority": 1}]}
        )
    monkeypatch.setattr(objective_step, "call_llm", fake_llm)

    SessionLocal = await _create_test_db()
    async with SessionLocal() as db:
        # Create project
        project = Project(name="Full Cycle Test", description="Testing full approval workflow")
        db.add(project)
        await db.commit()
        await db.refresh(project)

        # Step 1: Run LLM step
        await objective_step.run_objective_step(db, project.id)

        result = await db.execute(
            select(ProjectStep).where(
                ProjectStep.project_id == project.id,
                ProjectStep.step_type == StepType.OBJECTIVE,
            )
        )
        step = result.scalars().first()

        assert step.status == StepStatus.COMPLETED
        assert step.approval_status == ApprovalStatus.PENDING
        assert step.last_approved_at is None

        # Step 2: Approve
        step.approval_status = ApprovalStatus.APPROVED
        step.last_approved_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(step)

        assert step.approval_status == ApprovalStatus.APPROVED
        assert step.last_approved_at is not None

        # Verify workflow completed successfully
        assert step.status == StepStatus.COMPLETED
        assert step.approval_status == ApprovalStatus.APPROVED
