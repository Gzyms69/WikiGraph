#!/bin/bash
# ~/WikiGraph/scripts/monitor_progress.sh
# Monitor processing progress in real-time

echo "=== WIKIPEDIA PROCESSING MONITOR ==="
echo "Updated every 10 seconds"
echo ""

while true; do
    clear
    echo "$(date '+%H:%M:%S') - Progress Monitor"
    echo "======================================="

    # Count batches
    BATCHES=$(ls -1 ~/WikiGraph/processed_batches/articles_batch_*.jsonl.gz 2>/dev/null | wc -l)
    ARTICLES=$((BATCHES * 2000))

    # Count links (approximate)
    if [ $BATCHES -gt 0 ]; then
        LINKS=$(zcat ~/WikiGraph/processed_batches/links_batch_*.csv.gz 2>/dev/null | wc -l 2>/dev/null || echo "0")
    else
        LINKS=0
    fi

    # Memory usage
    MEMORY=$(ps aux | grep python | grep phase1_production | grep -v grep | awk '{print $6/1024" MB"}' | head -1)

    # Checkpoint info
    if [ -f ~/WikiGraph/processed_batches/checkpoint.json ]; then
        LAST_ID=$(grep -o '"last_article_id": [0-9]*' ~/WikiGraph/processed_batches/checkpoint.json | cut -d' ' -f2)
        if [ -n "$LAST_ID" ] && [ "$LAST_ID" -gt 0 ]; then
            PERCENTAGE=$(echo "scale=2; $LAST_ID / 2000000 * 100" | bc 2>/dev/null || echo "0")
        else
            PERCENTAGE=0
        fi
    else
        LAST_ID=0
        PERCENTAGE=0
    fi

    echo "Batches completed: $BATCHES"
    echo "Articles processed: $ARTICLES"
    echo "Links extracted: $LINKS"
    echo "Memory usage: ${MEMORY:-N/A}"
    echo "Progress: ${PERCENTAGE}%"
    echo ""
    echo "Latest batch articles:"
    if [ $BATCHES -gt 0 ]; then
        LAST_BATCH=$(printf "%04d" $BATCHES)
        zcat ~/WikiGraph/processed_batches/articles_batch_${LAST_BATCH}.jsonl.gz 2>/dev/null | tail -5 | jq -r '.title' 2>/dev/null || echo "No articles found"
    fi
    echo ""
    echo "Press Ctrl+C to stop monitoring"

    sleep 10
done
