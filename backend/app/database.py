import logging
import time

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def wait_for_db(max_delay: float = 30.0) -> None:
    """Block until the database is reachable, retrying with backoff.

    The database may not be up yet on first boot (e.g. in Kubernetes, where
    there is no Compose-style depends_on startup ordering), so the backend
    must retry rather than crash and rely on the container being restarted.
    """
    delay = 1.0
    while True:
        try:
            with engine.connect():
                return
        except OperationalError:
            logger.warning("Database not reachable yet, retrying in %.0fs", delay)
            time.sleep(delay)
            delay = min(delay * 2, max_delay)
