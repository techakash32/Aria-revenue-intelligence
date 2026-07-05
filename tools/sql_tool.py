import logging
import os

import mysql.connector

from safety import execute_with_timeout, validate_query

logger = logging.getLogger(__name__)

QUERY_TIMEOUT = int(os.getenv("QUERY_TIMEOUT_SECONDS", "5"))


def get_readonly_config():
    return {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", 3306)),
        "user": os.getenv("MYSQL_READONLY_USER"),
        "password": os.getenv("MYSQL_READONLY_PASSWORD"),
        "database": os.getenv("MYSQL_DATABASE"),
    }


def get_app_db_config():
    return {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", 3306)),
        "user": os.getenv("MYSQL_USER"),
        "password": os.getenv("MYSQL_PASSWORD"),
        "database": os.getenv("MYSQL_DATABASE"),
    }


async def run_sql(query: str) -> dict:
    """Execute a read-only SQL query and return results as a dictionary."""
    is_safe, reason = validate_query(query)
    if not is_safe:
        logger.warning("Query blocked: %s", reason)
        return {"success": False, "error": f"Query blocked: {reason}", "data": None}

    conn = None
    try:
        try:
            conn = mysql.connector.connect(**get_readonly_config())
        except mysql.connector.Error as readonly_exc:
            logger.warning("Read-only DB user unavailable, falling back to app DB user: %s", readonly_exc)
            conn = mysql.connector.connect(**get_app_db_config())
        cur = conn.cursor(dictionary=True)
        rows = execute_with_timeout(cur, query, timeout_seconds=QUERY_TIMEOUT)
        columns = [desc[0] for desc in cur.description] if cur.description else []
        logger.info("Query executed: %d rows returned", len(rows))
        return {
            "success": True,
            "columns": columns,
            "data": rows,
            "row_count": len(rows),
        }
    except Exception as exc:
        logger.exception("SQL execution error")
        return {"success": False, "error": str(exc), "data": None}
    finally:
        if conn:
            conn.close()
