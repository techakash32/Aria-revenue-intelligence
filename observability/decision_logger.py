import json
import logging
import os
from datetime import date, datetime, timezone
from decimal import Decimal

import mysql.connector

logger = logging.getLogger(__name__)

def get_db_config():
    return {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", 3306)),
        "user": os.getenv("MYSQL_USER"),
        "password": os.getenv("MYSQL_PASSWORD"),
        "database": os.getenv("MYSQL_DATABASE"),
    }

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS agent_decisions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    input JSON,
    output JSON,
    confidence FLOAT,
    action_taken VARCHAR(255)
);
"""

def log_decision(
    agent_id: str,
    input_data: dict,
    output_data: dict,
    confidence: float,
    action_taken: str,
):
    try:
        ensure_decision_table()
        conn = mysql.connector.connect(**get_db_config())
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO agent_decisions
               (agent_id, timestamp, input, output, confidence, action_taken)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (
                agent_id,
                datetime.now(timezone.utc),
                json.dumps(input_data, default=json_default),
                json.dumps(output_data, default=json_default),
                confidence,
                action_taken,
            ),
        )
        conn.commit()
        cur.close()
        conn.close()
        logger.debug("Logged decision for agent %s", agent_id)
    except Exception:
        logger.exception("Failed to log decision for %s", agent_id)


def ensure_decision_table() -> None:
    conn = mysql.connector.connect(**get_db_config())
    try:
        cur = conn.cursor()
        cur.execute(CREATE_TABLE_SQL)
        conn.commit()
        cur.close()
    finally:
        conn.close()


def json_default(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)
