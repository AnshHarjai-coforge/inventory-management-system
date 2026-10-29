# inventory-management-system

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