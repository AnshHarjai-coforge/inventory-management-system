# Plan: inventory management system

A small hardware store tracks stock in a spreadsheet. Prices drift, counts are wrong, and a sale does not leave a clear record of what changed. This program stores the data in SQLite and offers a terminal menu.

## Decisions

1. Prices are stored as whole cents, so the database never holds a decimal. A price of $18.99 is stored as 1899. The menu prints 1899 as 18.99. Times are stored as text, such as `2026-01-05T10:15:00Z`. The caller can pass a time. If they do not, we use the current time.

2. The database enforces the rules: unique SKUs, required fields, no negative prices or quantities, a valid movement reason, and foreign keys. Python raises one error with a short message. The menu prints that message. A prompt that expects a number asks again when it receives text.

3. Database code lives in one module. The menu collects input and calls that module. A change with several steps is saved all at once, or not at all. A helper used inside that change does not save on its own. Connections are closed with `contextlib.closing`. Values go into queries as placeholders.

4. `schema.sql` creates the five tables and only what is missing. Running it again leaves existing data in place and does not fail. Tables are `STRICT`, which needs SQLite 3.37 or newer. If the installed SQLite is older, leave `STRICT` out and say so in the README. `connect` turns foreign key checks on for every connection and makes rows readable by column name.

## The five tables

**suppliers.** A supplier is its own row so many products can point at the same one. Two suppliers may share a name.

- Primary key: `id`.
- Foreign key: none.
- Name is required and may be duplicated.

**products.** One row for each thing the store sells: SKU, name, category, supplier, unit price, quantity in stock, and reorder level.

- Primary key: `id`.
- Foreign key: `supplier_id` references `suppliers.id`.
- SKU, name, and category are required. SKU is unique.
- Unit price, quantity in stock, and reorder level are zero or greater. Quantity and reorder level start at zero.

**sales.** The header of one customer sale, so one sale can contain many products. It records when the sale happened.

- Primary key: `id`.
- Foreign key: none.
- The time is required.

**sale_items.** One line of a sale. It records the product, the quantity, and the unit price charged at the time of the sale. Later price edits leave old revenue unchanged.

- Primary key: `id`.
- Foreign keys: `sale_id` references `sales.id`, and `product_id` references `products.id`.
- Quantity is at least one. The recorded price is zero or greater.
- The same product cannot appear twice on one sale.

**stock_movements.** The log of every stock change. Each row records the product, a signed change, the reason, and when it happened.

- Primary key: `id`.
- Foreign key: `product_id` references `products.id`.
- The reason is restock, adjustment, or sale.
- The time is required.
- A positive change adds stock. A negative change removes it.

## How the tables relate

A supplier has many products. A product has many sale lines and many stock movements. A sale has many lines.

- A product’s `supplier_id` points at `suppliers.id`. A supplier that still has products cannot be deleted.
- A product that has been sold cannot be deleted. The link from a sale line to the product enforces that, and the menu turns the failure into a message.
- Deleting a sale deletes its lines.
- Deleting a product that was never sold also deletes its movement log.
- One sale and one product together are unique, so the same product twice on one sale is refused and the sale is undone.

One index, on `products.supplier_id`, supports the stock-value-by-supplier join. SKU is already unique.

## Public functions

Every function takes the open connection first. `connect` is the one function that opens a connection: an optional path, otherwise `INVENTORY_DB`, otherwise `inventory.db` beside the code. It returns the open connection.

**init_schema** — The connection. Returns nothing. Runs `schema.sql`.

**add_product** — SKU, name, category, supplier id, price in cents, and optional starting quantity and reorder level. Returns the new product id. A duplicate SKU, an unknown supplier, or a negative price or quantity is an error.

**get_product** — A product id. Returns that product together with the supplier’s name, or nothing if the id is unknown.

**update_price** — A product id and a new price in cents. Returns true if the price changed, and false if there is no such product. A negative price is an error.

**delete_product** — A product id. Returns true if the product was deleted, and false if it does not exist. A product with sales is an error.

**search_products** — Optional text, plus optional filters for category, maximum price in cents, in stock only, and low stock only. Returns matching products sorted by name. Text is matched, ignoring case, against the product name, the SKU, and the supplier name. The filters combine. The text is bound as a placeholder.

