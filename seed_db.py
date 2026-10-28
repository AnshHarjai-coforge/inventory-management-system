from contextlib import closing

from inventory_db import connect, init_schema

SUPPLIERS = [
    (1, "Northwind Tools"),
    (2, "Ironclad Fasteners"),
    (3, "BrightSpark Electrical"),
    (4, "Garden & Grove"),
]

PRODUCTS = [
    (1, "HT-001", "Claw Hammer 16oz", "Hand Tools", 1, 1899, 40, 10),
    (2, "HT-002", "Screwdriver Set 6pc", "Hand Tools", 1, 2450, 25, 8),
    (3, "HT-003", "Adjustable Wrench 10in", "Hand Tools", 1, 1550, 6, 10),
    (4, "HT-004", "Tape Measure 8m", "Hand Tools", 1, 1200, 60, 15),
    (5, "FS-001", "Wood Screws 4x40 (100pk)", "Fasteners", 2, 650, 200, 50),
    (6, "FS-002", "Hex Bolts M8 (50pk)", "Fasteners", 2, 980, 45, 20),
    (7, "FS-003", "Wall Plugs (200pk)", "Fasteners", 2, 450, 12, 12),
    (8, "EL-001", "LED Bulb 9W", "Electrical", 3, 799, 150, 40),
    (9, "EL-002", "Extension Lead 4-way", "Electrical", 3, 1499, 30, 10),
    (10, "EL-003", "Cable Clips (100pk)", "Electrical", 3, 399, 80, 25),
    (11, "GD-001", "Garden Hose 15m", "Garden", 4, 2999, 18, 5),
    (12, "GD-002", "Pruning Shears", "Garden", 4, 1750, 9, 12),
]

SALES = [
    (1, "2026-01-05T10:15:00Z"),
    (2, "2026-01-12T14:40:00Z"),
    (3, "2026-02-02T09:05:00Z"),
    (4, "2026-02-14T16:20:00Z"),
    (5, "2026-03-01T11:00:00Z"),
]

# sale_id, product_id, quantity, unit_price_cents
SALE_ITEMS = [
    (1, 1, 2, 1899),
    (1, 5, 5, 650),
    (1, 8, 10, 799),
    (2, 2, 1, 2450),
    (2, 9, 2, 1499),
    (3, 1, 1, 1799),
    (3, 6, 4, 980),
    (3, 11, 1, 2999),
    (4, 4, 3, 1200),
    (4, 7, 2, 450),
    (5, 8, 6, 799),
    (5, 3, 1, 1550),
]


def seed(conn):
    """Load the sample rows. The caller must already have created the tables."""
    with conn:
        conn.executemany(
            "INSERT INTO suppliers (id, name) VALUES (?, ?)",
            SUPPLIERS,
        )
        conn.executemany(
            """INSERT INTO products (
                   id, sku, name, category, supplier_id,
                   unit_price_cents, quantity_in_stock, reorder_level
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            PRODUCTS,
        )
        conn.executemany(
            "INSERT INTO sales (id, sold_at) VALUES (?, ?)",
            SALES,
        )
        conn.executemany(
            """INSERT INTO sale_items (
                   sale_id, product_id, quantity, unit_price_cents
               ) VALUES (?, ?, ?, ?)""",
            SALE_ITEMS,
        )


def main():
    with closing(connect()) as conn:
        init_schema(conn)
        seed(conn)
        for table in ("suppliers", "products", "sales", "sale_items", "stock_movements"):
            # table name is a literal from our own tuple, never user input
            count = conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
            print(f"{table}: {count}")


if __name__ == "__main__":
    main()
