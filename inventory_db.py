import os
import sqlite3
from pathlib import Path

DEFAULT_DB = Path(__file__).with_name("inventory.db")
SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def connect(db_path=None):
    """Open the database with foreign keys on and rows readable by column name."""
    if db_path is None:
        db_path = os.environ.get("INVENTORY_DB")
    if db_path is None:
        db_path = DEFAULT_DB

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # This has to happen on every connection. It is not saved in the file.
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn):
    """Create any missing tables. Running this again leaves existing data in place."""
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema_sql)


def add_product(conn, sku, name, category, supplier_id, unit_price_cents, quantity_in_stock=0, reorder_level=0):
    """Add a product and return its new id."""
    cursor = conn.execute(
        "INSERT INTO products (sku, name, category, supplier_id, unit_price_cents, quantity_in_stock, reorder_level) " \
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (sku, name, category, supplier_id, unit_price_cents, quantity_in_stock, reorder_level),
    )
    conn.commit()
    return cursor.lastrowid


def get_product(conn, product_id):
    """Return one product and its supplier's name, or None."""
    return conn.execute(
        "SELECT p.*, s.name AS supplier_name FROM products p " \
        "INNER JOIN suppliers s ON p.supplier_id = s.id " \
        "WHERE p.id = ?",
        (product_id,)
    ).fetchone()


def update_price(conn, product_id, new_price_cents):
    """Change a product's price. Return False if it does not exist."""
    cursor = conn.execute(
        "UPDATE products SET unit_price_cents = ? " \
        "WHERE id = ?",
        (new_price_cents, product_id)
    )
    conn.commit()
    return cursor.rowcount == 1


def delete_product(conn, product_id):
    """Delete a product. Return False if it does not exist."""
    cursor = conn.execute(
        "DELETE FROM products WHERE id = ?",
        (product_id,)
    )
    conn.commit()
    return cursor.rowcount == 1


def search_products(conn, text="", category=None, max_price_cents=None, in_stock_only=False, low_stock_only=False):
    """Find products by name, SKU, or supplier, with optional filters."""
    # LIKE ignores case for ordinary letters. None or 0 means that filter is off.
    like = "%" + text + "%"
    return conn.execute(
        "SELECT p.*, s.name AS supplier_name FROM products p " \
        "INNER JOIN suppliers s ON p.supplier_id = s.id " \
        "WHERE (p.name LIKE ? OR p.sku LIKE ? OR s.name LIKE ?) " \
        "AND (? IS NULL OR p.category = ?) " \
        "AND (? IS NULL OR p.unit_price_cents <= ?) " \
        "AND (? = 0 OR p.quantity_in_stock > 0) " \
        "AND (? = 0 OR p.quantity_in_stock <= p.reorder_level) " \
        "ORDER BY p.name",
        (like, like, like, category, category, max_price_cents, max_price_cents, in_stock_only, low_stock_only),
    ).fetchall()