**stock_value_by_supplier** — Takes only the connection. Returns each supplier’s name and the value of its stock, price times quantity, highest first.

**low_stock_report** — Takes only the connection. Returns each product at or below its reorder level, including how many units short it is.

**sales_by_product** — Takes only the connection. Returns each product that has sold, with units sold and revenue, highest revenue first. Revenue uses the price stored on the sale line.

**never_sold** — Takes only the connection. Returns products that appear in no sale.

**restock** — Adds stock from a delivery and logs it. Inputs are a product id, a positive amount, and an optional time. Returns the new quantity on hand.

**adjust_stock** — Changes stock up or down for damage or a recount, and logs it. Inputs are a product id, the change, and an optional time. Returns the new quantity on hand. A change that would make stock negative is refused.

**record_sale** — Saves one customer sale, or saves nothing. Inputs are pairs of product id and quantity, and an optional time. Returns the new sale id.

**backup_database** — A destination path. Returns nothing. Copies the live database with SQLite’s own backup.

The menu offers search, lookup, add, restock, record a sale, each of the four reports, and backup. Price changes, deletes, and adjustments stay as functions the tests call.

Version 1.1.0 shows a startup banner with the number of rows from the low-stock report. That needs no new function and no schema change.

## Restock

Restock adds a delivery to one product and writes a log row for it.

1. If the amount is zero or less, stop. Nothing is written.
2. Start a transaction.
3. Add the amount to that product. If the product does not exist, undo and stop.
4. Write a log row: the same positive amount, reason restock, and the given time or the current time.
5. Save.

If step 3 or 4 fails, undo. The new quantity and the log row are saved together, or not at all.

## Adjust

Adjust changes one product’s count up or down and writes a log row. A damaged item is a negative change. A recount that found extra items is a positive change.

1. Start a transaction.
2. Apply the change. If the product does not exist, or the count would go below zero, stop. Nothing is written.
3. Write a log row with reason adjustment.
4. Save.

If step 2 or 3 fails, undo. The count and the log stay as they were.

## Record a sale

Record a sale saves one customer purchase: the sale, a line for each product at today’s price, a lower stock count, and a log row for each line.

1. Start one transaction.
2. Write the sale, with the given time or the current time.
3. For each product, find it. If it does not exist, undo the sale.
4. Write the line at the product’s current price. If that product is already on this sale, undo the sale.
5. Lower the stock by the quantity sold. If there is not enough, undo the sale.
6. Write a log row with reason sale. If that write fails, undo the sale.
7. Save, and return the new sale id.

Undoing the sale removes the sale, its lines, the stock changes, and the log rows from this attempt.

## Sample data

`seed_db.py` creates the tables, then loads the rows with placeholders and `executemany`. It prints the row count of each table. The data is 4 suppliers, 12 products in at least 3 categories, and 5 sales with 12 sale items. At least 2 products were never sold, and at least 2 are at or below their reorder level, including one where stock equals the level. Every supplier has at least one product. `stock_movements` starts empty. The quantities on the products are today’s shelf counts, not a replay of the seeded sales. One seeded line uses an older price than the product’s current price, so the sales report is visibly using the stored price.

## Release

Six pull requests, each from its own branch, each merged only after CI passes. Commit messages start with a verb. The branch is deleted after the merge.

1. `feature/database-and-seed` — schema, seed, and `connect`. CI runs the tests.
2. `feature/products-and-search` — product functions, search, and their tests.
3. `feature/reports` — the four reports and their tests.
4. `feature/stock-and-sales` — restock, adjust, record a sale, and their tests.
5. `feature/menu-and-container` — menu, backup, Dockerfile, `.dockerignore`, README, and changelog. The CI workflow gains a `docker-build` job that builds the image and runs the tests inside it. Tag `v1.0.0` and the image `1.0.0`.
6. `feature/low-stock-banner` — the startup banner only. Tag `v1.1.0` and the image `1.1.0`.

The database file lives on a volume, so a new container still sees the same data. The image reads `INVENTORY_DB` and falls back to a file beside the code. The Dockerfile pins the Python version and installs dependencies before copying the source.

Version 1.1.0 changes no schema and writes no new data. Rolling back means running the `1.0.0` image against the same volume. The banner goes away and the rows stay. `CHANGELOG.md` has an entry for each version.
