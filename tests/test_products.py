import sqlite3

import pytest

import inventory_db as db


def test_add_product_returns_the_new_id(seeded):
    new_id = db.add_product(seeded, "ZZ-001", "Widget", "Tools", 1, 500)
    assert new_id == 13
    assert db.get_product(seeded, new_id)["name"] == "Widget"
    assert db.get_product(seeded, new_id)["quantity_in_stock"] == 0


def test_add_product_with_duplicate_sku_is_refused(seeded):
    with pytest.raises(sqlite3.IntegrityError):
        db.add_product(seeded, "HT-001", "Another Hammer", "Hand Tools", 1, 500)


def test_add_product_with_unknown_supplier_is_refused(seeded):
    with pytest.raises(sqlite3.IntegrityError):
        db.add_product(seeded, "ZZ-002", "Widget", "Tools", 99, 500)


@pytest.mark.parametrize("price, quantity", [
    (-1, 0),
    (100, -1),
])
def test_negative_price_or_quantity_is_refused(seeded, price, quantity):
    with pytest.raises(sqlite3.IntegrityError):
        db.add_product(seeded, "ZZ-009", "Widget", "Tools", 1, price, quantity)
    assert seeded.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 12


def test_get_product_returns_the_supplier_name(seeded):
    product = db.get_product(seeded, 1)
    assert product["sku"] == "HT-001"
    assert product["supplier_name"] == "Northwind Tools"


def test_get_product_returns_none_when_missing(seeded):
    assert db.get_product(seeded, 999) is None


def test_product_text_is_never_run_as_sql(seeded):
    text = "'; DROP TABLE products; --"
    new_id = db.add_product(seeded, "ZZ-010", text, "Tools", 1, 500)
    assert db.get_product(seeded, new_id)["name"] == text
    assert db.get_product(seeded, 1)["sku"] == "HT-001"


def test_update_price_changes_the_price(seeded):
    assert db.update_price(seeded, 1, 2000) is True
    assert db.get_product(seeded, 1)["unit_price_cents"] == 2000


def test_update_price_for_missing_product_returns_false(seeded):
    assert db.update_price(seeded, 999, 2000) is False


def test_a_product_that_was_sold_cannot_be_deleted(seeded):
    with pytest.raises(sqlite3.IntegrityError):
        db.delete_product(seeded, 1)


def test_a_product_that_was_never_sold_can_be_deleted(seeded):
    assert db.delete_product(seeded, 10) is True
    assert db.get_product(seeded, 10) is None
