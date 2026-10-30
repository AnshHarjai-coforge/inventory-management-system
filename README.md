# inventory-management-system

A hardware store keeps its stock, prices, and sales in a SQLite database. The terminal menu searches products, looks one up, adds one, restocks, records a sale, runs four reports, and backs up the database. Prices are stored as whole cents and shown with two decimals.

## How to run it

From the project folder, load the sample data, then start the menu:

```bash
python seed_db.py
python main.py
```

`seed_db.py` creates the tables and prints a row count for each one. `python main.py` opens the menu.

1. Search products
2. Look up a product
3. Add a product
4. Restock
5. Record a sale
6. Stock value by supplier
7. Low stock
8. Sales by product
9. Products never sold
10. Back up the database
0. Quit

## Configuration

`INVENTORY_DB` is the path to the database file. When it is not set, the program uses `inventory.db` next to the code.

## Tests

```bash
pytest -q
ruff check .
```

## Reports

Prices are stored as whole cents. The dollar column is the cents divided by 100, shown with two decimals. These are the rows the sample data produces.

### Stock value by supplier

| Supplier | Cents | Dollars |
| --- | --- | --- |
| Northwind Tools | 218510 | 2185.10 |
| BrightSpark Electrical | 196740 | 1967.40 |
| Ironclad Fasteners | 179500 | 1795.00 |
| Garden & Grove | 69732 | 697.32 |

### Low stock

| SKU | Name | On hand | Reorder level | Units short |
| --- | --- | --- | --- | --- |
| HT-003 | Adjustable Wrench 10in | 6 | 10 | 4 |
| GD-002 | Pruning Shears | 9 | 12 | 3 |
| FS-003 | Wall Plugs (200pk) | 12 | 12 | 0 |

### Sales by product

| SKU | Name | Units sold | Cents | Dollars |
| --- | --- | --- | --- | --- |
| EL-001 | LED Bulb 9W | 16 | 12784 | 127.84 |
| HT-001 | Claw Hammer 16oz | 3 | 5597 | 55.97 |
| FS-002 | Hex Bolts M8 (50pk) | 4 | 3920 | 39.20 |
| HT-004 | Tape Measure 8m | 3 | 3600 | 36.00 |
| FS-001 | Wood Screws 4x40 (100pk) | 5 | 3250 | 32.50 |
| GD-001 | Garden Hose 15m | 1 | 2999 | 29.99 |
| EL-002 | Extension Lead 4-way | 2 | 2998 | 29.98 |
| HT-002 | Screwdriver Set 6pc | 1 | 2450 | 24.50 |
| HT-003 | Adjustable Wrench 10in | 1 | 1550 | 15.50 |
| FS-003 | Wall Plugs (200pk) | 2 | 900 | 9.00 |

### Never sold

| SKU | Name | Category |
| --- | --- | --- |
| EL-003 | Cable Clips (100pk) | Electrical |
| GD-002 | Pruning Shears | Garden |

## A sale that fails halfway

The first line sells 1 claw hammer, which is in stock. The second line asks for 7 adjustable wrenches, and only 6 are on the shelf. The error happens on that second line, and the hammer line is rolled back with it.

### Before

| | |
| --- | --- |
| sales | 5 |
| sale_items | 12 |
| stock_movements | 0 |
| HT-001 Claw Hammer 16oz | 40 on hand, current price 1899 cents |
| HT-003 Adjustable Wrench 10in | 6 on hand |

```python
record_sale(conn, [(1, 1), (3, 7)], "2026-04-01T12:00:00Z")
```

```text
sqlite3.IntegrityError: CHECK constraint failed: quantity_in_stock >= 0
```

### After

| | |
| --- | --- |
| sales | 5 |
| sale_items | 12 |
| stock_movements | 0 |
| HT-001 Claw Hammer 16oz | 40 on hand, current price 1899 cents |
| HT-003 Adjustable Wrench 10in | 6 on hand |

## Docker

Build the image, then run the menu with `-it`. The database file lives on a volume. `INVENTORY_DB` points at it.

```bash
docker build -t inventory:1.0.0 .
docker volume create inventory-data
docker run -it --rm \
  -e INVENTORY_DB=/data/inventory.db \
  -v inventory-data:/data \
  inventory:1.0.0
```

The image uses Python 3.15.0. CI builds it and runs the tests inside it. Tag `v1.0.0` on main after this branch is merged.

The end of the build looked like this:

```text
#8 3.536 Successfully installed iniconfig-2.3.1 packaging-26.3 pluggy-1.7.0 pygments-2.21.0 pytest-9.1.1 ruff-0.17.3
#9 [5/5] COPY . .
#9 DONE 0.0s
#10 naming to docker.io/library/inventory:1.0.0 done
#10 DONE 1.5s
```

I loaded the sample data into the volume:

```bash
docker run --rm \
  -e INVENTORY_DB=/data/inventory.db \
  -v inventory-data:/data \
  inventory:1.0.0 \
  python seed_db.py
```

```text
suppliers: 4
products: 12
sales: 5
sale_items: 12
stock_movements: 0
```

Then I added a product in one container. It printed `Added product 13.` I started a new container with the same volume and looked up id 13. It printed:

```text
ZZ-001 Demo Widget Hand Tools Northwind Tools 1.00 qty 5 reorder 2
```

## Backup and restore

Option 10 asks for a file path and copies the database. To put it back, quit the program and copy that file over the database file.

I checked a backup of the sample data:

```text
Backup saved to /tmp/inventory-check/backup.db.
ok
ok
suppliers|4
products|12
sales|5
sale_items|12
stock_movements|0
suppliers|4
products|12
sales|5
sale_items|12
stock_movements|0
```

Both `PRAGMA integrity_check` results are `ok`. The row counts match.

```bash
cp /tmp/inventory-check/backup.db /tmp/inventory-check/inventory.db
```

In Docker, save the backup on the volume, such as `/data/inventory-backup.db`. After the container stops:

```bash
docker run --rm -v inventory-data:/data inventory:1.0.0 \
  cp /data/inventory-backup.db /data/inventory.db
```

## Rollback

Version 1.1.0 only adds a low-stock count when the menu starts. The tables stay the same. To go back, run the 1.0.0 image with the same volume:

```bash
docker run -it --rm \
  -e INVENTORY_DB=/data/inventory.db \
  -v inventory-data:/data \
  inventory:1.0.0
```

The count goes away. The rows stay. I will paste that output after the 1.1.0 image exists.
