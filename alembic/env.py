from logging.config import fileConfig
import os
import sys

from sqlalchemy import engine_from_config, pool
from alembic import context

# Ensure app package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.config import get_settings
from app.database import Base, engine
from app.models import *  # noqa: F401, F403

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata

settings = get_settings()
if settings.database_url:
    config.set_main_option("sqlalchemy.url", settings.database_url)


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
