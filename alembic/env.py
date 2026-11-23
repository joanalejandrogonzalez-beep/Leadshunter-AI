import os
import sys
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Agregar raíz del proyecto a sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Asignar metadata y URL de base de datos desde leadhunter
try:
    from leadhunter.models.schema import Base
    from leadhunter.database import DATABASE_URL
    target_metadata = Base.metadata
    if DATABASE_URL:
        # Reemplazar esquema postgres:// por postgresql:// si viene de servicios cloud como Supabase/Heroku
        norm_url = DATABASE_URL
        if norm_url.startswith("postgres://"):
            norm_url = norm_url.replace("postgres://", "postgresql://", 1)
        config.set_main_option("sqlalchemy.url", norm_url)
except Exception:
    target_metadata = None


def run_migrations_offline() -> None:
    """Ejecución de migraciones en modo offline (generación de SQL)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Ejecución de migraciones en modo online contra el motor activo."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
