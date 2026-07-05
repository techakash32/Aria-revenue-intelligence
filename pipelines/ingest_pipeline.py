import csv
import logging
import os

import mysql.connector
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST"),
    "port": int(os.getenv("MYSQL_PORT", 3306)),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE"),
}

def ingest_csv(file_path: str):
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()
    with open(file_path, "r") as f:
        reader = csv.DictReader(f)
        rows = [
            (
                row["date"],
                row["product_id"],
                row["product_name"],
                row["category"],
                int(row["quantity"]),
                float(row["unit_price"]),
                float(row["total_revenue"]),
            )
            for row in reader
        ]
    cur.executemany(
        """INSERT IGNORE INTO daily_sales
           (date, product_id, product_name, category, quantity, unit_price, total_revenue)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        rows
    )
    conn.commit()
    cur.close()
    conn.close()
    logging.info(f"Ingested {len(rows)} rows from {file_path}")

# __main__ unchanged
