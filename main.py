import sqlite3
from contextlib import closing

import inventory_db as db


def dollars(cents):
    """Show a cent amount with two decimals."""
    return f"{cents / 100:.2f}"


def ask_int(prompt):
    """Ask until the user types a whole number."""
    while True:
        raw = input(prompt).strip()
        try:
            return int(raw)
        except ValueError:
            print("Enter a whole number.")


def ask_optional_int(prompt):
    """Ask for a whole number, or blank for none."""
    while True:
        raw = input(prompt).strip()
        if raw == "":
            return None
        try:
            return int(raw)
        except ValueError:
            print("Enter a whole number.")


def ask_yes_no(prompt):
    """Ask until the user types y or n."""
    while True:
        answer = input(prompt).strip().lower()
        if answer == "y":
            return True
        if answer == "n":
            return False
        print("Enter y or n.")


def print_product(row):
    """Print one product on one line."""
    print(
        row["sku"],
        row["name"],
        row["category"],
        row["supplier_name"],
        dollars(row["unit_price_cents"]),
        "qty",
        row["quantity_in_stock"],
        "reorder",
        row["reorder_level"],
    )


def print_menu():
    """Print the menu options."""
    print()
    print("Inventory")
    print("1. Search products")
    print("2. Look up a product")
    print("3. Add a product")
    print("4. Restock")
    print("5. Record a sale")
    print("6. Stock value by supplier")
    print("7. Low stock")
    print("8. Sales by product")
    print("9. Products never sold")
    print("10. Back up the database")
    print("0. Quit")


def search(conn):
    """Find products by text and optional filters."""
    text = input("Text (blank for any): ").strip()
    category = input("Category (blank for any): ").strip()
    if category == "":
        category = None
    max_price_cents = ask_optional_int("Max price in cents (blank for any): ")
    in_stock_only = ask_yes_no("In stock only? (y/n): ")
    low_stock_only = ask_yes_no("Low stock only? (y/n): ")
    rows = db.search_products(
        conn, text, category, max_price_cents, in_stock_only, low_stock_only,
    )
    if not rows:
        print("No products found.")
        return
    for row in rows:
        print_product(row)


def lookup(conn):
    """Show one product and its supplier."""
    product_id = ask_int("Product id: ")
    row = db.get_product(conn, product_id)
    if row is None:
        print("No product with that id.")
        return
    print_product(row)


def add(conn):
    """Ask for a new product and save it."""
    sku = input("SKU: ").strip()
    name = input("Name: ").strip()
    category = input("Category: ").strip()
    supplier_id = ask_int("Supplier id: ")
    price = ask_int("Price in cents: ")
    quantity = ask_optional_int("Quantity (blank for 0): ")
    reorder_level = ask_optional_int("Reorder level (blank for 0): ")
    if quantity is None:
        quantity = 0
    if reorder_level is None:
        reorder_level = 0
    new_id = db.add_product(
        conn, sku, name, category, supplier_id, price, quantity, reorder_level,
    )
    print(f"Added product {new_id}.")


def restock_one(conn):
    """Add stock to one product."""
    product_id = ask_int("Product id: ")
    amount = ask_int("Amount: ")
    quantity = db.restock(conn, product_id, amount)
    print(f"New quantity: {quantity}.")


def record_a_sale(conn):
    """Record a sale from product and quantity pairs."""
    items = []
    while True:
        raw = input("Product id (blank to finish): ").strip()
        if raw == "":
            break
        try:
            product_id = int(raw)
        except ValueError:
            print("Enter a whole number.")
            continue
        quantity = ask_int("Quantity: ")
        items.append((product_id, quantity))
    if not items:
        print("A sale needs at least one line.")
        return
    sale_id = db.record_sale(conn, items)
    print(f"Sale {sale_id} saved.")


def show_stock_value(conn):
    """Print stock value by supplier."""
    print("Stock value by supplier")
    rows = db.stock_value_by_supplier_report(conn)
    if not rows:
        print("None.")
        return
    for row in rows:
        print(f"{row['supplier_name']}: {dollars(row['total_stock_value_cents'])}")


def show_low_stock(conn):
    """Print products at or below their reorder level."""
    print("Low stock")
    rows = db.low_stock_report(conn)
    if not rows:
        print("None.")
        return
    for row in rows:
        print(
            f"{row['sku']} {row['name']}: {row['quantity_in_stock']} on hand, "
            f"reorder {row['reorder_level']}, short {row['units_short']}"
        )


def show_sales_by_product(conn):
    """Print units sold and revenue by product."""
    print("Sales by product")
    rows = db.sales_by_product_report(conn)
    if not rows:
        print("None.")
        return
    for row in rows:
        print(
            f"{row['sku']} {row['name']}: {row['units_sold']} sold, "
            f"{dollars(row['revenue_cents'])}"
        )


def show_never_sold(conn):
    """Print products that appear in no sale."""
    print("Products never sold")
    rows = db.never_sold_report(conn)
    if not rows:
        print("None.")
        return
    for row in rows:
        print(f"{row['sku']} {row['name']} ({row['category']})")


def back_up(conn):
    """Copy the database to a path the user chooses."""
    destination = ""
    while destination == "":
        destination = input("Backup file: ").strip()
    try:
        db.backup_database(conn, destination)
    except sqlite3.DatabaseError:
        print("Could not write the backup.")
        return
    except ValueError as err:
        if str(err) == "That file is the database already in use.":
            print(err)
        else:
            print("Could not write the backup.")
        return
    print(f"Backup saved to {destination}.")


def main():
    """Run the inventory menu until the user quits."""
    with closing(db.connect()) as conn:
        db.init_schema(conn)
        low = len(db.low_stock_report(conn))
        print(f"Low stock: {low} products at or below their reorder level.")
        while True:
            print_menu()
            try:
                choice = input("Choice: ").strip()
                if choice == "0":
                    break
                elif choice == "1":
                    search(conn)
                elif choice == "2":
                    lookup(conn)
                elif choice == "3":
                    add(conn)
                elif choice == "4":
                    restock_one(conn)
                elif choice == "5":
                    record_a_sale(conn)
                elif choice == "6":
                    show_stock_value(conn)
                elif choice == "7":
                    show_low_stock(conn)
                elif choice == "8":
                    show_sales_by_product(conn)
                elif choice == "9":
                    show_never_sold(conn)
                elif choice == "10":
                    back_up(conn)
                else:
                    print("Choose a number from the menu.")
            except EOFError:
                print()
                break
            except sqlite3.IntegrityError as err:
                print(f"That was not saved. {err}")
            except ValueError as err:
                print(err)


if __name__ == "__main__":
    main()
