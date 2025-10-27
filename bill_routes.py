# bill_routes.py
# Contains all API endpoints related to Monthly Bills.
# This file is compatible with the database_schema.sql provided.
# UPDATED: Marking a bill as paid now updates associated orders to 'Completed'.

from flask import Blueprint, jsonify, request, send_file
from db import get_db_connection
import mysql.connector
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging

# Import helpers from pdf_generator and config
from pdf_generator import create_monthly_bill_pdf
from config import COMPANY_DETAILS

bill_bp = Blueprint('bill_bp', __name__)

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

# --- Monthly Bill Management Endpoints ---

@bill_bp.route('/monthly-bills', methods=['POST'])
def generate_monthly_bill_endpoint():
    data = request.get_json()
    if not data or 'client_id' not in data or 'billing_month' not in data:
        return jsonify({"error": "Missing client_id or billing_month (YYYY-MM)"}), 400

    client_id = data['client_id']
    billing_period = data['billing_month'] # Expecting 'YYYY-MM' format

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()

        try:
            year, month = map(int, billing_period.split('-'))
        except ValueError:
            conn.rollback()
            return jsonify({"error": "Invalid billing_month format. Use YYYY-MM."}), 400

        # Find challans that are not yet billed for the period
        challan_query = """
            SELECT challan_id, total_amount
            FROM challans
            WHERE client_id = %s
              AND monthly_bill_id IS NULL
              AND YEAR(challan_date) = %s
              AND MONTH(challan_date) = %s
            FOR UPDATE
        """
        cursor.execute(challan_query, (client_id, year, month))
        unbilled_challans = cursor.fetchall()

        if not unbilled_challans:
            conn.rollback()
            return jsonify({"message": f"No unbilled challans found for client ID {client_id} in {billing_period}."}), 200 # 200 OK, just no action

        total_amount = sum(Decimal(ch['total_amount']) for ch in unbilled_challans)
        challan_ids = [ch['challan_id'] for ch in unbilled_challans]

        bill_date = datetime.now().date()
        due_date = bill_date + timedelta(days=15)

        # Insert the new monthly bill
        insert_bill_query = """
            INSERT INTO monthly_bills (client_id, billing_period, total_amount, due_date)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_bill_query, (client_id, billing_period, total_amount, due_date))
        new_bill_id = cursor.lastrowid

        # Link the challans to the new bill
        placeholders = ', '.join(['%s'] * len(challan_ids))
        update_challan_query = f"""
            UPDATE challans
            SET monthly_bill_id = %s
            WHERE challan_id IN ({placeholders})
        """
        update_params = [new_bill_id] + challan_ids
        cursor.execute(update_challan_query, tuple(update_params))

        conn.commit()
        return jsonify({"message": f"Monthly bill {new_bill_id} generated successfully for {billing_period}.", "bill_id": new_bill_id}), 201

    except mysql.connector.Error as err:
        conn.rollback()
        logging.error(f"Database error during bill generation: {err}", exc_info=True)
        return jsonify({"error": f"Database error: {err}"}), 500
    except Exception as e:
        conn.rollback()
        logging.error(f"Unexpected error during bill generation: {e}", exc_info=True)
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


@bill_bp.route('/monthly-bills/<int:bill_id>/pdf', methods=['GET'])
def get_monthly_bill_pdf_endpoint(bill_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        # Get bill details
        query = """
            SELECT mb.bill_id, mb.billing_period, mb.total_amount, mb.due_date, mb.status,
                   c.company_name as client_name
            FROM monthly_bills mb
            JOIN clients c ON mb.client_id = c.client_id
            WHERE mb.bill_id = %s
        """
        cursor.execute(query, (bill_id,))
        bill_data = cursor.fetchone()
        if not bill_data:
            return jsonify({"error": "Monthly Bill not found"}), 404
        bill_data['total_amount'] = float(bill_data['total_amount'])

        # Format data for PDF
        current_date = datetime.now().date()
        bill_data['billing_date'] = current_date.strftime('%d-%m-%Y')
        bill_data['due_date_formatted'] = bill_data['due_date'].strftime('%d-%m-%Y') if bill_data['due_date'] else 'N/A'
        bill_data['bill_no_formatted'] = f"AKM-SP{bill_data['billing_period'].replace('-','')}-{bill_id}"

        # Get items associated with the bill's challans
        items_query = """
            SELECT
                p.name,
                oi.quantity,
                oi.price_per_unit,
                (oi.quantity * oi.price_per_unit) as item_total,
                ch.challan_date
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            JOIN orders o ON oi.order_id = o.order_id
            JOIN challans ch ON o.associated_challan_id = ch.challan_id
            WHERE ch.monthly_bill_id = %s
            ORDER BY ch.challan_date, p.name
        """
        cursor.execute(items_query, (bill_id,))
        items_data = cursor.fetchall()
        for item in items_data:
            item['price_per_unit'] = float(item['price_per_unit'])
            item['item_total'] = float(item['item_total'])
            item['challan_date_formatted'] = item['challan_date'].strftime('%d-%m-%Y') if item['challan_date'] else 'N/A' # Add formatted date

        pdf_buffer = create_monthly_bill_pdf(COMPANY_DETAILS, bill_data, items_data)
        return send_file(pdf_buffer, as_attachment=True, download_name=f'Invoice_{bill_data["bill_no_formatted"]}.pdf', mimetype='application/pdf')
    except Exception as e:
        logging.error(f"Error generating PDF for bill {bill_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred while generating the PDF."}), 500
    finally:
        cursor.close()
        conn.close()

@bill_bp.route('/monthly-bills', methods=['GET'])
def get_all_monthly_bills():
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
            # Filter by due_date or maybe creation date? Assuming due_date for now
            where_clauses.append("DATE(mb.due_date) >= %s")
            query_params.append(start_date)

        if end_date:
            where_clauses.append("DATE(mb.due_date) <= %s")
            query_params.append(end_date)

        where_sql = " AND ".join(where_clauses)

        count_query = f"""
            SELECT COUNT(*) as total_count
            FROM monthly_bills mb
            WHERE {where_sql}
        """
        cursor.execute(count_query, tuple(query_params))
        total_count = cursor.fetchone()['total_count']
        total_pages = (total_count + per_page - 1) // per_page

        # Select all necessary columns including billing_period
        data_query = f"""
            SELECT mb.bill_id, mb.client_id, c.company_name as client_name, mb.billing_period,
                   mb.total_amount, mb.status, mb.due_date, mb.payment_date, mb.payment_method
            FROM monthly_bills mb JOIN clients c ON mb.client_id = c.client_id
            WHERE {where_sql}
            ORDER BY mb.billing_period DESC, mb.bill_id DESC
            LIMIT %s OFFSET %s
        """

        query_params_paginated = query_params + [per_page, offset]
        cursor.execute(data_query, tuple(query_params_paginated))

        bills = cursor.fetchall()
        for bill in bills:
            # Rename billing_period to billing_month for frontend consistency
            bill['billing_month'] = bill.pop('billing_period', None)
            bill['due_date'] = format_datetime(bill['due_date'])
            bill['payment_date'] = format_datetime(bill['payment_date'])
            bill['total_amount'] = format_datetime(bill['total_amount'])

        return jsonify({
            "data": bills,
            "current_page": page,
            "total_pages": total_pages,
            "total_count": total_count
        })

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@bill_bp.route('/monthly-bills/<int:bill_id>', methods=['DELETE'])
def delete_monthly_bill(bill_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor()
    try:
        conn.start_transaction()

        # Unlink challans from the bill
        cursor.execute("UPDATE challans SET monthly_bill_id = NULL WHERE monthly_bill_id = %s", (bill_id,))

        # Delete the bill
        cursor.execute("DELETE FROM monthly_bills WHERE bill_id = %s", (bill_id,))
        if cursor.rowcount == 0:
            conn.rollback()
            return jsonify({"error": "Monthly bill not found"}), 404
        conn.commit()
        return jsonify({"message": "Monthly bill deleted and associated challans unlinked."}), 200
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@bill_bp.route('/monthly-bills/<int:bill_id>/payment', methods=['PUT'])
def record_bill_payment(bill_id):
    data = request.get_json()
    if not data or 'payment_date' not in data or 'payment_method' not in data:
        return jsonify({"error": "Missing 'payment_date' or 'payment_method'"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor()
    try:
        conn.start_transaction()

        # Update the bill status, payment date, and method
        update_bill_query = """
            UPDATE monthly_bills
            SET status = 'Paid', payment_date = %s, payment_method = %s
            WHERE bill_id = %s AND status != 'Paid'
        """
        cursor.execute(update_bill_query, (data['payment_date'], data['payment_method'], bill_id))

        if cursor.rowcount == 0:
            # Check if the bill exists but was already paid
            cursor.execute("SELECT bill_id FROM monthly_bills WHERE bill_id = %s", (bill_id,))
            if cursor.fetchone():
                conn.rollback() # No changes needed
                return jsonify({"message": "Bill was already marked as Paid."}), 200
            else:
                conn.rollback()
                return jsonify({"error": "Monthly bill not found or already paid"}), 404

        # ---
        # --- THE FIX IS HERE ---
        # Find associated orders via challans and update their status to 'Completed'
        # ---
        update_orders_query = """
            UPDATE orders o
            JOIN challans ch ON o.associated_challan_id = ch.challan_id
            SET o.status = 'Completed'
            WHERE ch.monthly_bill_id = %s AND o.status = 'Processing'
        """
        cursor.execute(update_orders_query, (bill_id,))
        logging.info(f"Updated {cursor.rowcount} associated orders to 'Completed' for bill {bill_id}.")
        # --- End of Fix ---

        conn.commit()
        return jsonify({"message": "Payment recorded, bill marked as Paid, and associated orders updated."}), 200
    except mysql.connector.Error as err:
        conn.rollback()
        logging.error(f"Database error recording payment for bill {bill_id}: {err}", exc_info=True)
        return jsonify({"error": str(err)}), 500
    except Exception as e:
        conn.rollback()
        logging.error(f"Unexpected error recording payment for bill {bill_id}: {e}", exc_info=True)
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()