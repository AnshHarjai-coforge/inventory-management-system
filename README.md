# inventory-management-system

A hardware store keeps its stock, prices, and sales in a SQLite database. The terminal menu searches products, looks one up, adds one, restocks, records a sale, runs four reports, and backs up the database. When the menu starts, it prints how many products are at or below their reorder level. Prices are stored as whole cents and shown with two decimals.

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

The image uses Python 3.15.0. CI builds an image and runs the tests inside it. `v1.0.0` is the image `inventory:1.0.0`. `v1.1.0` is the image `inventory:1.1.0`, built with `docker build -t inventory:1.1.0 .`.

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

Version 1.1.0 only adds a low-stock count when the menu starts. The tables stay the same, and this version writes no new kind of data, so the same database file serves both images. A later release that changed the schema would need a down-migration before the old image could open the file.

I seeded a fresh volume with the 1.1.0 image:

```bash
docker volume create inventory-rollback
docker run --rm \
  -e INVENTORY_DB=/data/inventory.db \
  -v inventory-rollback:/data \
  inventory:1.1.0 \
  python seed_db.py
```

```text
suppliers: 4
products: 12
sales: 5
sale_items: 12
stock_movements: 0
```

Then I restocked product 1 by 5 and looked up product 13. The answers were piped in, so each prompt stays on the same line as the next one.

```bash
printf '4\n1\n5\n2\n13\n0\n' | docker run -i --rm \
  -e INVENTORY_DB=/data/inventory.db \
  -v inventory-rollback:/data \
  inventory:1.1.0
```

```text
Low stock: 3 products at or below their reorder level.

Inventory
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
Choice: Product id: Amount: New quantity: 45.

Inventory
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
Choice: Product id: No product with that id.

Inventory
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
Choice:
```

The first line is the banner. The hammer went from 40 on hand to 45. Product 13 is not in the seed.

The same volume on 1.0.0 has no banner. The restock is still there.

```bash
printf '2\n1\n0\n' | docker run -i --rm \
  -e INVENTORY_DB=/data/inventory.db \
  -v inventory-rollback:/data \
  inventory:1.0.0
```

```text

Inventory
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
Choice: Product id: HT-001 Claw Hammer 16oz Hand Tools Northwind Tools 18.99 qty 45 reorder 10

Inventory
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
Choice:
```

Both images report the same row counts for that file:

```text
suppliers 4
products 12
sales 5
sale_items 12
stock_movements 1
```

## Self-review

If I built this again, I would keep the connection setup, the five tables, and the way a sale is one transaction. `connect` turns foreign keys on every time, the schema holds the rules, and `record_sale` writes the sale, the lines, the stock change, and the log together.

I would split `inventory_db.py` once the reports were in. One file was fine for products and search. After restock, adjust, and sales landed, I was scrolling past the reports to find a stock change. Products, search, reports, and stock changes would each be easier to find in their own file, with `connect` still the only way to open the database.

I would also pass a time into the menu the same way the functions already take a time. The failed-sale section above calls `record_sale` with a fixed timestamp. The menu always uses the current time, so I cannot reproduce that section by typing the sale at the prompt. A menu that asked for a date, and used now when the date was left blank, would make that demo something I could run from the menu.

The thing I want a reviewer to check is `quantity_in_stock` against `stock_movements`. Restock, adjust, and record a sale update the quantity and write the log row in the same transaction, so those two should agree for any change made through those functions. The seed is separate from that. It loads today's shelf counts and leaves `stock_movements` empty, so the seeded sales have no matching movement rows. Adding up the log and comparing it with the quantity on the product is the right check for every restock, adjustment, and sale after seeding. I would want a reviewer to confirm the seed is the exception and the three stock functions stay in agreement.
