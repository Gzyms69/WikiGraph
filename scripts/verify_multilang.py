#!/usr/bin/env python3
"""
Verify Multi-Language Database Contents

Checks that both Polish and English data coexist properly.
"""

import sqlite3
import sys
from pathlib import Path

def main():
    db_path = Path('/mnt/c/Users/PC/WikiGraph/databases/wikigraph_multilang.db')

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    print("🔍 MULTI-LANGUAGE DATABASE VERIFICATION")
    print("=" * 50)

    # Check language distribution
    cursor.execute("SELECT language, COUNT(*) FROM articles GROUP BY language ORDER BY language;")
    languages = cursor.fetchall()

    print("📊 Articles by Language:")
    total_articles = 0
    for lang, count in languages:
        print(f"  {lang}: {count:,} articles")
        total_articles += count
    print(f"  Total: {total_articles:,} articles")
    print()

    # Check links by language
    cursor.execute("SELECT language, COUNT(*) FROM links GROUP BY language ORDER BY language;")
    link_langs = cursor.fetchall()

    print("🔗 Links by Language:")
    total_links = 0
    for lang, count in link_langs:
        print(f"  {lang}: {count:,} links")
        total_links += count
    print(f"  Total: {total_links:,} links")
    print()

    # Check for title collisions across languages
    cursor.execute("""
        SELECT title, COUNT(DISTINCT language) as lang_count
        FROM articles
        GROUP BY title
        HAVING lang_count > 1
        ORDER BY title
        LIMIT 10;
    """)
    collisions = cursor.fetchall()

    print("⚠️  Title Collisions Across Languages:")
    if collisions:
        for title, count in collisions:
            print(f"  '{title}' appears in {count} languages")
        print(f"  Total collisions: {len(collisions)}")
    else:
        print("  ✅ No title collisions found")
    print()

    # Sample articles from each language
    for lang in ['pl', 'en']:
        cursor.execute("""
            SELECT title, word_count
            FROM articles
            WHERE language = ?
            ORDER BY word_count DESC
            LIMIT 3;
        """, (lang,))

        articles = cursor.fetchall()
        if articles:
            print(f"📝 Sample {lang.upper()} Articles (by word count):")
            for title, words in articles:
                print(f"  '{title}' ({words} words)")
            print()

    # Check metadata
    cursor.execute("SELECT key, value FROM metadata WHERE key LIKE '%_article_count' OR key LIKE '%_link_count';")
    metadata = cursor.fetchall()

    print("📋 Metadata:")
    for key, value in metadata:
        print(f"  {key}: {value}")
    print()

    print("✅ Verification Complete!")

    conn.close()

if __name__ == "__main__":
    main()
