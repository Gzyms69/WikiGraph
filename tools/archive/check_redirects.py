import sqlite3
import sys

db_path = "data/db/pl.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

total = c.execute('SELECT COUNT(*) FROM pages').fetchone()[0]
redirects = c.execute('SELECT COUNT(*) FROM pages WHERE is_redirect=1').fetchone()[0]

print(f"Total Pages: {total}")
print(f"Redirects:   {redirects}")
print(f"Percentage:  {redirects/total*100:.1f}%")
