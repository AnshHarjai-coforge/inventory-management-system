import inventory_db


def test_all_five_tables_exist(conn):
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    assert {row["name"] for row in rows} == {
        "suppliers",
        "products",
        "sales",
        "sale_items",
        "stock_movements",
    }


def test_init_schema_again_keeps_existing_rows(conn):
    conn.execute("INSERT INTO suppliers (name) VALUES (?)", ("Northwind Tools",))
    conn.commit()
    inventory_db.init_schema(conn)
    count = conn.execute("SELECT COUNT(*) AS n FROM suppliers").fetchone()["n"]
    assert count == 1


def test_seed_row_counts(seeded):
    assert seeded.execute("SELECT COUNT(*) AS n FROM suppliers").fetchone()["n"] == 4
    assert seeded.execute("SELECT COUNT(*) AS n FROM products").fetchone()["n"] == 12
    assert seeded.execute("SELECT COUNT(*) AS n FROM sales").fetchone()["n"] == 5
    assert seeded.execute("SELECT COUNT(*) AS n FROM sale_items").fetchone()["n"] == 12
    assert seeded.execute("SELECT COUNT(*) AS n FROM stock_movements").fetchone()["n"] == 0
