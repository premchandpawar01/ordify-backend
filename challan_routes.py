# challan_routes.py
# Contains all API endpoints related to Challans.
# This file is compatible with the database_schema.sql provided.
# UPDATED: Correctly updates order status to 'Processing' upon challan creation.

from flask import Blueprint, jsonify, request, send_file
from db import get_db_connection
import mysql.connector
from datetime import datetime, date
from decimal import Decimal
import logging

# Import helpers from pdf_generator and config
from pdf_generator import create_challan_pdf
from config import COMPANY_DETAILS

challan_bp = Blueprint('challan_bp', __name__)

# --- Helper function for data conversion ---
# (Copied from app.py for standalone use)
def format_datetime(obj):
    """Helper function to format datetime and Decimal objects for JSON serialization."""
    if obj is None:
        return None
    if isinstance(obj, datetime) or isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

# --- Challan Management Endpoints ---

@challan_bp.route('/challans', methods=['POST'])
def create_challan_from_order():
    data = request.get_json()
    if not data or 'order_id' not in data:
        return jsonify({"error": "Missing order_id"}), 400
    order_id = data['order_id']
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        # Check order status and if challan already exists
        cursor.execute("SELECT associated_challan_id, client_id, status FROM orders WHERE order_id = %s FOR UPDATE", (order_id,))
        order = cursor.fetchone()
        if not order:
            conn.rollback()
            return jsonify({"error": "Order not found"}), 404
        if order['associated_challan_id']:
            conn.rollback()
            return jsonify({"error": "Challan for this order already exists."}), 409
        if order['status'] != 'Pending':
            conn.rollback()
            return jsonify({"error": f"Order status is '{order['status']}', not 'Pending'. Cannot create challan."}), 409 # Prevent creating challan for non-pending orders

        # Calculate total
        cursor.execute("SELECT SUM(quantity * price_per_unit) as total FROM order_items WHERE order_id = %s", (order_id,))
        order_total_row = cursor.fetchone()
        order_total = order_total_row['total'] if order_total_row and order_total_row['total'] else Decimal('0.00')
        challan_date = datetime.now().date()

        # Insert the new challan
        challan_query = "INSERT INTO challans (client_id, total_amount, challan_date) VALUES (%s, %s, %s)"
        cursor.execute(challan_query, (order['client_id'], order_total, challan_date))
        new_challan_id = cursor.lastrowid

        # ---
        # --- THE FIX IS HERE ---
        # Update the order: set associated_challan_id AND update status to 'Processing'
        # ---
        update_order_query = """
            UPDATE orders
            SET associated_challan_id = %s, status = 'Processing'
            WHERE order_id = %s
        """
        cursor.execute(update_order_query, (new_challan_id, order_id))
        # --- End of Fix ---

        conn.commit()
        return jsonify({"message": "Challan created successfully and order status updated", "challan_id": new_challan_id}), 201
    except mysql.connector.Error as err:
        conn.rollback()
        logging.error(f"Database error creating challan for order {order_id}: {err}", exc_info=True)
        return jsonify({"error": str(err)}), 500
    except Exception as e:
        conn.rollback()
        logging.error(f"Unexpected error creating challan for order {order_id}: {e}", exc_info=True)
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500
    finally:
        # Safely close cursor and connection
        if cursor: cursor.close()
        if conn: conn.close()

