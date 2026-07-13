"""
One‑time script to create the `daily_sales` table and seed sample data.
Run: python data/seed_db.py
"""
import os

import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", 3306)),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE"),
}

SQL_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS daily_sales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    product_id VARCHAR(20) NOT NULL,
    product_name VARCHAR(100),
    category VARCHAR(50),
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_revenue DECIMAL(12,2) NOT NULL
);
"""

SQL_INSERT = """
INSERT IGNORE INTO daily_sales
(date, product_id, product_name, category, quantity, unit_price, total_revenue)
VALUES (%s, %s, %s, %s, %s, %s, %s)
"""

# Sample data (30 rows – 20 clean + 10 with anomalies)
DATA = [
    # 20 clean rows
    ('2026-01-05', 'P1001', 'Laptop', 'Electronics', 5, 800.00, 4000.00),
    ('2026-01-07', 'P1002', 'Smartphone', 'Electronics', 10, 500.00, 5000.00),
    ('2026-01-10', 'P1003', 'Desk Chair', 'Furniture', 8, 120.00, 960.00),
    ('2026-01-12', 'P1004', 'Notebook', 'Stationery', 50, 2.50, 125.00),
    ('2026-01-15', 'P1005', 'Headphones', 'Electronics', 15, 45.00, 675.00),
    ('2026-01-18', 'P1006', 'Coffee Table', 'Furniture', 3, 250.00, 750.00),
    ('2026-01-20', 'P1007', 'Pen Set', 'Stationery', 100, 1.20, 120.00),
    ('2026-01-22', 'P1008', 'Monitor', 'Electronics', 7, 300.00, 2100.00),
    ('2026-01-25', 'P1001', 'Laptop', 'Electronics', 2, 800.00, 1600.00),
    ('2026-01-28', 'P1009', 'Office Desk', 'Furniture', 4, 450.00, 1800.00),
    ('2026-02-01', 'P1010', 'USB Cable', 'Accessories', 200, 5.00, 1000.00),
    ('2026-02-03', 'P1011', 'Keyboard', 'Electronics', 12, 65.00, 780.00),
    ('2026-02-05', 'P1012', 'Mouse', 'Electronics', 25, 20.00, 500.00),
    ('2026-02-07', 'P1013', 'Bookcase', 'Furniture', 2, 180.00, 360.00),
    ('2026-02-10', 'P1014', 'Eraser', 'Stationery', 500, 0.50, 250.00),
    ('2026-02-12', 'P1015', 'Webcam', 'Electronics', 6, 90.00, 540.00),
    ('2026-02-15', 'P1016', 'Sofa', 'Furniture', 1, 1200.00, 1200.00),
    ('2026-02-18', 'P1017', 'Sticky Notes', 'Stationery', 300, 1.00, 300.00),
    ('2026-02-20', 'P1018', 'Router', 'Electronics', 9, 75.00, 675.00),
    ('2026-02-22', 'P1019', 'Lamp', 'Furniture', 7, 40.00, 280.00),

]

def main():
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(SQL_CREATE_TABLE)
    conn.commit()

    cur.executemany(SQL_INSERT, DATA)
    conn.commit()
    cur.close()
    conn.close()
    print(f"Seeded {len(DATA)} rows.")

if __name__ == "__main__":
    main()
