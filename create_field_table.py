#!/usr/bin/env python3
"""
Create field_cells table in resonance.sqlite3
"""

import sqlite3
import os

# Path to resonance.sqlite3
DB_PATH = "/data/data/com.termux/files/home/ariannamethod/resonance.sqlite3"

def create_table():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create field_cells table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS field_cells (
                id TEXT PRIMARY KEY,
                age INTEGER DEFAULT 0,
                resonance REAL DEFAULT 0.5,
                fitness REAL DEFAULT 0.5,
                context TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ field_cells table created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating table: {e}")

if __name__ == "__main__":
    create_table()
