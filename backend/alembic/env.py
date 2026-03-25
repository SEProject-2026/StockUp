from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
import os
import sys
from dotenv import load_dotenv
from src.infrastructure.db.database import Base
from src.infrastructure.db.models import UserModel

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
# target_metadata = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

load_dotenv()

# 1. שולפים את הכתובת מה-env באופן מפורש
db_url = os.getenv("DATABASE_URL")

# בדיקת הגנה: אם אין כתובת, נעצור הכל כדי שלא ינסה להתחבר לכתובות דמה
if not db_url:
    raise ValueError("❌ DATABASE_URL is missing! Please check your .env file.")

config.set_main_option("sqlalchemy.url", db_url)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=db_url, # הזרקנו פה את הכתובת ישירות
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    
    # 2. מושכים את ההגדרות של ה-ini
    ini_section = config.get_section(config.config_ini_section, {})
    
    # 3. דורסים בכוח את ה-URL בתוך המילון עם הכתובת האמיתית מה-env!
    ini_section["sqlalchemy.url"] = db_url

    connectable = engine_from_config(
        ini_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()