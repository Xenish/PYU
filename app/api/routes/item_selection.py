from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.filters import only_active
from app.db.session import get_db
from app.models.project import (
    ArchitectureComponent,
    Feature,
    ProjectObjective,
    TechStackOption,
)
from app.models.quality import DoDItem, NFRItem, RiskItem
from app.repositories.project_repo import get_project_by_id

router = APIRouter()


ITEM_TYPE_TO_MODEL = {
    "objective": ProjectObjective,
    "tech_stack": TechStackOption,
    "feature": Feature,
    "architecture": ArchitectureComponent,
    "dod": DoDItem,
    "nfr": NFRItem,
    "risk": RiskItem,
}


class ItemSelectionResponse(BaseModel):
    project_id: int
    item_type: str
    item_id: int
    is_selected: bool
    message: str


class BulkSelectionResponse(BaseModel):
    project_id: int
    item_type: str
    updated_count: int
    selected_count: int
    total_count: int


class SelectionSummaryResponse(BaseModel):
    project_id: int
    item_type: str
    selected_count: int
    total_count: int


class ToggleSelectionPayload(BaseModel):
    project_id: int


def _get_model_or_404(item_type: str):
    model = ITEM_TYPE_TO_MODEL.get(item_type)
    if not model:
        raise HTTPException(status_code=404, detail="Invalid item type")
    return model


async def _ensure_project_exists(db: AsyncSession, project_id: int):
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


async def _ensure_project_unlocked(db: AsyncSession, project_id: int):
    """Ensure project spec is not locked before allowing item selection changes."""
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.spec_locked:
        raise HTTPException(
            status_code=403,
            detail="Project spec is locked. Please clone the project to make changes.",
        )


async def _get_item_or_404(db: AsyncSession, model, item_id: int):
    stmt = select(model).where(model.id == item_id)
    stmt = only_active(stmt, model)
    result = await db.execute(stmt)
    item = result.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


async def _list_items_for_project(db: AsyncSession, model, project_id: int):
    stmt = select(model).where(model.project_id == project_id)
    stmt = only_active(stmt, model)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post(
    "/items/{item_type}/{item_id}/toggle-select",
    response_model=ItemSelectionResponse,
)
async def toggle_item_selection(
    item_type: str,
    item_id: int,
    payload: ToggleSelectionPayload,
    db: AsyncSession = Depends(get_db),
):
    """
    Toggle selection state of a single item.
    Requires the item to belong to the given project and spec to be unlocked.
    """
    model = _get_model_or_404(item_type)
    await _ensure_project_unlocked(db, payload.project_id)
    item = await _get_item_or_404(db, model, item_id)
    if item.project_id != payload.project_id:
        raise HTTPException(
            status_code=400, detail="Item does not belong to the given project"
        )

    item.is_selected = not bool(item.is_selected)
    await db.commit()
    await db.refresh(item)

    return ItemSelectionResponse(
        project_id=item.project_id,
        item_type=item_type,
        item_id=item.id,
        is_selected=item.is_selected,
        message="Item selection toggled",
    )


async def _apply_bulk_selection(
    db: AsyncSession, project_id: int, item_type: str, desired_state: bool
):
    model = _get_model_or_404(item_type)
    await _ensure_project_unlocked(db, project_id)
    items = await _list_items_for_project(db, model, project_id)

    updated_count = 0
    for item in items:
        if item.is_selected != desired_state:
            item.is_selected = desired_state
            updated_count += 1

    await db.commit()

    selected_count = len([i for i in items if i.is_selected])
    total_count = len(items)

    return BulkSelectionResponse(
        project_id=project_id,
        item_type=item_type,
        updated_count=updated_count,
        selected_count=selected_count,
        total_count=total_count,
    )


@router.post(
    "/projects/{project_id}/items/{item_type}/select-all",
    response_model=BulkSelectionResponse,
)
async def select_all_items(
    project_id: int,
    item_type: str,
    db: AsyncSession = Depends(get_db),
):
    """Mark all items of the given type as selected for a project."""
    return await _apply_bulk_selection(db, project_id, item_type, True)


@router.post(
    "/projects/{project_id}/items/{item_type}/deselect-all",
    response_model=BulkSelectionResponse,
)
async def deselect_all_items(
    project_id: int,
    item_type: str,
    db: AsyncSession = Depends(get_db),
):
    """Mark all items of the given type as unselected for a project."""
    return await _apply_bulk_selection(db, project_id, item_type, False)


@router.get(
    "/projects/{project_id}/items/{item_type}/selection-summary",
    response_model=SelectionSummaryResponse,
)
async def get_selection_summary(
    project_id: int,
    item_type: str,
    db: AsyncSession = Depends(get_db),
):
    """Return selection counts for a project's items of a given type."""
    model = _get_model_or_404(item_type)
    await _ensure_project_exists(db, project_id)
    items = await _list_items_for_project(db, model, project_id)

    selected_count = len([i for i in items if i.is_selected])
    total_count = len(items)

    return SelectionSummaryResponse(
        project_id=project_id,
        item_type=item_type,
        selected_count=selected_count,
        total_count=total_count,
    )