@challan_bp.route('/challans', methods=['GET'])
def get_all_challans():
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
            where_clauses.append("DATE(ch.challan_date) >= %s")
            query_params.append(start_date)

        if end_date:
            where_clauses.append("DATE(ch.challan_date) <= %s")
            query_params.append(end_date)

        where_sql = " AND ".join(where_clauses)

        count_query = f"""
            SELECT COUNT(*) as total_count
            FROM challans ch
            WHERE {where_sql}
        """
        cursor.execute(count_query, tuple(query_params))
        total_count = cursor.fetchone()['total_count']
        total_pages = (total_count + per_page - 1) // per_page

        data_query = f"""
            SELECT ch.challan_id, o.order_id, ch.client_id, c.company_name as client_name,
                   ch.total_amount, ch.monthly_bill_id, ch.challan_date,
                   CASE WHEN ch.monthly_bill_id IS NOT NULL THEN 'Billed' ELSE 'Pending' END as status
            FROM challans ch JOIN clients c ON ch.client_id = c.client_id
            LEFT JOIN orders o ON ch.challan_id = o.associated_challan_id
            WHERE {where_sql}
            ORDER BY ch.challan_date DESC, ch.challan_id DESC
            LIMIT %s OFFSET %s
        """

        query_params_paginated = query_params + [per_page, offset]
        cursor.execute(data_query, tuple(query_params_paginated))

        challans = cursor.fetchall()
        for ch in challans:
            ch['challan_date'] = format_datetime(ch['challan_date'])
            ch['total_amount'] = format_datetime(ch['total_amount'])

        return jsonify({
            "data": challans,
            "current_page": page,
            "total_pages": total_pages,
            "total_count": total_count
        })

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@challan_bp.route('/challans/<int:challan_id>', methods=['DELETE'])
def delete_challan(challan_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()

        cursor.execute("SELECT monthly_bill_id FROM challans WHERE challan_id = %s FOR UPDATE", (challan_id,))
        challan = cursor.fetchone()

        if not challan:
            conn.rollback()
            return jsonify({"error": "Challan not found"}), 404

        if challan.get('monthly_bill_id'):
            conn.rollback()
            return jsonify({"error": "Cannot delete challan. It is part of a monthly bill. Please delete the bill first."}), 409

        # Reset the associated order's challan ID and set status back to 'Pending'
        cursor.execute(
            "UPDATE orders SET associated_challan_id = NULL, status = 'Pending' WHERE associated_challan_id = %s",
            (challan_id,)
        )

        cursor.execute("DELETE FROM challans WHERE challan_id = %s", (challan_id,))

        conn.commit()

        return jsonify({"message": "Challan deleted. The original order status is reset to 'Pending'."}), 200

    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@challan_bp.route('/challans/<int:challan_id>/reset-billing', methods=['POST'])
def reset_challan_billing_status(challan_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor()
    try:
        query = "UPDATE challans SET monthly_bill_id = NULL WHERE challan_id = %s"
        cursor.execute(query, (challan_id,))
        if cursor.rowcount == 0:
            return jsonify({"error": "Challan not found"}), 404
        conn.commit()
        return jsonify({"message": f"Billing status for Challan ID {challan_id} has been reset."}), 200
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@challan_bp.route('/challans/<int:challan_id>/pdf', methods=['GET'])
def get_challan_pdf_endpoint(challan_id):
    conn = get_db_connection()
    if not conn:
        logging.error("Database connection failed.")
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT ch.challan_id, ch.challan_date, ch.total_amount, c.company_name, o.order_id
            FROM challans ch
            JOIN clients c ON ch.client_id = c.client_id
            LEFT JOIN orders o ON ch.challan_id = o.associated_challan_id
            WHERE ch.challan_id = %s
        """
        cursor.execute(query, (challan_id,))
        challan_data = cursor.fetchone()
        if not challan_data:
            return jsonify({"error": "Challan not found"}), 404
        if not challan_data.get('order_id'):
             return jsonify({"error": "Challan is not associated with an order."}), 404
        items_query = """
            SELECT p.name, oi.quantity, oi.price_per_unit, (oi.quantity * oi.price_per_unit) as item_total
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            WHERE oi.order_id = %s
            ORDER BY p.name
        """
        cursor.execute(items_query, (challan_data['order_id'],))
        items_data = cursor.fetchall()
        for item in items_data:
            item['price_per_unit'] = float(item['price_per_unit'])
            item['item_total'] = float(item['item_total'])
        challan_data['total_amount'] = float(challan_data['total_amount'])
        pdf_buffer = create_challan_pdf(COMPANY_DETAILS, challan_data, items_data)
        return send_file(pdf_buffer, as_attachment=True, download_name=f'Challan_OC{challan_id:03d}.pdf', mimetype='application/pdf')
    except Exception as e:
        logging.error(f"Error generating PDF for challan {challan_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred while generating the PDF."}), 500
    finally:
        cursor.close()
        conn.close()