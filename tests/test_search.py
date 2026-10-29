import inventory_db as db


def test_search_matches_a_product_by_name(seeded):
    assert len(db.search_products(seeded, "hammer")) == 1


def test_search_text_is_never_run_as_sql(seeded):
    assert db.search_products(seeded, "'; DROP TABLE products; --") == []
