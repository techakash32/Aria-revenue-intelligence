import os

import pytest
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture(scope="session")
def db_connection():
    """Live MySQL connection for integration tests.

    Only imported/connected lazily, inside the fixture body, so unit tests
    that don't request this fixture (most of the suite) can run without a
    database — e.g. in CI. Tests using this fixture are skipped if MySQL
    isn't reachable rather than failing the whole run.
    """
    mysql = pytest.importorskip("mysql.connector")
    try:
        conn = mysql.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", 3306)),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE"),
            connection_timeout=3,
        )
    except Exception as exc:
        pytest.skip(f"MySQL not reachable, skipping integration test: {exc}")
    yield conn
    conn.close()
