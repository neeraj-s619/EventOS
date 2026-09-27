from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

from app.core.config import settings
from app.models.database import Base


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.debug
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        try:
            event_cols = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(events)").fetchall()]
            for col, col_type in [
                ("city", "VARCHAR(50)"), ("state", "VARCHAR(50)"), ("country", "VARCHAR(50)"),
                ("venue_id", "VARCHAR(32)"), ("event_type", "VARCHAR(100)"),
                ("source_type", "VARCHAR(50)"), ("source_url", "VARCHAR(255)"), ("data_status", "VARCHAR(50)")
            ]:
                if col not in event_cols:
                    conn.exec_driver_sql(f"ALTER TABLE events ADD COLUMN {col} {col_type}")

            zone_cols = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(zones)").fetchall()]
            for col, col_type in [
                ("venue_id", "VARCHAR(32)"), ("description", "TEXT"), ("operational_capacity", "INTEGER"),
                ("latitude", "FLOAT"), ("longitude", "FLOAT"), ("source_type", "VARCHAR(50)")
            ]:
                if col not in zone_cols:
                    conn.exec_driver_sql(f"ALTER TABLE zones ADD COLUMN {col} {col_type}")

            prov_cols = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(providers)").fetchall()]
            for col, col_type in [
                ("source_type", "VARCHAR(50)"), ("source_name", "VARCHAR(100)"), ("location", "VARCHAR(255)")
            ]:
                if col not in prov_cols:
                    conn.exec_driver_sql(f"ALTER TABLE providers ADD COLUMN {col} {col_type}")

            conn.commit()
        except Exception:
            pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()