from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy import inspect
from sqlalchemy.orm import Session, sessionmaker


@dataclass
class DBManager:
    database_url: str

    def __post_init__(self) -> None:
        connect_args = {"check_same_thread": False} if self.database_url.startswith("sqlite") else {}
        self.engine: Engine = create_engine(self.database_url, future=True, connect_args=connect_args)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, future=True)

    def create_all(self, metadata) -> None:
        metadata.create_all(bind=self.engine)

    def has_all_tables(self, metadata) -> bool:
        inspector = inspect(self.engine)
        existing = set(inspector.get_table_names())
        expected = set(metadata.tables.keys())
        return bool(expected) and expected.issubset(existing)

    def session(self) -> Session:
        return self.SessionLocal()
