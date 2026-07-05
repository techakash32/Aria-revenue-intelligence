"""Unit tests for the SQL safety validator. No DB required."""
import pytest

from safety.sql_validator import validate_query


@pytest.mark.parametrize(
    "query",
    [
        "SELECT * FROM daily_sales",
        "SELECT date, SUM(total_revenue) FROM daily_sales GROUP BY date",
        "  select product_name from daily_sales limit 5  ",
    ],
)
def test_allows_select_statements(query):
    is_safe, reason = validate_query(query)
    assert is_safe is True
    assert reason == "OK"


@pytest.mark.parametrize(
    "query",
    [
        "DROP TABLE daily_sales",
        "DELETE FROM daily_sales WHERE id = 1",
        "UPDATE daily_sales SET total_revenue = 0",
        "INSERT INTO daily_sales VALUES (1, 2, 3)",
        "TRUNCATE TABLE daily_sales",
        "ALTER TABLE daily_sales ADD COLUMN x INT",
        "CREATE TABLE evil (id INT)",
    ],
)
def test_blocks_mutating_statements(query):
    is_safe, reason = validate_query(query)
    assert is_safe is False


def test_blocks_empty_query():
    is_safe, reason = validate_query("")
    assert is_safe is False
    assert reason == "Empty query"


def test_blocks_whitespace_only_query():
    is_safe, reason = validate_query("   \n\t  ")
    assert is_safe is False


def test_blocks_stacked_statement_with_drop():
    """Regression test: a leading SELECT must not let a later DROP smuggle through."""
    is_safe, reason = validate_query("SELECT * FROM daily_sales; DROP TABLE daily_sales;")
    assert is_safe is False
    assert "multiple statements" in reason.lower()
