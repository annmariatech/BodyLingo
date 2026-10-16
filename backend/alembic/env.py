from logging.config import fileConfig
from pathlib import Path
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from database import Base, database_url
import models.learning  # noqa: F401; registers learning tables with Base.metadata
import models.user  # noqa: F401; registers account tables with Base.metadata
from backend.models.completed_lesson import CompletedLesson  # noqa: F401
from backend.models.scenario import Scenario  # noqa: F401
from backend.models.scenario_response import ScenarioResponse  # noqa: F401
from backend.models.scenario_session import ScenarioSession  # noqa: F401
from backend.models.user_progress import UserProgress  # noqa: F401
from backend.models.base import Base as ScenarioBase

config = context.config
config.set_main_option("sqlalchemy.url", database_url().replace("%", "%%"))
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = [Base.metadata, ScenarioBase.metadata]


def run_migrations_offline() -> None:
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
