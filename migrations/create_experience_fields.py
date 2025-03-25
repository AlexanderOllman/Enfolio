"""Add additional experience fields to the Content model

This script directly modifies the SQLite database to add new columns 
for the Experience content type.
"""
import sqlite3
import os
import sys

def get_db_path():
    # Assuming the database is in the root directory and named "site.db"
    # Update this path if your database is stored elsewhere
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "site.db")

def run_migration():
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        sys.exit(1)
    
    print(f"Adding new experience fields to database at {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(content)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Define columns to add
        new_columns = [
            ("employment_type", "VARCHAR(50)"),
            ("location", "VARCHAR(200)"),
            ("is_remote", "BOOLEAN DEFAULT 0"),
            ("team_size", "INTEGER"),
            ("key_achievements", "TEXT"),
            ("skills", "VARCHAR(500)"),
            ("responsibilities", "TEXT")
        ]
        
        # Add columns that don't already exist
        for col_name, col_type in new_columns:
            if col_name not in columns:
                sql = f"ALTER TABLE content ADD COLUMN {col_name} {col_type}"
                print(f"Executing: {sql}")
                cursor.execute(sql)
                print(f"✓ Added column {col_name}")
            else:
                print(f"Column {col_name} already exists, skipping")
        
        conn.commit()
        print("Migration completed successfully!")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration() 