from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

import reach.core.db.init as db_init
from reach.core.db.base import Base
from reach.core.db.models import Route


@pytest.fixture
def isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_file = tmp_path / "reach_test.db"
    test_engine = create_engine(f"sqlite:///{db_file}", future=True)

    # Reset + rebuild schema against an isolated test database.
    Base.metadata.drop_all(bind=test_engine)
    monkeypatch.setattr(db_init, "engine", test_engine)
    monkeypatch.setattr(db_init, "_db_initialized", False)
    db_init.init_db(force=True)

    return db_file, test_engine


@pytest.mark.e2e
@pytest.mark.integration
def test_db_rebuild_creates_sqlite_file(isolated_db) -> None:
    db_file, _ = isolated_db
    assert db_file.exists(), f"Expected SQLite DB file to be created at {db_file}"


@pytest.mark.e2e
@pytest.mark.integration
def test_db_connection_is_accessible(isolated_db) -> None:
    _, test_engine = isolated_db
    with test_engine.connect() as conn:
        value = conn.execute(text("SELECT 1")).scalar_one()
    assert value == 1


@pytest.mark.e2e
@pytest.mark.integration
def test_db_rebuild_creates_expected_tables(isolated_db) -> None:
    _, test_engine = isolated_db
    expected_tables = {
        "routes",
        "request_logs",
        "trigger_rules",
        "rule_state",
        "dns_zones",
    }
    actual_tables = set(inspect(test_engine).get_table_names())
    missing = expected_tables - actual_tables
    assert not missing, f"Missing expected DB tables: {sorted(missing)}"


@pytest.mark.e2e
@pytest.mark.integration
def test_db_read_write_round_trip(isolated_db) -> None:
    _, test_engine = isolated_db
    Session = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)
    with Session() as session:
        route = Route(
            method="GET",
            path="/db-health-check",
            status_code=200,
            response_body="ok",
            content_type="text/plain",
        )
        session.add(route)
        session.commit()

        loaded = session.query(Route).filter(Route.path == "/db-health-check").first()
        assert loaded is not None
        assert loaded.response_body == "ok"
