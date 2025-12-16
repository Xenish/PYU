from sqlalchemy import Select


def only_active(stmt: Select, model) -> Select:
    """Apply soft-delete filter if model has is_deleted flag."""
    is_deleted_col = getattr(model, "is_deleted", None)
    if is_deleted_col is not None:
        return stmt.where(is_deleted_col == False)  # noqa: E712
    return stmt
