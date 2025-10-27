# app.py
# Main Flask application file for the Client Order Portal API.
# UPDATED: Now handles image file uploads for products.
# UPDATED: Replaced unbilled-challans-check route with the correct /monthly-bills/check-status route.
# UPDATED: Fixed SQL error in check_bill_status by using the correct 'billing_period' column name.

from flask import Flask, jsonify, request, send_file, url_for
from flask_cors import CORS
from db import get_db_connection
import mysql.connector
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging
import os
from werkzeug.utils import secure_filename

# Import company details from config
from config import COMPANY_DETAILS

# Import PDF helpers
from pdf_generator import create_challan_pdf, create_monthly_bill_pdf

# Import the route blueprints
from challan_routes import challan_bp
from bill_routes import bill_bp

# --- App Configuration ---
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Initialize the Flask application and logging
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.DEBUG)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Register the blueprints
app.register_blueprint(challan_bp)
app.register_blueprint(bill_bp)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Helper function for data conversion ---
def format_datetime(obj):
    """Helper function to format datetime and Decimal objects for JSON serialization."""
    if obj is None:
        return None
    if isinstance(obj, datetime) or isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

# --- New Route to Serve Uploaded Files ---
@app.route('/uploads/<path:filename>')
def send_upload(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

# --- API Endpoint to check for low stock products ---
@app.route('/products/low-stock', methods=['GET'])
def get_low_stock_products():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT product_id, name, stock_quantity, low_stock_threshold FROM products WHERE stock_quantity <= low_stock_threshold"
        cursor.execute(query)
        low_stock_items = cursor.fetchall()
        return jsonify(low_stock_items)
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# --- NEW DASHBOARD SUMMARY ENDPOINT ---
@app.route('/dashboard-summary', methods=['GET'])
def get_dashboard_summary():
    """
    Provides a high-level summary of key business metrics for the admin dashboard.
    """
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = conn.cursor(dictionary=True)
    try:
        # This query is compatible with the ENUM schema
        query = """
            SELECT
                (SELECT COUNT(*) 
                 FROM orders 
                 WHERE DATE(order_date) = CURDATE()) AS new_orders_today,
                 
                (SELECT COUNT(*) 
                 FROM orders 
                 WHERE associated_challan_id IS NULL 
                   AND status != 'Cancelled') AS pending_challans,
                   
                (SELECT COUNT(*) 
                 FROM challans 
                 WHERE monthly_bill_id IS NULL) AS unbilled_challans,
                 
                (SELECT COUNT(*) 
                 FROM monthly_bills 
                 WHERE due_date < CURDATE() 
                   AND status != 'Paid') AS overdue_bills
        """
        
        cursor.execute(query)
        summary_data = cursor.fetchone()
        
        for key in summary_data:
            summary_data[key] = int(summary_data[key])
            
        return jsonify(summary_data)
        
    except mysql.connector.Error as err:
        app.logger.error(f"Dashboard summary query failed: {err}")
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# --- Product Management Endpoints ---
@app.route('/products', methods=['GET'])
def get_all_products():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        # Includes image_url as specified in schema
        cursor.execute("SELECT product_id, name, description, price, stock_quantity, image_url FROM products ORDER BY name")
        products = cursor.fetchall()
        for product in products:
            product['price'] = format_datetime(product['price'])
            # Create absolute URL for images
            if product['image_url']:
                product['image_url'] = url_for('send_upload', filename=product['image_url'], _external=True)
        return jsonify(products)
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/products', methods=['POST'])
def add_new_product():
    # This endpoint now handles multipart/form-data
    if 'name' not in request.form or 'price' not in request.form or 'stock_quantity' not in request.form:
        return jsonify({"error": "Missing required fields: name, price, stock_quantity"}), 400

    data = request.form
    image_url_to_save = None

    # Check for image file
    if 'image_file' in request.files:
        file = request.files['image_file']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Ensure unique filename to avoid overwrites
            base, ext = os.path.splitext(filename)
            unique_filename = f"{base}_{int(datetime.now().timestamp())}{ext}"
            
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(save_path)
            # We save the *relative path* to the DB, not the full URL
            image_url_to_save = unique_filename 

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor()
    
    query = "INSERT INTO products (name, description, price, stock_quantity, low_stock_threshold, image_url) VALUES (%s, %s, %s, %s, %s, %s)"
    values = (
        data.get('name'), data.get('description'), data.get('price'),
        data.get('stock_quantity'), data.get('low_stock_threshold', 10),
        image_url_to_save # Use the new filename
    )
    try:
        cursor.execute(query, values)
        conn.commit()
        new_product_id = cursor.lastrowid
        return jsonify({"message": "Product added successfully", "product_id": new_product_id}), 201
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product_by_id(product_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
        product = cursor.fetchone()
        if product:
            product['price'] = format_datetime(product['price'])
            # Create absolute URL for image
            if product['image_url']:
                product['image_url'] = url_for('send_upload', filename=product['image_url'], _external=True)
            return jsonify(product)
        else:
            return jsonify({"error": "Product not found"}), 404
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    # This endpoint now handles multipart/form-data
    if 'name' not in request.form:
        return jsonify({"error": "No input data provided"}), 400

    data = request.form
    image_url_to_save = data.get('image_url') # Default to existing URL

    # Check for a new image file
    if 'image_file' in request.files:
        file = request.files['image_file']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            base, ext = os.path.splitext(filename)
            unique_filename = f"{base}_{int(datetime.now().timestamp())}{ext}"
            
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(save_path)
            # We save the *relative path* to the DB
            image_url_to_save = unique_filename
            # TODO: Add logic here to delete the *old* image file if it exists

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = conn.cursor()
    update_fields = []
    values = []
    
    # Get fields from form data
    for key in ['name', 'description', 'price', 'stock_quantity', 'low_stock_threshold']:
        if key in data:
            update_fields.append(f"{key} = %s")
            values.append(data[key])
            
    # Add the image_url
    update_fields.append("image_url = %s")
    values.append(image_url_to_save)
    
    if not update_fields:
        return jsonify({"error": "No valid fields to update"}), 400
    
    values.append(product_id)
    query = f"UPDATE products SET {', '.join(update_fields)} WHERE product_id = %s"
    
    try:
        cursor.execute(query, tuple(values))
        if cursor.rowcount == 0:
            return jsonify({"error": "Product not found"}), 404
        conn.commit()
        return jsonify({"message": "Product updated successfully"}), 200
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True) # Use dictionary cursor to get image_url
    try:
        # First, check for associated orders
        cursor.execute("SELECT COUNT(*) as count FROM order_items WHERE product_id = %s", (product_id,))
        if cursor.fetchone()['count'] > 0:
            return jsonify({"error": "Cannot delete product because it is part of an existing order."}), 409
        
        # Get the image_url before deleting
        cursor.execute("SELECT image_url FROM products WHERE product_id = %s", (product_id,))
        product = cursor.fetchone()
        
        # Delete the product from DB
        cursor.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
        if cursor.rowcount == 0:
            return jsonify({"error": "Product not found"}), 404
        
        conn.commit()
        
        # If delete was successful, try to delete the image file
        if product and product['image_url']:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], product['image_url']))
            except OSError as e:
                app.logger.error(f"Error deleting image file {product['image_url']}: {e}")

        return jsonify({"message": "Product deleted successfully"}), 200
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# --- Order Management Endpoints ---
@app.route('/orders', methods=['POST'])
def create_new_order():
    data = request.get_json()
    if not data or 'client_id' not in data or 'items' not in data:
        return jsonify({"error": "Missing client_id or items list"}), 400
    client_id = data['client_id']
    items = data['items']
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        order_items_to_insert = []
        for item in items:
            cursor.execute("SELECT * FROM products WHERE product_id = %s FOR UPDATE", (item['product_id'],))
            product = cursor.fetchone()
            if not product:
                raise Exception(f"Product with ID {item['product_id']} not found.")
            if product['stock_quantity'] < item['quantity']:
                raise Exception(f"Not enough stock for {product['name']}. Requested: {item['quantity']}, Available: {product['stock_quantity']}")
            cursor.execute("SELECT custom_price FROM client_pricing WHERE client_id = %s AND product_id = %s", (client_id, item['product_id']))
            custom_price_row = cursor.fetchone()
            final_price = custom_price_row['custom_price'] if custom_price_row else product['price']
            order_items_to_insert.append({'product_id': item['product_id'], 'quantity': item['quantity'], 'price_per_unit': final_price})
        
        # This INSERT is correct. It omits 'status' and lets the DB
        # use the default value 'Pending' from the ENUM.
        order_query = "INSERT INTO orders (client_id) VALUES (%s)"
        cursor.execute(order_query, (client_id,))
        new_order_id = cursor.lastrowid
        
        for item_data in order_items_to_insert:
            item_query = "INSERT INTO order_items (order_id, product_id, quantity, price_per_unit) VALUES (%s, %s, %s, %s)"
            cursor.execute(item_query, (new_order_id, item_data['product_id'], item_data['quantity'], item_data['price_per_unit']))
            stock_update_query = "UPDATE products SET stock_quantity = stock_quantity - %s WHERE product_id = %s"
            cursor.execute(stock_update_query, (item_data['quantity'], item_data['product_id']))
        conn.commit()
        return jsonify({"message": "Order created successfully", "order_id": new_order_id}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/orders', methods=['GET'])
def get_all_orders():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 25)) 
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        offset = (page - 1) * per_page
        
        where_clauses = ["1=1"]
        query_params = []
        
        if start_date:
            where_clauses.append("DATE(o.order_date) >= %s") 
            query_params.append(start_date)
            
        if end_date:
            where_clauses.append("DATE(o.order_date) <= %s") 
            query_params.append(end_date)
            
        where_sql = " AND ".join(where_clauses)

        count_query = f"""
            SELECT COUNT(*) as total_count
            FROM orders o
            WHERE {where_sql}
        """
        cursor.execute(count_query, tuple(query_params))
        total_count = cursor.fetchone()['total_count']
        total_pages = (total_count + per_page - 1) // per_page

        data_query = f"""
            SELECT o.order_id, o.client_id, c.company_name as client_name,
                   (SELECT SUM(oi.quantity * oi.price_per_unit) FROM order_items oi WHERE oi.order_id = o.order_id) AS total_amount,
                   o.status, o.order_date, o.associated_challan_id
            FROM orders o JOIN clients c ON o.client_id = c.client_id
            WHERE {where_sql}
            ORDER BY o.order_date DESC
            LIMIT %s OFFSET %s
        """
        
        query_params_paginated = query_params + [per_page, offset]
        cursor.execute(data_query, tuple(query_params_paginated))
        
        orders = cursor.fetchall()
        for order in orders:
            order['order_date'] = format_datetime(order['order_date'])
            order['total_amount'] = format_datetime(order['total_amount']) if order['total_amount'] else 0.0
            
        return jsonify({
            "data": orders,
            "current_page": page,
            "total_pages": total_pages,
            "total_count": total_count
        })
        
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order_by_id(order_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT o.order_id, o.client_id, c.company_name as client_name, o.status, o.order_date,
                   (SELECT SUM(oi.quantity * oi.price_per_unit) FROM order_items oi WHERE oi.order_id = o.order_id) AS total_amount
            FROM orders o JOIN clients c ON o.client_id = c.client_id
            WHERE o.order_id = %s
        """, (order_id,))
        order = cursor.fetchone()
        if not order:
            return jsonify({"error": "Order not found"}), 404
        cursor.execute("""
            SELECT oi.product_id, p.name as product_name, oi.quantity, oi.price_per_unit
            FROM order_items oi JOIN products p ON oi.product_id = p.product_id
            WHERE oi.order_id = %s
        """, (order_id,))
        items = cursor.fetchall()
        order['order_date'] = format_datetime(order['order_date'])
        order['total_amount'] = format_datetime(order['total_amount']) if order['total_amount'] else 0.0
        for item in items:
            item['price_per_unit'] = format_datetime(item['price_per_unit'])
        order['items'] = items
        return jsonify(order)
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        
        cursor.execute("SELECT associated_challan_id FROM orders WHERE order_id = %s FOR UPDATE", (order_id,))
        order = cursor.fetchone()
        
        if not order:
            conn.rollback()
            return jsonify({"error": "Order not found"}), 404
            
        if order.get('associated_challan_id'):
            conn.rollback()
            return jsonify({"error": "Cannot delete order. It is linked to a challan. Please delete the challan first."}), 409

        cursor.execute("SELECT product_id, quantity FROM order_items WHERE order_id = %s", (order_id,))
        items_to_restock = cursor.fetchall()

        for item in items_to_restock:
            cursor.execute(
                "UPDATE products SET stock_quantity = stock_quantity + %s WHERE product_id = %s",
                (item['quantity'], item['product_id'])
            )

        cursor.execute("DELETE FROM order_items WHERE order_id = %s", (order_id,))
        cursor.execute("DELETE FROM orders WHERE order_id = %s", (order_id,))
        
        conn.commit()
        return jsonify({"message": "Order deleted and stock has been restocked."}), 200
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# --- Client Management (CRM) Endpoints ---
@app.route('/clients', methods=['GET'])
def get_all_clients():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT client_id, username, company_name FROM clients ORDER BY company_name")
        clients = cursor.fetchall()
        return jsonify(clients)
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/clients', methods=['POST'])
def add_new_client():
    client_data = request.get_json()
    if not client_data:
        return jsonify({"error": "No input data provided"}), 400
    if 'username' not in client_data or 'company_name' not in client_data:
        return jsonify({"error": "Missing required fields: username and company_name"}), 400
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor()
    query = "INSERT INTO clients (username, company_name) VALUES (%s, %s)"
    values = (client_data['username'], client_data['company_name'])
    try:
        cursor.execute(query, values)
        conn.commit()
        new_client_id = cursor.lastrowid
        return jsonify({"message": "Client registered successfully", "client_id": new_client_id}), 201
    except mysql.connector.Error as err:
        if err.errno == 1062: # Duplicate entry
            return jsonify({"error": "A client with this username already exists."}), 409
        return jsonify({"error": f"Database error: {err}"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/clients/<int:client_id>', methods=['GET'])
def get_client_by_id(client_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT client_id, username, company_name, created_at FROM clients WHERE client_id = %s", (client_id,))
        client = cursor.fetchone()
        if client:
            if 'created_at' in client and client['created_at']:
                 client['created_at'] = client['created_at'].isoformat()
            return jsonify(client)
        else:
            return jsonify({"error": "Client not found"}), 404
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/clients/<int:client_id>', methods=['PUT'])
def update_client(client_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor()
    update_fields = []
    values = []
    allowed_fields = ['company_name']
    for key, value in data.items():
        if key in allowed_fields:
            update_fields.append(f"{key} = %s")
            values.append(value)
    if not update_fields:
        return jsonify({"message": "No fields to update"}), 200
    values.append(client_id)
    query = f"UPDATE clients SET {', '.join(update_fields)} WHERE client_id = %s"
    try:
        cursor.execute(query, tuple(values))
        if cursor.rowcount == 0:
            return jsonify({"error": "Client not found"}), 404
        conn.commit()
        return jsonify({"message": "Client updated successfully"}), 200
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/clients/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM orders WHERE client_id = %s", (client_id,))
        if cursor.fetchone()[0] > 0:
            return jsonify({"error": "Cannot delete client with existing orders. Please reassign or delete orders first."}), 409
        cursor.execute("DELETE FROM clients WHERE client_id = %s", (client_id,))
        if cursor.rowcount == 0:
            return jsonify({"error": "Client not found"}), 404
        conn.commit()
        return jsonify({"message": "Client deleted successfully"}), 200
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/clients/<int:client_id>/orders', methods=['GET'])
def get_orders_for_client(client_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT order_id, 
               (SELECT SUM(oi.quantity * oi.price_per_unit) FROM order_items oi WHERE oi.order_id = o.order_id) AS total_amount,
               status, order_date
        FROM orders o WHERE client_id = %s
        ORDER BY order_date DESC
    """
    try:
        cursor.execute(query, (client_id,))
        orders = cursor.fetchall()
        for order in orders:
            order['order_date'] = format_datetime(order['order_date'])
            order['total_amount'] = format_datetime(order['total_amount']) if order['total_amount'] else 0.0
        return jsonify(orders)
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()


# ===================================================================
# --- UPDATED ENDPOINT FOR BILL GENERATION PRE-CHECK ---
# --- This route now has robust error handling ---
# ===================================================================
@app.route('/monthly-bills/check-status', methods=['GET'])
def check_bill_status():
    """
    Checks if a bill can be generated for a given client and month.
    This endpoint is called by the "Generate Bill" UI to provide real-time feedback.
    """
    # Initialize connection variables
    conn = None
    cursor = None
    
    try:
        client_id = request.args.get('client_id', type=int)
        billing_period_str = request.args.get('billing_month') # Matches frontend param

        if not client_id or not billing_period_str:
            return jsonify({"error": "client_id and billing_month are required"}), 400

        # Validate format and extract year/month for challan check
        try:
            year, month = map(int, billing_period_str.split('-'))
        except ValueError:
            return jsonify({"error": "Invalid 'billing_month' format. Use YYYY-MM."}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor(dictionary=True)

        # --- 1. Check if a bill ALREADY exists ---
        # ---
        # --- THE FIX IS HERE ---
        # Was: ... WHERE client_id = %s AND billing_month = %s  <-- Using wrong column name
        # Now: ... WHERE client_id = %s AND billing_period = %s <-- Using correct column name
        # ---
        query_bill = """
            SELECT status FROM monthly_bills
            WHERE client_id = %s AND billing_period = %s 
        """
        cursor.execute(query_bill, (client_id, billing_period_str)) # Use the string YYYY-MM
        existing_bill = cursor.fetchone()

        if existing_bill:
            # A bill already exists, generation is not allowed.
            return jsonify({
                "message": f"Bill already exists (Status: {existing_bill['status']})",
                "status": existing_bill['status'], # e.g., "Pending" or "Paid"
                "can_generate": False
            })

        # --- 2. If no bill, check for PENDING challans ---
        query_challan = """
            SELECT COUNT(*) as unbilled_count
            FROM challans
            WHERE client_id = %s
              AND monthly_bill_id IS NULL
              AND YEAR(challan_date) = %s
              AND MONTH(challan_date) = %s
        """
        cursor.execute(query_challan, (client_id, year, month)) # Use year and month for challan check
        result = cursor.fetchone()
        unbilled_count = result.get('unbilled_count', 0)

        if unbilled_count > 0:
            # Challans are pending, generation is allowed.
            return jsonify({
                "message": f"{unbilled_count} pending challan(s) found.",
                "status": "Ready",
                "can_generate": True
            })
        else:
            # No bill and no pending challans.
            return jsonify({
                "message": "No pending challans found for this period.",
                "status": "Nothing to bill",
                "can_generate": False
            })

    except mysql.connector.Error as err:
        # Handle specific database errors
        app.logger.error(f"Database error in check_bill_status: {err}")
        return jsonify({"error": f"Database error: {err}"}), 500
    except Exception as e:
        # Handle all other unexpected errors (e.g., AttributeError if conn is None)
        app.logger.error(f"Unexpected error in check_bill_status: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500
    finally:
        # Safely close cursor and connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# --- Client-Specific Pricing Endpoints ---
@app.route('/clients/<int:client_id>/pricing', methods=['POST'])
def set_client_specific_price(client_id):
    data = request.get_json()
    if not data or 'product_id' not in data or 'custom_price' not in data:
        return jsonify({"error": "Missing product_id or custom_price"}), 400
    product_id = data['product_id']
    custom_price = data['custom_price']
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor()
    query = "INSERT INTO client_pricing (client_id, product_id, custom_price) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE custom_price = VALUES(custom_price)"
    try:
        cursor.execute(query, (client_id, product_id, custom_price))
        conn.commit()
        return jsonify({"message": "Custom price set successfully"}), 200
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/clients/<int:client_id>/pricing', methods=['GET'])
def get_client_specific_prices(client_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT cp.product_id, p.name as product_name, cp.custom_price
        FROM client_pricing cp JOIN products p ON cp.product_id = p.product_id
        WHERE cp.client_id = %s
    """
    try:
        cursor.execute(query, (client_id,))
        prices = cursor.fetchall()
        for price in prices:
            price['custom_price'] = format_datetime(price['custom_price'])
        return jsonify(prices)
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()


# --- Main execution block ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)