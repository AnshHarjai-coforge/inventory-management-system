import inventory_db as db


def test_stock_value_by_supplier_report(seeded):
    rows = db.stock_value_by_supplier_report(seeded)
    assert [(row["supplier_name"], row["total_stock_value_cents"]) for row in rows] == [
        ("Northwind Tools", 218510),
        ("BrightSpark Electrical", 196740),
        ("Ironclad Fasteners", 179500),
        ("Garden & Grove", 69732),
    ]


def test_low_stock_report(seeded):
    rows = db.low_stock_report(seeded)
    assert [(row["sku"], row["name"], row["quantity_in_stock"], row["reorder_level"], row["units_short"]) for row in rows] == [
        ("HT-003", "Adjustable Wrench 10in", 6, 10, 4),
        ("GD-002", "Pruning Shears", 9, 12, 3),
        ("FS-003", "Wall Plugs (200pk)", 12, 12, 0),
    ]


def test_sales_by_product_report(seeded):
    rows = db.sales_by_product_report(seeded)
    assert [(row["sku"], row["name"], row["units_sold"], row["revenue_cents"]) for row in rows] == [
        ("EL-001", "LED Bulb 9W", 16, 12784),
        ("HT-001", "Claw Hammer 16oz", 3, 5597),
        ("FS-002", "Hex Bolts M8 (50pk)", 4, 3920),
        ("HT-004", "Tape Measure 8m", 3, 3600),
        ("FS-001", "Wood Screws 4x40 (100pk)", 5, 3250),
        ("GD-001", "Garden Hose 15m", 1, 2999),
        ("EL-002", "Extension Lead 4-way", 2, 2998),
        ("HT-002", "Screwdriver Set 6pc", 1, 2450),
        ("HT-003", "Adjustable Wrench 10in", 1, 1550),
        ("FS-003", "Wall Plugs (200pk)", 2, 900),
    ]


def test_never_sold_report(seeded):
    rows = db.never_sold_report(seeded)
    assert [(row["sku"], row["name"], row["category"]) for row in rows] == [
        ("EL-003", "Cable Clips (100pk)", "Electrical"),
        ("GD-002", "Pruning Shears", "Garden"),
    ]
