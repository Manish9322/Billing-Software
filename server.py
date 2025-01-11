from flask import Flask, request, render_template, redirect, url_for
import mysql.connector

app = Flask(__name__)


def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Manish@123",
        database="inventory",
    )
    return connection


@app.route("/pay", methods=["POST"])
def pay():
    total_price = float(request.form.get("totalPrice", 0.00))
    total_quantity = int(request.form.get("totalQuantity", 0))

    receipt_items = request.form.to_dict(flat=False)
    receipt_data = {
        key.replace("quantity-", ""): int(value[0])
        for key, value in receipt_items.items()
        if key.startswith("quantity-")
    }

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Update product quantities and handle removal of zero-quantity products
        for product_name, purchased_quantity in receipt_data.items():
            # Check if the product exists and has sufficient quantity
            cursor.execute(
                "SELECT quantity FROM Products WHERE name = %s", (product_name,)
            )
            product = cursor.fetchone()

            if product and product[0] >= purchased_quantity:
                # Subtract the purchased quantity
                new_quantity = product[0] - purchased_quantity
                if new_quantity > 0:
                    # Update the quantity if it's greater than zero
                    update_query = "UPDATE Products SET quantity = %s WHERE name = %s"
                    cursor.execute(update_query, (new_quantity, product_name))
                else:
                    # Delete the product if quantity reaches zero
                    delete_query = "DELETE FROM Products WHERE name = %s"
                    cursor.execute(delete_query, (product_name,))

        # Insert revenue and sales data
        revenue_query = """
        INSERT INTO revenue_sales (total_revenue, total_sales)
        VALUES (%s, %s)
        """
        cursor.execute(revenue_query, (total_price, total_quantity))

        connection.commit()

    except mysql.connector.Error as e:
        print("Database Error:", e)
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("manage_inventory"))


@app.route("/", methods=["GET", "POST"])
def manage_inventory():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    product_search_results = None
    customer_search_results = None

    if request.method == "POST":
        # Product Search
        if "product-searchbar" in request.form and "product-search-column" in request.form:
            product_column = request.form.get("product-search-column")
            product_value = request.form.get("product-searchbar")

            try:
                # Handle special case for searching by `type`
                if product_column == "type":
                    query = """
                    SELECT 
                        p.id, 
                        p.name, 
                        pt.type_name AS type, 
                        p.price, 
                        p.quantity, 
                        p.manufacturer, 
                        p.stock
                    FROM Products p
                    JOIN ProductTypes pt ON p.type_id = pt.id
                    WHERE pt.type_name LIKE %s
                    """
                else:
                    query = f"""
                    SELECT 
                        p.id, 
                        p.name, 
                        pt.type_name AS type, 
                        p.price, 
                        p.quantity, 
                        p.manufacturer, 
                        p.stock
                    FROM Products p
                    JOIN ProductTypes pt ON p.type_id = pt.id
                    WHERE p.{product_column} LIKE %s
                    """
                cursor.execute(query, (f"%{product_value}%",))
                product_search_results = cursor.fetchall()
            except mysql.connector.Error as e:
                print("Product Search Error:", e)

        # Customer Search
        elif "customer-searchbar" in request.form and "customer-search-column" in request.form:
            customer_column = request.form.get("customer-search-column")
            customer_value = request.form.get("customer-searchbar")

            try:
                # Construct and execute the customer search query
                query = f"SELECT * FROM customers WHERE {customer_column} LIKE %s"
                cursor.execute(query, (f"%{customer_value}%",))
                customer_search_results = cursor.fetchall()
            except mysql.connector.Error as e:
                print("Customer Search Error:", e)

    # Default Queries for Rendering
    product_query = """
    SELECT 
        p.id, 
        p.name, 
        pt.type_name AS type, 
        p.price, 
        p.quantity, 
        p.manufacturer, 
        p.stock
    FROM Products p
    JOIN ProductTypes pt ON p.type_id = pt.id
    """
    cursor.execute(product_query)
    products = cursor.fetchall()

    cursor.execute("SELECT * FROM ProductTypes")
    product_types = cursor.fetchall()

    customer_query = "SELECT * FROM customers"
    cursor.execute(customer_query)
    customers = cursor.fetchall()

    cursor.execute(
        "SELECT SUM(total_revenue) AS total_revenue, SUM(total_sales) AS total_sales FROM revenue_sales"
    )
    revenue_sales_data = cursor.fetchone()
    total_revenue = revenue_sales_data["total_revenue"] or 0.00
    total_sales = revenue_sales_data["total_sales"] or 0

    cursor.close()
    connection.close()

    return render_template(
        "index.html",
        products=product_search_results if product_search_results else products,
        product_types=product_types,
        customers=customer_search_results if customer_search_results else customers,
        total_revenue=total_revenue,
        total_sales=total_sales,
    )


if __name__ == "__main__":
    app.run(port=5000, debug=True)
