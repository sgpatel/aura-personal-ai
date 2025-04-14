# alembic/env.py
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# --- Add project root to path ---
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))
# --- End Path Addition ---

# --- Import application's Base and Models ---
from backend.db.base_class import Base
from backend.db import models # noqa - Ensures models are loaded
# --- End Application Imports ---

# --- Import settings to get database URL ---
from backend.core.config import settings # noqa
# --- End Settings Import ---


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Set target metadata ---
target_metadata = Base.metadata
# --- End Target Metadata ---


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = str(settings.DATABASE_URL)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # --- Use DATABASE_URL from settings ---
    # Get section from config object using the correct attribute name
    # FIX: Changed config.config_main_section -> config.config_ini_section
    configuration = config.get_section(config.config_ini_section)
    if configuration is None:
        configuration = {}
    configuration["sqlalchemy.url"] = str(settings.DATABASE_URL)

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    # --- End URL Configuration ---

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata,
            # Include pgvector types for autogenerate support if needed
            # process_revision_directives=process_revision_directives, # See Alembic docs for complex types
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
