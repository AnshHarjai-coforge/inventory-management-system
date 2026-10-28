-- Foreign keys are enabled in inventory_db.connect() for every connection.

CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL CHECK (length(trim(name)) > 0)
) STRICT;

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    sku TEXT NOT NULL UNIQUE CHECK (length(trim(sku)) > 0),
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    category TEXT NOT NULL CHECK (length(trim(category)) > 0),
    supplier_id INTEGER NOT NULL
        REFERENCES suppliers(id) ON DELETE RESTRICT,
    unit_price_cents INTEGER NOT NULL CHECK (unit_price_cents >= 0),
    quantity_in_stock INTEGER NOT NULL DEFAULT 0 CHECK (quantity_in_stock >= 0),
    reorder_level INTEGER NOT NULL DEFAULT 0 CHECK (reorder_level >= 0)
) STRICT;

CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY,
    sold_at TEXT NOT NULL CHECK (length(sold_at) >= 10) -- ISO-8601 UTC
) STRICT;

CREATE TABLE IF NOT EXISTS sale_items (
    id INTEGER PRIMARY KEY,
    sale_id INTEGER NOT NULL
        REFERENCES sales(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL
        REFERENCES products(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_cents INTEGER NOT NULL CHECK (unit_price_cents >= 0),
    UNIQUE (sale_id, product_id)
) STRICT;

CREATE TABLE IF NOT EXISTS stock_movements (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL
        REFERENCES products(id) ON DELETE CASCADE,
    change INTEGER NOT NULL CHECK (change <> 0),
    reason TEXT NOT NULL CHECK (reason IN ('restock', 'adjustment', 'sale')),
    occurred_at TEXT NOT NULL
) STRICT;

-- Indexes
-- SKU is already indexed by its UNIQUE constraint.

CREATE INDEX IF NOT EXISTS idx_products_supplier
    ON products(supplier_id);

CREATE INDEX IF NOT EXISTS idx_products_category
    ON products(category);

CREATE INDEX IF NOT EXISTS idx_sale_items_product
    ON sale_items(product_id);

CREATE INDEX IF NOT EXISTS idx_stock_movements_product
    ON stock_movements(product_id, occurred_at);
