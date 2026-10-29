import os
import sqlite3
from pathlib import Path

DEFAULT_DB = Path(__file__).with_name("inventory.db")
SCHEMA_PATH = Path(__file__).with_name("schema.sql")

# Connection to Database

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


# Product - level Functions

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


#  Search Function

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


# Reports

def stock_value_by_supplier_report(conn):
    """Return each supplier's name and the total value of its stock, highest first."""
    return conn.execute("""
        SELECT s.name AS supplier_name,
               SUM(p.quantity_in_stock * p.unit_price_cents) AS total_stock_value_cents
          FROM suppliers s
          INNER JOIN products p ON s.id = p.supplier_id
         GROUP BY s.id, s.name
         ORDER BY total_stock_value_cents DESC, s.name
    """).fetchall()


def low_stock_report(conn):
    """Return each product at or below its reorder level, and how many units short it is."""
    return conn.execute("""
        SELECT sku, name, quantity_in_stock, reorder_level,
               (reorder_level - quantity_in_stock) AS units_short
          FROM products
         WHERE quantity_in_stock <= reorder_level
         ORDER BY units_short DESC, name
    """).fetchall()


def sales_by_product_report(conn):
    """Return each sold product with units sold and revenue, highest revenue first."""
    # Revenue uses the price stored on the sale line, not the product's current price.
    return conn.execute("""
        SELECT p.sku, p.name,
               SUM(si.quantity) AS units_sold,
               SUM(si.quantity * si.unit_price_cents) AS revenue_cents
          FROM sale_items si
          INNER JOIN products p ON p.id = si.product_id
         GROUP BY p.id, p.sku, p.name
         ORDER BY revenue_cents DESC, p.name
    """).fetchall()


def never_sold_report(conn):
    """Return products that appear in no sale."""
    return conn.execute("""
        SELECT sku, name, category
          FROM products
         WHERE NOT EXISTS (
             SELECT 1 FROM sale_items WHERE product_id = products.id
         )
         ORDER BY name
    """).fetchall()
