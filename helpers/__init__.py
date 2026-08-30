import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from config import Config

BASE = declarative_base()

db_dir = os.path.dirname(Config.DATABASE_PATH)
if db_dir:
    os.makedirs(db_dir, exist_ok=True)

_engine = create_engine(f"sqlite:///{Config.DATABASE_PATH}")
SESSION = scoped_session(sessionmaker(bind=_engine, autoflush=False))

# Import model modules so their tables register on BASE.metadata before
# create_all runs below. Must happen after BASE/SESSION are defined, since
# these modules import BASE/SESSION back from this package.
from helpers import gDrive_sql, parent_id_sql  # noqa: E402,F401

BASE.metadata.create_all(_engine)
