from typing import Any

from sqlalchemy import Boolean, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class Scenario(Base):
    """A published or unpublished BodyLingo learning scenario."""

    __tablename__ = "scenarios"

    id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    learning_objectives: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    media_placeholder: Mapped[str] = mapped_column(
        String(200), nullable=False, default="Text-based practice; no media asset is included."
    )
    start_node_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    nodes: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )
    published: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
