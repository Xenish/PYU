from fastapi import APIRouter

from app.api.routes import (
    approval,
    health,
    item_selection,
    jobs,
    metrics,
    planning,
    planning_approval,
    planning_update,
    projects,
    spec_wizard,
    status,
    tasks,
)


api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(projects.router, tags=["projects"])
api_router.include_router(spec_wizard.router, tags=["spec_wizard"])
api_router.include_router(item_selection.router, tags=["item_selection"])
api_router.include_router(approval.router, tags=["approval"])
api_router.include_router(planning.router, tags=["planning"])
api_router.include_router(planning_approval.router, tags=["planning-approval"])
api_router.include_router(planning_update.router, tags=["planning"])
api_router.include_router(tasks.router, tags=["tasks"])
api_router.include_router(jobs.router, tags=["jobs"])
api_router.include_router(status.router, tags=["status"])
api_router.include_router(metrics.router, tags=["metrics"])
