# db.py (UPDATED)
import mysql.connector
import os

def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.environ.get("DB_HOST"),          # <--- READ FROM ENV
            user=os.environ.get("DB_USER"),          # <--- READ FROM ENV
            password=os.environ.get("DB_PASSWORD"),  # <--- READ FROM ENV
            database=os.environ.get("DB_NAME")       # <--- READ FROM ENV
        )
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None