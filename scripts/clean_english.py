#!/usr/bin/env python3
"""
Clean English data from database
"""

import sqlite3
from pathlib import Path

db_path = Path('/mnt/c/Users/PC/WikiGraph/databases/wikigraph_multilang.db')

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("Cleaning English data...")
cursor.execute("DELETE FROM articles WHERE language='en'")
cursor.execute("DELETE FROM links WHERE language='en'")
cursor.execute("DELETE FROM metadata WHERE key LIKE 'en_%'")

conn.commit()
conn.close()

print("✅ English data cleaned")
