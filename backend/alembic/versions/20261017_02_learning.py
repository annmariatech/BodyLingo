"""Add learning preferences, demo premium entitlement, attempts and review schedule."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261017_02"
down_revision: Union[str, None] = "20261017_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("preferences", sa.JSON(), nullable=False, server_default="{}"))
    op.add_column("users", sa.Column("is_premium", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_table(
        "lesson_attempts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lesson_id", sa.String(100), nullable=False),
        sa.Column("question_id", sa.String(100), nullable=False),
        sa.Column("selected_option_id", sa.String(100), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_lesson_attempts_user_id", "lesson_attempts", ["user_id"])
    op.create_index("ix_lesson_attempts_lesson_id", "lesson_attempts", ["lesson_id"])
    op.create_table(
        "lesson_completions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lesson_id", sa.String(100), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "lesson_id", name="uq_lesson_completion_user_lesson"),
    )
    op.create_index("ix_lesson_completions_user_id", "lesson_completions", ["user_id"])
    op.create_table(
        "question_reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lesson_id", sa.String(100), nullable=False),
        sa.Column("question_id", sa.String(100), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("interval_days", sa.Integer(), nullable=False),
        sa.Column("repetitions", sa.Integer(), nullable=False),
        sa.UniqueConstraint("user_id", "lesson_id", "question_id", name="uq_question_review_user_question"),
    )
    op.create_index("ix_question_reviews_user_id", "question_reviews", ["user_id"])
    op.create_index("ix_question_reviews_due_at", "question_reviews", ["due_at"])


def downgrade() -> None:
    op.drop_index("ix_question_reviews_due_at", table_name="question_reviews")
    op.drop_index("ix_question_reviews_user_id", table_name="question_reviews")
    op.drop_table("question_reviews")
    op.drop_index("ix_lesson_completions_user_id", table_name="lesson_completions")
    op.drop_table("lesson_completions")
    op.drop_index("ix_lesson_attempts_lesson_id", table_name="lesson_attempts")
    op.drop_index("ix_lesson_attempts_user_id", table_name="lesson_attempts")
    op.drop_table("lesson_attempts")
    op.drop_column("users", "is_premium")
    op.drop_column("users", "preferences")
