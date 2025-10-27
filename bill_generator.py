# bill_generator.py
# Contains the business logic for generating monthly bills.

import logging
from datetime import datetime, timedelta
import mysql.connector

logging.basicConfig(level=logging.DEBUG)

def generate_monthly_bill_logic(conn, client_id, billing_period):
    """
    Handles the logic for generating a monthly bill for a given client and period.
    Expects billing_period in 'YYYY-MM' (zero-padded) or 'YYYY-M' — will parse both.
    """
    cursor = conn.cursor(dictionary=True)
    try:
        # Parse billing_period into year and month (robust to single-digit months)
        try:
            year_str, month_str = billing_period.split('-')
            year = int(year_str)
            month = int(month_str)
        except Exception:
            logging.error("Invalid billing_period format: %s", billing_period)
            return {"status": "error", "message": "Invalid billing_period format. Expected 'YYYY-MM'."}

        # 1. Find all unbilled challans for the client in the specified month (use YEAR/MONTH to avoid formatting mismatches)
        query_challans = """
            SELECT challan_id, total_amount
            FROM challans
            WHERE client_id = %s
              AND YEAR(challan_date) = %s
              AND MONTH(challan_date) = %s
              AND monthly_bill_id IS NULL
        """
        logging.debug("Querying challans for client=%s year=%s month=%s", client_id, year, month)
        cursor.execute(query_challans, (client_id, year, month))
        challans_to_bill = cursor.fetchall()

        if not challans_to_bill:
            logging.info("No challans to bill for client %s in %s-%02d", client_id, year, month)
            return {"status": "no_action", "message": "No new challans to bill for this client and month."}

        # 2. Calculate total amount and due date
        total_amount = sum(c['total_amount'] for c in challans_to_bill)
        due_date = (datetime(year, month, 1) + timedelta(days=45)).date()

        # 3. Insert the new monthly bill record
        insert_bill_query = """
            INSERT INTO monthly_bills (client_id, billing_period, total_amount, due_date)
            VALUES (%s, %s, %s, %s)
        """
        billing_period_normalized = f"{year:04d}-{month:02d}"
        cursor.execute(insert_bill_query, (client_id, billing_period_normalized, total_amount, due_date))
        new_bill_id = cursor.lastrowid

        # 4. Update the challans to link them to the new bill
        challan_ids = [c['challan_id'] for c in challans_to_bill]
        placeholders = ', '.join(['%s'] * len(challan_ids))
        update_query = f"UPDATE challans SET monthly_bill_id = %s WHERE challan_id IN ({placeholders})"
        params = [new_bill_id] + challan_ids
        cursor.execute(update_query, params)

        logging.info("Generated monthly bill %s for client %s including %d challans", new_bill_id, client_id, len(challan_ids))
        return {
            "status": "success",
            "message": "Monthly bill generated successfully",
            "monthly_bill_id": new_bill_id,
            "total_amount": float(total_amount),
            "included_challans": len(challan_ids)
        }
    finally:
        cursor.close()