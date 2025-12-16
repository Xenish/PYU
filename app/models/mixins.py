from sqlalchemy import Boolean, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column


class EnhancedItemMixin:
    """Decision support metadata for wizard items."""

    priority_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    impact_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    recommendation_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    category_tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    advantages: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    disadvantages: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    conflicts_with: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    requires: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    category_exclusive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
