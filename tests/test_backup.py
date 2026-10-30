from contextlib import closing

import inventory_db as db


def test_backup_matches_the_open_database(seeded, tmp_path):
    destination = tmp_path / "backup.db"
    db.backup_database(seeded, destination)
    with closing(db.connect(destination)) as copy:
        check = copy.execute("PRAGMA integrity_check").fetchone()[0]
        assert check == "ok"
        original = seeded.execute("SELECT COUNT(*) AS n FROM suppliers").fetchone()["n"]
        copied = copy.execute("SELECT COUNT(*) AS n FROM suppliers").fetchone()["n"]
        assert copied == original
        original = seeded.execute("SELECT COUNT(*) AS n FROM products").fetchone()["n"]
        copied = copy.execute("SELECT COUNT(*) AS n FROM products").fetchone()["n"]
        assert copied == original
        original = seeded.execute("SELECT COUNT(*) AS n FROM sales").fetchone()["n"]
        copied = copy.execute("SELECT COUNT(*) AS n FROM sales").fetchone()["n"]
        assert copied == original
        original = seeded.execute("SELECT COUNT(*) AS n FROM sale_items").fetchone()["n"]
        copied = copy.execute("SELECT COUNT(*) AS n FROM sale_items").fetchone()["n"]
        assert copied == original
        original = seeded.execute("SELECT COUNT(*) AS n FROM stock_movements").fetchone()["n"]
        copied = copy.execute("SELECT COUNT(*) AS n FROM stock_movements").fetchone()["n"]
        assert copied == original
