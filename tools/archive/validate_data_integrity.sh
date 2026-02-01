#!/bin/bash
echo "=== 1. POLISH CANONICAL STATS ==="
sqlite3 data/db/pl.db "
  SELECT 
    COUNT(*) as total_canonical_articles,
    SUM(CASE WHEN infobox IS NOT NULL THEN 1 ELSE 0 END) as with_infobox,
    ROUND(SUM(CASE WHEN infobox IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as percentage_with_infobox,
    COUNT(DISTINCT title) as unique_titles
  FROM pages 
  WHERE namespace=0 AND is_redirect=0;
"

echo -e "\n=== 2. POLISH POTENTIAL DUPLICATES ==="
sqlite3 data/db/pl.db "
  SELECT 
    COUNT(*) as total_infobox_rows,
    COUNT(DISTINCT page_id) as unique_page_infoboxes,
    COUNT(*) - COUNT(DISTINCT page_id) as potential_duplicates
  FROM pages 
  WHERE infobox IS NOT NULL;
"

echo -e "\n=== 3. GERMAN INTEGRITY CHECK (BASELINE) ==="
sqlite3 data/db/de.db "
  SELECT 
    COUNT(*) as german_total_canonical,
    COUNT(infobox) as german_with_infobox,
    ROUND(COUNT(infobox)*100.0/COUNT(*), 2) as german_percentage
  FROM pages 
  WHERE namespace=0 AND is_redirect=0;
"

echo -e "\n=== 4. POLISH PATTERN DISTRIBUTION ==="
sqlite3 data/db/pl.db "
  SELECT 
    CASE 
      WHEN json_array_length(infobox) = 0 THEN 'empty_list'
      WHEN json_extract(infobox, '$[0].template') LIKE '%infobox' AND 
           json_extract(infobox, '$[0].template') NOT LIKE 'Infobox%' THEN 'suffix_only'
      WHEN json_extract(infobox, '$[0].template') LIKE 'Infobox%' THEN 'prefix_only'
      WHEN json_extract(infobox, '$[0].template') LIKE '%infobox%' THEN 'mixed_or_other'
      ELSE 'unknown'
    END as pattern_type,
    COUNT(*) as count,
    ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM pages WHERE infobox IS NOT NULL), 2) as percentage
  FROM pages 
  WHERE infobox IS NOT NULL
  GROUP BY pattern_type
  ORDER BY count DESC;
"
