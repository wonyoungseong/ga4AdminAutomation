"""
Alembic environment configuration for async SQLAlchemy
"""

from logging.config import fileConfig
from typing import Optional

from sqlalchemy import pool
from sqlalchemy.engine import Connection

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

# Import models for autogenerate support
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.core.database import Base
from src.models.db_models import (
    User, Client, ServiceAccount, PermissionGrant, AuditLog, PasswordResetToken,
    ClientAssignment, PropertyAccessRequest, UserActivityLog, UserSession, 
    GA4Property, UserPermission, NotificationLog, ReportDownloadLog,
    ServiceAccountProperty, PropertyAccessBinding, PermissionRequest
)

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Get URL from alembic config or environment
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        # Fallback to environment variable
        from src.core.config import settings
        url = settings.database_url_sync
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    from sqlalchemy import engine_from_config
    
    # Get URL from config or environment
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        from src.core.config import settings
        url = settings.database_url_sync
    
    connectable = engine_from_config(
        {"sqlalchemy.url": url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()