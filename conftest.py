from contextlib import closing

import pytest

import inventory_db
import seed_db


@pytest.fixture
def conn():
    """A fresh in-memory database per test, with foreign keys on."""
    # ":memory:" is sqlite's name for a database that is not a file.
    # It only lasts until this connection closes, so tests can't step on each other.
    with closing(inventory_db.connect(":memory:")) as connection:
        inventory_db.init_schema(connection)
        yield connection


@pytest.fixture
def seeded(conn):
    """The in-memory database loaded with the sample data from seed_db.py."""
    seed_db.seed(conn)
    return conn
