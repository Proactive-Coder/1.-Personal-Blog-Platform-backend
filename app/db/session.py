from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Generator
import logging

from app.config import settings

logger = logging.getLogger(__name__)


engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,

    echo=settings.DEBUG,    
)


# =============================================================================
#  Session Factory
# =============================================================================
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,   # always use explicit transactions
    autoflush=False,    # flush manually for full control
    expire_on_commit=False,  # keep objects accessible after commit
)


# =============================================================================
#  Base Model
# =============================================================================
class Base(DeclarativeBase):
    pass


# =============================================================================
#  Dependency  —  use this in every FastAPI route
# =============================================================================
def get_db() -> Generator[Session, None, None]:
    """
    Yields a DB session per request and guarantees cleanup.

    Usage in routes:
        def my_route(db: Session = Depends(get_db)):
            ...
    """
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()             # auto-commit if no exception was raised
    except SQLAlchemyError as e:
        db.rollback()           # rollback on any DB error
        logger.error(f"Database error: {e}", exc_info=True)
        raise
    finally:
        db.close()              # always release connection back to pool


# =============================================================================
#  Health Check  —  call from /health endpoint or app lifespan
# =============================================================================
def check_db_connection() -> bool:
    """Returns True if DB is reachable, False otherwise."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False