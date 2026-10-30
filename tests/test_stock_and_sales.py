import sqlite3

import pytest

import inventory_db as db


def test_restock_increases_stock_and_logs_one_movement(seeded):
    assert db.restock(seeded, 1, 10, "2026-04-01T12:00:00Z") == 50
    assert db.get_product(seeded, 1)["quantity_in_stock"] == 50
    moves = seeded.execute("SELECT product_id, change, reason FROM stock_movements").fetchall()
    assert [tuple(row) for row in moves] == [(1, 10, "restock")]


def test_restock_of_zero_is_refused(seeded):
    with pytest.raises(sqlite3.IntegrityError):
        db.restock(seeded, 1, 0, "2026-04-01T12:00:00Z")
    assert db.get_product(seeded, 1)["quantity_in_stock"] == 40


def test_restock_below_zero_is_refused(seeded):
    with pytest.raises(ValueError):
        db.restock(seeded, 1, -5, "2026-04-01T12:00:00Z")
    assert db.get_product(seeded, 1)["quantity_in_stock"] == 40


def test_adjustment_that_would_go_negative_changes_nothing(seeded):
    with pytest.raises(sqlite3.IntegrityError):
        db.adjust_stock(seeded, 3, -7, "2026-04-01T12:00:00Z")
    assert db.get_product(seeded, 3)["quantity_in_stock"] == 6
    assert seeded.execute("SELECT COUNT(*) FROM stock_movements").fetchone()[0] == 0


def test_sale_records_lines_at_current_prices_and_reduces_stock(seeded):
    sale_id = db.record_sale(seeded, [(1, 2), (10, 1)], "2026-04-01T12:00:00Z")
    lines = seeded.execute(
        "SELECT product_id, quantity, unit_price_cents FROM sale_items WHERE sale_id = ? ORDER BY product_id",
        (sale_id,),
    ).fetchall()
    assert [tuple(line) for line in lines] == [(1, 2, 1899), (10, 1, 399)]
    assert db.get_product(seeded, 1)["quantity_in_stock"] == 38
    assert db.get_product(seeded, 10)["quantity_in_stock"] == 79
    moves = seeded.execute(
        "SELECT product_id, change, reason FROM stock_movements ORDER BY product_id"
    ).fetchall()
    assert [tuple(row) for row in moves] == [(1, -2, "sale"), (10, -1, "sale")]


def test_failed_sale_changes_nothing(seeded):
    sales_before = seeded.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    with pytest.raises(sqlite3.IntegrityError):
        db.record_sale(seeded, [(1, 1), (3, 7)], "2026-04-01T12:00:00Z")  # only 6 wrenches
    assert seeded.execute("SELECT COUNT(*) FROM sales").fetchone()[0] == sales_before
    assert db.get_product(seeded, 1)["quantity_in_stock"] == 40  # the first line was undone too
    assert db.get_product(seeded, 3)["quantity_in_stock"] == 6


def test_sale_for_unknown_product_changes_nothing(seeded):
    sales_before = seeded.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    with pytest.raises(ValueError):
        db.record_sale(seeded, [(1, 1), (999, 1)], "2026-04-01T12:00:00Z")
    assert seeded.execute("SELECT COUNT(*) FROM sales").fetchone()[0] == sales_before
    assert db.get_product(seeded, 1)["quantity_in_stock"] == 40
