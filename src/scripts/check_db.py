#!/usr/bin/env python3
"""Script to check database schema and contents."""
import sqlite3
import os
from pathlib import Path

def check_database_schema(db_path):
    """Check the database schema and print table information."""
    try:
        # Connect to the database
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\nTables in the database:")
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            print("-" * (len(table_name) + 8))
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # Print column information
            print("Columns:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"\n  Rows: {count}")
            
            # Show sample data for small tables
            if count > 0 and count <= 5:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                rows = cursor.fetchall()
                print("\n  Sample data:")
                for row in rows:
                    print(f"  {row}")
        
        # Close the connection
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error accessing database: {e}")
        return False

if __name__ == "__main__":
    db_path = "/home/altay/Masaüstü/mevzuat/C:\\Users\\klc\\Documents\\MevzuatDeposu/db/mevzuat.sqlite"
    print(f"Checking database at: {db_path}")
    
    if not os.path.exists(db_path):
        print("Error: Database file not found!")
    else:
        check_database_schema(db_path)
